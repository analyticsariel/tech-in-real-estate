"""Saved questions for signed-in readers (S20.J, decision #157: 12 months, a clear control, carry-over).

Owners are `user#<clerk id>` (kept 12 months) or `device#<id>` for the anonymous free question (kept 24 hours).
When a signed-in request carries the same device token, the device's items move to the user.
Item ids sort by time, so the newest come first without a separate index.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Protocol

USER_DAYS = 365
DEVICE_HOURS = 24
LIST_LIMIT = 100


def new_id(now: datetime) -> str:
    return f"{now:%Y%m%dT%H%M%S%f}-{uuid.uuid4().hex[:8]}"  # URL-safe: a "#" would start a fragment


def summary(item: dict) -> dict:
    return {k: item[k] for k in ("id", "question", "outcome", "created_at")}


class HistoryStore(Protocol):
    def put(self, owner: str, item: dict, expires_at: int) -> None: ...
    def list(self, owner: str) -> list[dict]: ...
    def get(self, owner: str, item_id: str) -> dict | None: ...
    def delete_all(self, owner: str) -> int: ...


class MemoryHistory:
    def __init__(self):
        self.items: dict[str, dict[str, dict]] = {}

    def put(self, owner, item, expires_at):
        self.items.setdefault(owner, {})[item["id"]] = {
            **item,
            "expires_at": expires_at,
        }

    def list(self, owner):
        rows = self.items.get(owner, {})
        return [rows[k] for k in sorted(rows, reverse=True)][:LIST_LIMIT]

    def get(self, owner, item_id):
        return self.items.get(owner, {}).get(item_id)

    def delete_all(self, owner):
        return len(self.items.pop(owner, {}))


class DynamoHistory:
    """Table: pk (owner), sk (item id), plus question, outcome, created_at, payload (JSON), expires_at (TTL)."""

    def __init__(self, table):
        self.table = table

    def put(self, owner, item, expires_at):
        self.table.put_item(
            Item={
                "pk": owner,
                "sk": item["id"],
                "question": item["question"],
                "outcome": item["outcome"],
                "created_at": item["created_at"],
                "payload": json.dumps(item["payload"], default=str),
                "expires_at": expires_at,
            }
        )

    @staticmethod
    def _item(row: dict) -> dict:
        return {
            "id": row["sk"],
            "question": row["question"],
            "outcome": row["outcome"],
            "created_at": row["created_at"],
            "payload": json.loads(row["payload"]),
        }

    def list(self, owner):
        from boto3.dynamodb.conditions import Key

        resp = self.table.query(
            KeyConditionExpression=Key("pk").eq(owner),
            ScanIndexForward=False,
            Limit=LIST_LIMIT,
        )
        return [self._item(r) for r in resp.get("Items", [])]

    def get(self, owner, item_id):
        row = self.table.get_item(Key={"pk": owner, "sk": item_id}).get("Item")
        return self._item(row) if row else None

    def delete_all(self, owner):
        from boto3.dynamodb.conditions import Key

        deleted = 0
        kwargs = {
            "KeyConditionExpression": Key("pk").eq(owner),
            "ProjectionExpression": "pk, sk",
        }
        while True:
            resp = self.table.query(**kwargs)
            with self.table.batch_writer() as batch:
                for row in resp.get("Items", []):
                    batch.delete_item(Key={"pk": row["pk"], "sk": row["sk"]})
                    deleted += 1
            if "LastEvaluatedKey" not in resp:
                return deleted
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


class History:
    def __init__(self, store: HistoryStore, now=lambda: datetime.now(UTC)):
        self.store = store
        self.now = now

    def save(
        self, user_id: str | None, device_id: str, question: str, payload: dict
    ) -> str:
        """Signed in: kept 12 months. Anonymous: kept 24 hours, waiting to be claimed at sign-in."""
        now = self.now()
        owner, keep = (
            (f"user#{user_id}", timedelta(days=USER_DAYS))
            if user_id
            else (f"device#{device_id}", timedelta(hours=DEVICE_HOURS))
        )
        item = {
            "id": new_id(now),
            "question": question,
            "outcome": payload["outcome"],
            "created_at": now.isoformat(timespec="seconds"),
            "payload": payload,
        }
        self.store.put(owner, item, int((now + keep).timestamp()))
        return item["id"]

    def claim(self, user_id: str, device_id: str | None) -> int:
        """Move a device's saved free question to the user who just signed in on it."""
        if not device_id:
            return 0
        items = self.store.list(f"device#{device_id}")
        keep = int((self.now() + timedelta(days=USER_DAYS)).timestamp())
        for item in items:
            self.store.put(f"user#{user_id}", item, keep)
        self.store.delete_all(f"device#{device_id}")
        return len(items)

    def list(self, user_id: str) -> list[dict]:
        return [summary(i) for i in self.store.list(f"user#{user_id}")]

    def get(self, user_id: str, item_id: str) -> dict | None:
        return self.store.get(f"user#{user_id}", item_id)

    def clear(self, user_id: str) -> int:
        return self.store.delete_all(f"user#{user_id}")
