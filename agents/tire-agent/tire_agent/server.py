"""HTTP surface of the deployed agent (S20.G). Runs in Lambda behind the Lambda Web Adapter.

    POST   /ask           {"question", "turnstile_token"?, "device_token"?} + optional Clerk bearer token
                          -> SSE: `progress` events (search, read, check, retry), then one `answer`
    GET    /history       signed in: your saved questions (claims the device's free question, X-Device-Token)
    GET    /history/{id}  signed in: one saved answer
    DELETE /history       signed in: clear your history
    GET    /health        corpus generated_at, git sha, model, stage
    POST   /events        scheduled ping (EventBridge, via the adapter's pass-through path): warms, corpus age

The sign-in gate (S20.J) admits a caller before any model call. With no Clerk issuer configured it is off
on local and dev, and prod refuses to start, so prod can never run ungated.

The stream carries progress steps and then the validated answer, never answer tokens (decision #157), so no
unchecked number ever reaches a reader. Guardrails run before the model is called and fail closed.

Local run:  uvicorn --factory tire_agent.server:create_app --port 8080
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from tire_agent.gate import (
    ClerkVerifier,
    DeviceTokens,
    Gate,
    Refused,
    turnstile_siteverify,
)
from tire_agent.history import DynamoHistory, History, MemoryHistory
from tire_agent.limits import (
    DAILY_SPEND_USD,
    MONTHLY_SPEND_USD,
    DynamoStore,
    Limits,
    MemoryStore,
)

if TYPE_CHECKING:
    from tire_agent.ask import AskResult

MAX_QUESTION_CHARS = 500
# Some proxies hold small chunks back. A 2 KB comment at the start of the stream pushes the first bytes
# through so progress shows immediately (SSE clients ignore comment lines).
STREAM_PADDING = ": " + " " * 2048 + "\n\n"
_KEY_IN_SQL = re.compile(r"key\s*=\s*'([A-Za-z0-9_]+)'")


class AskIn(BaseModel):
    question: str
    turnstile_token: str | None = None
    device_token: str | None = None


_FROM_ENV = (
    object()
)  # create_app default: build the gate and history from the environment


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def emit_metric(name: str, value: float, stage: str) -> None:
    """CloudWatch embedded metric format: one stdout line, no PutMetricData call."""
    print(
        json.dumps(
            {
                "_aws": {
                    "Timestamp": int(time.time() * 1000),
                    "CloudWatchMetrics": [
                        {
                            "Namespace": "TireAgent",
                            "Dimensions": [["Stage"]],
                            "Metrics": [{"Name": name}],
                        }
                    ],
                },
                "Stage": stage,
                name: value,
            }
        ),
        flush=True,
    )


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )


class Corpus:
    """Read-only lookups the response needs: page titles, latest dates, build info."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as db:
            self.build = dict(db.execute("SELECT name, value FROM build_info"))
            self.titles = {}
            for url, title, kind in db.execute(
                "SELECT url, title, kind FROM pages ORDER BY rowid"
            ):
                if (
                    kind != "reading"
                ):  # a metric page and its weekly reading share a URL; keep the page title
                    self.titles.setdefault(url, title)
            self.metric_titles = dict(db.execute("SELECT key, title FROM metrics"))
            self.latest = {
                url: (date, bool(forecast))
                for url, date, forecast in db.execute(
                    "SELECT url, latest_date, is_forecast FROM metric_summary WHERE role = 'primary'"
                )
            }

    def citation(self, url: str) -> dict:
        latest_date, is_forecast = self.latest.get(url, (None, False))
        return {
            "url": url,
            "title": self.titles.get(url, url),
            "latest_date": latest_date,
            "is_forecast": is_forecast,
        }

    def step(self, event: dict) -> dict:
        """Progress event for the browser. A read names the page it reads, never the SQL."""
        if event["type"] == "read":
            m = _KEY_IN_SQL.search(event.get("sql", ""))
            return {
                "type": "read",
                "title": self.metric_titles.get(m.group(1)) if m else None,
            }
        if event["type"] == "search":
            return {"type": "search", "query": event.get("query")}
        return event

    def age_days(self) -> float:
        built = datetime.fromisoformat(self.build["generated_at"])
        return (datetime.now(UTC) - built).total_seconds() / 86400


def answer_payload(r: AskResult, corpus: Corpus, model: str) -> dict:
    return {
        "outcome": r.outcome,
        "answer": r.answer,
        "citations": [corpus.citation(u) for u in r.citations],
        "checked_figures": r.checked_figures,
        "latency_s": r.latency_s,
        "retried": r.retried,
        "model": model,
        "build": corpus.build.get("git_sha", "")[:7],
    }


def _ssm_secret(name: str) -> str:
    """A SecureString from SSM, so secrets never sit in the image or the template."""
    import boto3

    return boto3.client("ssm").get_parameter(Name=name, WithDecryption=True)[
        "Parameter"
    ]["Value"]


def _load_langsmith_key(stage: str) -> None:
    """Tracing is optional: without the key it is switched off, not fatal."""
    name = os.environ.get("TIRE_LANGSMITH_PARAM")
    if not name or os.environ.get("LANGSMITH_API_KEY"):
        return
    try:
        value = _ssm_secret(name)
    except Exception as exc:  # noqa: BLE001
        print(f"tire-agent: tracing off, could not read {name}: {exc}", file=sys.stderr)
        os.environ["LANGSMITH_TRACING"] = "false"
        return
    os.environ["LANGSMITH_API_KEY"] = value
    os.environ.setdefault("LANGSMITH_PROJECT", f"tire-agent-{stage}")


def _default_gate(stage: str, store) -> Gate | None:
    """The sign-in gate from env. Unlike tracing, its secrets are required once it is configured: fail loudly."""
    issuer = os.environ.get("TIRE_CLERK_ISSUER")
    if not issuer:
        if stage == "prod":
            raise RuntimeError(
                "TIRE_CLERK_ISSUER is unset: prod never runs without the sign-in gate"
            )
        print(
            f"tire-agent: sign-in gate OFF ({stage}): no TIRE_CLERK_ISSUER",
            file=sys.stderr,
        )
        return None
    origins = [
        o.strip()
        for o in os.environ.get("TIRE_AUTH_ORIGINS", "").split(",")
        if o.strip()
    ]
    public_key = (os.environ.get("TIRE_CLERK_PUBLIC_KEY") or "").replace(
        "\\n", "\n"
    ) or None
    turnstile_secret = _ssm_secret(os.environ["TIRE_TURNSTILE_PARAM"])
    device_secret = _ssm_secret(os.environ["TIRE_DEVICE_PARAM"])

    async def turnstile(token: str, ip: str) -> bool:
        return await turnstile_siteverify(turnstile_secret, token, ip)

    return Gate(
        store,
        ClerkVerifier(issuer, origins, public_key),
        turnstile,
        DeviceTokens(device_secret),
    )


def _default_history() -> History:
    table = os.environ.get("TIRE_HISTORY_TABLE")
    if not table:
        return History(MemoryHistory())
    import boto3

    return History(DynamoHistory(boto3.resource("dynamodb").Table(table)))


def _default_limits() -> Limits:
    """Caps come from the environment so dev can run lower than prod (TIRE_DAILY_SPEND_USD, TIRE_MONTHLY_SPEND_USD)."""
    caps = {
        "daily_usd": float(os.environ.get("TIRE_DAILY_SPEND_USD", DAILY_SPEND_USD)),
        "monthly_usd": float(
            os.environ.get("TIRE_MONTHLY_SPEND_USD", MONTHLY_SPEND_USD)
        ),
    }
    table = os.environ.get("TIRE_LIMITS_TABLE")
    if not table:
        return Limits(MemoryStore(), **caps)
    import boto3

    return Limits(DynamoStore(boto3.resource("dynamodb").Table(table)), **caps)


def _build_dir() -> Path:
    """Same rule as agent.build_agent (TIRE_BUILD_DIR, else the package's build/), without importing LangChain."""
    return Path(
        os.environ.get("TIRE_BUILD_DIR") or Path(__file__).resolve().parent / "build"
    )


def _load_agent(stage: str):
    from tire_agent.agent import build_agent
    from tire_agent.ask import aask

    _load_langsmith_key(stage)
    return build_agent(), aask


def create_app(
    agent=None,
    limits: Limits | None = None,
    ask_fn=None,
    gate: Gate | None = _FROM_ENV,
    history: History | None = _FROM_ENV,
) -> FastAPI:
    """The agent loads on a background thread so /health answers at once.

    On a 1 GB Lambda, importing LangChain and building the agent took ~10 s, Lambda's whole init window.
    Waiting for it before reporting ready timed init out and re-ran it inside the first request.
    """
    stage = os.environ.get("TIRE_STAGE", "local")
    if agent is None:
        ready: Future = ThreadPoolExecutor(max_workers=1).submit(_load_agent, stage)
        db_path = _build_dir() / "tire.db"
    else:
        if ask_fn is None:
            from tire_agent.ask import aask as ask_fn
        ready = Future()
        ready.set_result((agent, ask_fn))
        db_path = agent.db_path
    limits = limits or _default_limits()
    if gate is _FROM_ENV:
        gate = _default_gate(stage, limits.store)
    if history is _FROM_ENV:
        history = _default_history()
    corpus = Corpus(db_path)
    app = FastAPI(title="tire-agent", docs_url=None, redoc_url=None, openapi_url=None)
    if stage == "local":
        # In AWS the function URL owns CORS. Locally, let the Next dev server call this one.
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["content-type", "authorization", "x-device-token"],
        )

    @app.get("/health")
    def health():
        loaded = ready.done() and ready.exception() is None
        return {
            "generated_at": corpus.build.get("generated_at"),
            "git_sha": corpus.build.get("git_sha"),
            "model": ready.result()[0].model if loaded else None,
            "stage": stage,
            "agent_ready": loaded,
        }

    @app.post("/events")
    async def scheduled():
        """Every 5 minutes: finish loading the agent while nobody is waiting, then report corpus age.

        Lambda freezes the environment between requests, so the background load only advances during one.
        """
        try:
            await asyncio.wait_for(asyncio.wrap_future(ready), timeout=45)
        except Exception as exc:  # noqa: BLE001
            print(f"tire-agent: agent not ready after ping: {exc!r}", file=sys.stderr)
        emit_metric("CorpusAgeDays", round(corpus.age_days(), 2), stage)
        return {"ok": True}

    @app.post("/ask")
    async def ask(body: AskIn, request: Request):
        question = body.question.strip()
        if not question:
            return JSONResponse({"code": "empty"}, status_code=400)
        if len(question) > MAX_QUESTION_CHARS:
            return JSONResponse(
                {"code": "too_long", "max": MAX_QUESTION_CHARS}, status_code=400
            )
        denied = limits.spend_open()
        if denied:
            print(
                json.dumps({"event": "spend_cap_hit", "code": denied.code}), flush=True
            )
            emit_metric("SpendCapHit", 1, stage)
            return JSONResponse(denied.body(), status_code=denied.status)
        ip = client_ip(request)
        denied = limits.count_ip(ip)
        if denied:
            return JSONResponse(denied.body(), status_code=denied.status)
        caller = None
        if gate:
            try:
                caller = await gate.admit(
                    request.headers.get("authorization"),
                    body.turnstile_token,
                    body.device_token,
                    ip,
                )
            except Refused as refused:
                return JSONResponse(
                    refused.denied.body(), status_code=refused.denied.status
                )
        agent, ask_fn = await asyncio.wrap_future(
            ready
        )  # usually done; on a cold start, waits for the load

        queue: asyncio.Queue = asyncio.Queue()

        async def on_event(event: dict) -> None:
            await queue.put(corpus.step(event))

        async def run() -> AskResult:
            try:
                result = await ask_fn(agent, question, on_event=on_event)
                limits.record_spend(result.cost_usd)
                return result
            finally:
                await queue.put(None)

        async def stream():
            yield STREAM_PADDING
            task = asyncio.create_task(run())
            while (event := await queue.get()) is not None:
                yield sse("progress", event)
            result = await task
            print(
                json.dumps(
                    {
                        "event": "answer",
                        "outcome": result.outcome,
                        "cost_usd": result.cost_usd,
                        "latency_s": result.latency_s,
                        "model_calls": result.model_calls,
                        "fallback_reason": result.fallback_reason,
                        "run_ids": result.run_ids,
                    }
                ),
                flush=True,
            )
            payload = answer_payload(result, corpus, agent.model)
            if result.outcome in ("error", "timeout"):
                emit_metric("AgentErrors", 1, stage)
            elif caller:
                # Only a real answer uses up the free question or one of the 10, and only it is saved.
                gate.record_success(caller)
                payload["history_id"] = history.save(
                    caller.user_id, caller.device_id, question, payload
                )
            if caller:
                payload["device_token"] = gate.devices.issue(caller.device_id)
                payload["signed_in"] = not caller.anonymous
            yield sse("answer", payload)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    def signed_in_user(request: Request) -> str | None:
        auth = request.headers.get("authorization") or ""
        if not gate or not auth.startswith("Bearer "):
            return None
        try:
            return gate.verifier.user_id(auth[7:])
        except Exception:  # noqa: BLE001
            return None

    def sign_in_required() -> JSONResponse:
        return JSONResponse(
            {"code": "sign_in_required", "reset_at": None}, status_code=401
        )

    @app.get("/history")
    def list_history(request: Request):
        user_id = signed_in_user(request)
        if not user_id:
            return sign_in_required()
        history.claim(user_id, gate.devices.read(request.headers.get("x-device-token")))
        return {"items": history.list(user_id), "retention_days": 365}

    @app.get("/history/{item_id}")
    def get_history(item_id: str, request: Request):
        user_id = signed_in_user(request)
        if not user_id:
            return sign_in_required()
        item = history.get(user_id, item_id)
        if not item:
            return JSONResponse({"code": "not_found"}, status_code=404)
        return {
            k: item[k] for k in ("id", "question", "outcome", "created_at", "payload")
        }

    @app.delete("/history")
    def clear_history(request: Request):
        user_id = signed_in_user(request)
        if not user_id:
            return sign_in_required()
        return {"deleted": history.clear(user_id)}

    return app
