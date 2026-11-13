"""tire-agent assembly: deep agent + search/query tools + read-only corpus (S20.D)."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import boto3
from botocore.config import Config
from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
)
from langchain.agents.structured_output import ProviderStrategy
from langchain_aws import ChatBedrockConverse
from pydantic import BaseModel, Field

from tire_agent.prompts import SYSTEM_PROMPT
from tire_agent.tools import make_tools

DEFAULT_BUILD = Path(__file__).resolve().parent / "build"
DEFAULT_MODEL = "claude-haiku-5-5"  # chosen by the S20.E baseline (decision #152)
MODEL_TIMEOUT_S = 30
# Claude runs on Amazon Bedrock, billed to the TiRE AWS account (decision #156).
EXPECTED_AWS_ACCOUNT = ""  # set TIRE_AWS_ACCOUNT_ID
DEFAULT_REGION = "us-east-1"
MAX_TOOL_CALLS = 6
MAX_MODEL_CALLS = 8


class Answer(BaseModel):
    status: Literal["answered", "cannot_answer"] = Field(
        description="answered, or cannot_answer when the site has no data, the page is coming soon, "
        "or the question asks for a prediction or advice."
    )
    answer: str = Field(
        description="Two to five direct sentences. Numbers exactly as tools returned them."
    )
    citations: list[str] = Field(
        description="Site URLs from tool results that support the answer."
    )


@dataclass
class TireAgent:
    graph: object
    model: str
    routes: set[str]
    db_path: Path


class WrongAWSAccount(RuntimeError):
    """Refuse to call Bedrock from any account but TiRE's (the shell default profile is a different account)."""


def bedrock_model_id(model: str) -> str:
    """Short name (claude-haiku-5-5) -> Bedrock US inference profile (us.anthropic.claude-haiku-5-5).

    US over global: same median latency, but the global profile's tail hit 23 s where US stayed under
    11 s (2026-11-06 benchmark), for 10% more per token (decision #156).
    """
    if model.startswith(("global.", "us.", "anthropic.")):
        return model
    return f"us.anthropic.{model}"


def aws_session() -> boto3.Session:
    """Bedrock credentials: TIRE_AWS_PROFILE locally, the Lambda execution role in AWS, the OIDC deploy role in
    GitHub Actions. Never the default profile.

    Verifies the account before anything is billed, because the developer machine's default AWS_PROFILE
    belongs to another account.
    """
    profile = os.environ.get("TIRE_AWS_PROFILE")
    in_aws = (
        os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("GITHUB_ACTIONS") == "true"
    )
    if not profile and not in_aws:
        raise WrongAWSAccount(
            "set TIRE_AWS_PROFILE (e.g. my-aws-profile); the default AWS profile is not allowed"
        )
    session = boto3.Session(
        profile_name=profile,
        region_name=os.environ.get("TIRE_AWS_REGION", DEFAULT_REGION),
    )
    expected = os.environ.get("TIRE_AWS_ACCOUNT_ID", EXPECTED_AWS_ACCOUNT)
    account = session.client("sts").get_caller_identity()["Account"]
    if account != expected:
        raise WrongAWSAccount(
            f"AWS account {account} is not the TiRE account {expected}; refusing to call Bedrock"
        )
    return session


def chat_model(model: str, session: boto3.Session) -> ChatBedrockConverse:
    client = session.client(
        "bedrock-runtime",
        config=Config(
            connect_timeout=5,
            read_timeout=MODEL_TIMEOUT_S,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )
    return ChatBedrockConverse(
        model=bedrock_model_id(model),
        region_name=session.region_name,
        client=client,
        max_tokens=2048,
    )


def build_agent(
    model: str | None = None,
    build_dir: Path | None = None,
    session: boto3.Session | None = None,
) -> TireAgent:
    model = model or os.environ.get("TIRE_AGENT_MODEL") or DEFAULT_MODEL
    build_dir = Path(build_dir or os.environ.get("TIRE_BUILD_DIR", DEFAULT_BUILD))
    db_path = build_dir / "tire.db"
    search, query = make_tools(db_path)
    with closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as db:
        routes = {r[0] for r in db.execute("SELECT url FROM routes")}
    graph = create_deep_agent(
        model=chat_model(model, session or aws_session()),
        tools=[search, query],
        system_prompt=SYSTEM_PROMPT,
        backend=CompositeBackend(
            default=StateBackend(),
            routes={
                "/corpus/": FilesystemBackend(
                    root_dir=str(build_dir / "corpus"), virtual_mode=True
                )
            },
        ),
        permissions=[
            FilesystemPermission(
                operations=["write"], paths=["/corpus/**"], mode="deny"
            )
        ],
        # Native structured output: the API enforces the schema. Profile auto-detection picked the
        # tool strategy for Haiku 5.5, which retried an invalid answer six times on one question.
        response_format=ProviderStrategy(Answer),
        middleware=[
            ToolCallLimitMiddleware(run_limit=MAX_TOOL_CALLS, exit_behavior="continue"),
            ModelCallLimitMiddleware(run_limit=MAX_MODEL_CALLS, exit_behavior="end"),
        ],
    )
    return TireAgent(graph=graph, model=model, routes=routes, db_path=db_path)
