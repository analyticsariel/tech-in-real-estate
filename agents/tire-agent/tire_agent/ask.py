"""Answer one question end to end: deadline, guard, grounding check, one retry, honest fallback (S20.D)."""

from __future__ import annotations

import asyncio
import os
import re
import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import HumanMessage

from tire_agent.agent import TireAgent
from tire_agent.grounding import checkable_numbers, checked_figures, validate
from tire_agent.guard import CallGuard, GuardError

DEADLINE_S = 45.0
FALLBACK_TEXT = "We couldn't answer that reliably from the site's data. These pages are the closest match."


@dataclass
class AskResult:
    status: str
    answer: str
    citations: list[str]
    cost_usd: float = 0.0
    model_calls: int = 0
    tool_calls: int = 0
    latency_s: float = 0.0
    retried: bool = False
    violations: list[str] = field(default_factory=list)
    fallback_reason: str | None = None
    error: str | None = None
    run_ids: list[str] = field(default_factory=list)
    checked_figures: list[dict] = field(
        default_factory=list
    )  # provenance per number (answered only)
    messages: list = field(
        default_factory=list, repr=False
    )  # full run, for traces and debugging

    @property
    def outcome(self) -> str:
        """answered | declined | unverified | timeout | error: what the site renders."""
        if self.fallback_reason is None:
            return "answered" if self.status == "answered" else "declined"
        if self.fallback_reason in ("deadline", "error"):
            return {"deadline": "timeout", "error": "error"}[self.fallback_reason]
        return "unverified"


EventSink = Callable[[dict], Awaitable[None]]


async def _emit(sink: EventSink | None, event: dict) -> None:
    """Progress is best effort: a client that went away must never break the answer."""
    if sink is None:
        return
    try:
        await sink(event)
    except Exception as exc:  # noqa: BLE001
        print(f"tire-agent: progress event dropped: {exc}", file=sys.stderr)


class Progress(AsyncCallbackHandler):
    """Turns tool callbacks into the site's progress steps: search and read.

    There is no "writing" step: the model is also called between tools to pick the next one, so no callback
    marks the start of the final answer. The site shows the latest real step until "check" arrives.
    """

    def __init__(self, sink: EventSink | None):
        self.sink = sink

    async def on_tool_start(self, serialized, input_str, *, inputs=None, **kwargs):
        name = (serialized or {}).get("name") or kwargs.get("name")
        args = inputs or {}
        if name == "search":
            await _emit(
                self.sink, {"type": "search", "query": args.get("query", input_str)}
            )
        elif name == "query":
            await _emit(self.sink, {"type": "read", "sql": args.get("sql", input_str)})


def _tool_texts(messages) -> list[str]:
    return [m.text for m in messages if m.type == "tool"]


def _tool_calls(messages) -> int:
    return sum(
        len(getattr(m, "tool_calls", []) or []) for m in messages if m.type == "ai"
    )


def _fallback_links(tool_texts: list[str], routes: set[str]) -> list[str]:
    seen = []
    for text in tool_texts:
        for url in re.findall(r"(/(?:metric|skills)/[A-Za-z0-9_./-]+)", text):
            if url in routes and url not in seen:
                seen.append(url)
    return seen[:3] or (["/data"] if "/data" in routes else [])


async def aask(
    agent: TireAgent,
    question: str,
    deadline_s: float = DEADLINE_S,
    on_event: EventSink | None = None,
) -> AskResult:
    """Answer one question. `on_event` receives progress steps (search, read, check, retry)."""
    start = time.monotonic()
    guard = CallGuard(agent.model)
    messages: list = [{"role": "user", "content": question}]
    state_messages: list = []
    result = AskResult(status="cannot_answer", answer=FALLBACK_TEXT, citations=[])

    def finish(**kw) -> AskResult:
        for k, v in kw.items():
            setattr(result, k, v)
        result.cost_usd, result.model_calls = guard.cost, guard.model_calls
        result.tool_calls = _tool_calls(state_messages)
        result.latency_s = round(time.monotonic() - start, 2)
        result.messages = state_messages
        if result.fallback_reason:
            result.citations = _fallback_links(
                _tool_texts(state_messages), agent.routes
            )
        elif result.status == "answered":
            result.checked_figures = checked_figures(
                result.answer, _tool_texts(state_messages), result.citations
            )
        return result

    for attempt in range(2):
        remaining = deadline_s - (time.monotonic() - start)
        if remaining <= 0:
            return finish(fallback_reason="deadline")
        run_id = uuid.uuid4()
        result.run_ids.append(str(run_id))
        config = {
            "callbacks": [guard, Progress(on_event)],
            "recursion_limit": 60,
            "run_id": run_id,
            "run_name": "tire-agent",
        }
        try:
            state = await asyncio.wait_for(
                agent.graph.ainvoke({"messages": messages}, config=config), remaining
            )
        except TimeoutError:
            return finish(fallback_reason="deadline")
        except GuardError as exc:
            return finish(fallback_reason=f"guard: {exc}")
        # Any API/network error becomes the honest fallback, logged to stderr for the alarm metric.
        except Exception as exc:  # noqa: BLE001
            print(f"tire-agent error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return finish(fallback_reason="error", error=f"{type(exc).__name__}: {exc}")
        state_messages = state["messages"]
        answer = state.get("structured_response")
        if answer is None:
            return finish(fallback_reason="no structured answer (call budget reached)")
        await _emit(
            on_event,
            {"type": "check", "numbers": len(checkable_numbers(answer.answer))},
        )
        violations = validate(answer, _tool_texts(state_messages), agent.routes)
        if not violations:
            return finish(
                status=answer.status,
                answer=answer.answer,
                citations=answer.citations,
                violations=result.violations,
            )
        result.violations = violations
        if attempt == 0:
            result.retried = True
            await _emit(on_event, {"type": "retry"})
            messages = [
                *state_messages,
                HumanMessage(
                    "Your answer failed these checks: "
                    + "; ".join(violations)
                    + ". Answer again using only numbers and URLs that appear in tool results, or decline."
                ),
            ]
    return finish(fallback_reason="grounding")


def ask(agent: TireAgent, question: str, deadline_s: float = DEADLINE_S) -> AskResult:
    return asyncio.run(aask(agent, question, deadline_s))


_PROJECT_IDS: dict[str, str] = {}


def _project_id(client, name: str) -> str:
    if (
        name not in _PROJECT_IDS
    ):  # one lookup per process (Lambda container), not per question
        _PROJECT_IDS[name] = str(client.read_project(project_name=name).id)
    return _PROJECT_IDS[name]


def record_feedback(result: AskResult) -> None:
    """Attach the grounding outcome to the trace in LangSmith (best effort; never fails the answer).

    grounding_pass = 1 when the final answer passed the checks (possibly after the retry), 0 when it fell back.
    """
    if (
        os.environ.get(
            "LANGSMITH_TRACING", os.environ.get("LANGCHAIN_TRACING_V2", "")
        ).lower()
        != "true"
    ):
        return
    try:
        from langsmith import Client

        client = Client()
        project = (
            os.environ.get("LANGSMITH_PROJECT")
            or os.environ.get("LANGCHAIN_PROJECT")
            or "default"
        )
        client.create_feedback(
            run_id=result.run_ids[-1],
            session_id=_project_id(client, project),
            key="grounding_pass",
            score=int(result.fallback_reason is None),
            comment="; ".join(result.violations) or result.fallback_reason,
        )
    except Exception as exc:  # noqa: BLE001 - feedback is best effort; never fail the answer
        print(
            f"tire-agent: feedback not recorded ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
