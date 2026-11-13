"""Server-side guardrails for the deployed agent (S20.G, decision #140): per-IP backstop and spend caps.

The browser only shows the right prompt. This module decides. Every cap fails closed. Days and months
roll over at midnight ET (decision #157). Sign-in and the free anonymous question are S20.J.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

IP_PER_HOUR = 10
IP_PER_DAY = 30
DAILY_SPEND_USD = 0.80
MONTHLY_SPEND_USD = 25.00


@dataclass(frozen=True)
class Denied:
    """Why a request was refused, in the shape the site renders: a code, an HTTP status, and when it resets."""

    code: str  # rate_limited | daily_cap | monthly_cap | sign_in_required | daily_limit
    status: int
    reset_at: (
        str | None
    )  # ISO 8601 with offset; None when waiting won't help (sign in instead)
    reason: str | None = (
        None  # sign_in_required only: free_used | pool_exhausted | turnstile_failed | invalid_token
    )

    def body(self) -> dict:
        body = {"code": self.code, "reset_at": self.reset_at}
        return {**body, "reason": self.reason} if self.reason else body


class Store(Protocol):
    def incr(self, key: str, limit: int, expires_at: int) -> bool:
        """Add 1 if the count is below `limit`. False (and no change) if it isn't."""

    def total(self, key: str) -> float: ...

    def add(self, key: str, amount: float, expires_at: int) -> None: ...


class MemoryStore:
    """In-process store for tests and local runs."""

    def __init__(self):
        self.counts: dict[str, float] = {}

    def incr(self, key, limit, expires_at):
        if self.counts.get(key, 0) >= limit:
            return False
        self.counts[key] = self.counts.get(key, 0) + 1
        return True

    def total(self, key):
        return float(self.counts.get(key, 0))

    def add(self, key, amount, expires_at):
        self.counts[key] = self.counts.get(key, 0) + amount


class DynamoStore:
    """One DynamoDB table: pk (string), n (number), expires_at (TTL attribute)."""

    def __init__(self, table):
        self.table = table

    def incr(self, key, limit, expires_at):
        try:
            self.table.update_item(
                Key={"pk": key},
                UpdateExpression="ADD n :one SET expires_at = if_not_exists(expires_at, :ttl)",
                ConditionExpression="attribute_not_exists(n) OR n < :limit",
                ExpressionAttributeValues={
                    ":one": 1,
                    ":limit": limit,
                    ":ttl": expires_at,
                },
            )
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        return True

    def total(self, key):
        item = self.table.get_item(Key={"pk": key}, ConsistentRead=True).get("Item")
        return float(item["n"]) if item else 0.0

    def add(self, key, amount, expires_at):
        self.table.update_item(
            Key={"pk": key},
            UpdateExpression="ADD n :amount SET expires_at = if_not_exists(expires_at, :ttl)",
            ExpressionAttributeValues={
                ":amount": Decimal(str(round(amount, 6))),
                ":ttl": expires_at,
            },
        )


def _next_hour(now: datetime) -> datetime:
    return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def next_midnight(now: datetime) -> datetime:
    return datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), ET)


def _next_month(now: datetime) -> datetime:
    first = now.date().replace(day=1)
    return datetime.combine(
        (first + timedelta(days=32)).replace(day=1), datetime.min.time(), ET
    )


def expires_after(reset: datetime) -> int:
    """Keep a counter a day past its window, then let DynamoDB drop it."""
    return int((reset + timedelta(days=1)).timestamp())


class Limits:
    def __init__(
        self,
        store: Store,
        now=lambda: datetime.now(ET),
        daily_usd: float = DAILY_SPEND_USD,
        monthly_usd: float = MONTHLY_SPEND_USD,
    ):
        self.store = store
        self.now = now
        self.daily_usd = daily_usd
        self.monthly_usd = monthly_usd

    def spend_open(self) -> Denied | None:
        """Refuse before any model call if today's or this month's spend has hit its cap."""
        now = self.now()
        if self.store.total(f"spend#d#{now:%Y%m%d}") >= self.daily_usd:
            return Denied("daily_cap", 503, next_midnight(now).isoformat())
        if self.store.total(f"spend#m#{now:%Y%m}") >= self.monthly_usd:
            return Denied("monthly_cap", 503, _next_month(now).isoformat())
        return None

    def count_ip(self, ip: str) -> Denied | None:
        """Per-IP backstop: counts every attempt, so retries can't be used to hammer the endpoint."""
        now = self.now()
        hour, day = _next_hour(now), next_midnight(now)
        if not self.store.incr(
            f"ip#{ip}#h#{now:%Y%m%d%H}", IP_PER_HOUR, expires_after(hour)
        ):
            return Denied("rate_limited", 429, hour.isoformat())
        if not self.store.incr(
            f"ip#{ip}#d#{now:%Y%m%d}", IP_PER_DAY, expires_after(day)
        ):
            return Denied("rate_limited", 429, day.isoformat())
        return None

    def record_spend(self, usd: float) -> None:
        """Every answer's real cost counts, including fallbacks: the model was still called."""
        if usd <= 0:
            return
        now = self.now()
        self.store.add(f"spend#d#{now:%Y%m%d}", usd, expires_after(next_midnight(now)))
        self.store.add(f"spend#m#{now:%Y%m}", usd, expires_after(_next_month(now)))
