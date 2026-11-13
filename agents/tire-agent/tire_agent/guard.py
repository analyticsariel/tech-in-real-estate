"""Per-call guard: stop_reason check and per-answer cost cap (S20.D, decision #140).

Runs as a LangChain callback on every model call. A truncated or refused call, or one
that pushes the answer past its cost cap, raises immediately. A partial answer is never
returned (the 2026-11-05 readings saved truncated output for months).
"""

from __future__ import annotations

from langchain_core.callbacks import BaseCallbackHandler

from tire_agent.pricing import cost_usd

PER_ANSWER_CAP_USD = 0.03
REFUSAL_STOPS = {"refusal", "content_filtered", "guardrail_intervened"}


class GuardError(Exception):
    """Base for guard stops; ask() turns these into the honest fallback."""


class Truncated(GuardError):
    pass


class Refused(GuardError):
    pass


class BudgetExceeded(GuardError):
    pass


class CallGuard(BaseCallbackHandler):
    raise_error = (
        True  # propagate out of the agent run instead of being logged and ignored
    )

    def __init__(self, model: str, cap_usd: float = PER_ANSWER_CAP_USD):
        self.model = model
        self.cap_usd = cap_usd
        self.cost = 0.0
        self.model_calls = 0

    def on_llm_end(self, response, **kwargs) -> None:
        for gens in response.generations:
            for gen in gens:
                msg = getattr(gen, "message", None)
                if msg is None:
                    continue
                self.model_calls += 1
                meta = msg.response_metadata or {}
                # Anthropic's API says stop_reason; Bedrock Converse says stopReason. Missing either would
                # silently disable the truncation check.
                stop = meta.get("stop_reason") or meta.get("stopReason")
                if stop == "max_tokens":
                    raise Truncated("model output hit max_tokens")
                if stop in REFUSAL_STOPS:
                    raise Refused(f"model stopped: {stop}")
                self.cost += cost_usd(self.model, msg.usage_metadata or {})
                if self.cost > self.cap_usd:
                    raise BudgetExceeded(
                        f"answer cost ${self.cost:.4f} > cap ${self.cap_usd:.2f}"
                    )
