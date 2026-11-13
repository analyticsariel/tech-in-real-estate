"""Sign-in gate for the deployed agent (S20.J, decisions #145 and #163). The Lambda is the only enforcer.

Signed in (Clerk session token): 10 questions a day per user.
Anonymous: one free question, after a Cloudflare Turnstile check. The question is tracked by IP plus a signed
device token, and every anonymous question shares a pool of 15 a day.
Anything else gets 401 `sign_in_required`, with a `reason` the page uses to pick what to show.

Questions are counted only after a successful answer: a timeout or error never uses up the free question
or one of the 10 (decision #157).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt

from tire_agent.limits import ET, Denied, Store, expires_after, next_midnight

USER_PER_DAY = 10
ANON_POOL_PER_DAY = 15
FREE_MARK_DAYS = 30  # long enough to mean "one per visitor", short enough not to lock out a shared IP forever

TurnstileCheck = Callable[[str, str], Awaitable[bool]]


@dataclass(frozen=True)
class Caller:
    user_id: str | None
    device_id: str
    ip: str

    @property
    def anonymous(self) -> bool:
        return self.user_id is None


class Refused(Exception):
    def __init__(self, denied: Denied):
        super().__init__(denied.code)
        self.denied = denied


def _sign_in(reason: str) -> Refused:
    return Refused(Denied("sign_in_required", 401, None, reason))


class DeviceTokens:
    """`<id>.<hmac>`: an id the Lambda issued and can recognise, kept by the page (not a cookie; see #163)."""

    def __init__(self, secret: str):
        self.key = secret.encode()

    def _mac(self, device_id: str) -> str:
        digest = hmac.new(self.key, device_id.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest[:18]).decode()

    def issue(self, device_id: str | None = None) -> str:
        device_id = device_id or uuid.uuid4().hex
        return f"{device_id}.{self._mac(device_id)}"

    def read(self, token: str | None) -> str | None:
        """The device id if the token is one we signed, else None (a forged token is treated as no token)."""
        if not token or "." not in token:
            return None
        device_id, mac = token.split(".", 1)
        return device_id if hmac.compare_digest(mac, self._mac(device_id)) else None


class ClerkVerifier:
    """Verifies Clerk session tokens the way Clerk's manual-verification guide describes: RS256 signature,
    exp/nbf, issuer, and azp against our own origins. Uses the instance's public key when given (no network
    call), else the instance JWKS."""

    def __init__(
        self, issuer: str, origins: list[str], public_key: str | None = None, jwks=None
    ):
        self.issuer = issuer.rstrip("/")
        self.origins = origins
        self.public_key = public_key
        self.jwks = jwks or (
            None
            if public_key
            else jwt.PyJWKClient(f"{self.issuer}/.well-known/jwks.json")
        )

    def user_id(self, token: str) -> str:
        key = self.public_key or self.jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=self.issuer,
            leeway=5,
            options={"require": ["exp", "iat", "sub"], "verify_aud": False},
        )
        azp = claims.get("azp")
        if "*" not in self.origins and azp not in self.origins:
            raise jwt.InvalidTokenError(f"azp {azp!r} is not a site origin")
        return claims["sub"]


class Gate:
    def __init__(
        self,
        store: Store,
        verifier: ClerkVerifier,
        turnstile: TurnstileCheck,
        devices: DeviceTokens,
        now=lambda: datetime.now(ET),
    ):
        self.store = store
        self.verifier = verifier
        self.turnstile = turnstile
        self.devices = devices
        self.now = now

    def _today(self) -> str:
        return f"{self.now():%Y%m%d}"

    async def admit(
        self,
        authorization: str | None,
        turnstile_token: str | None,
        device_token: str | None,
        ip: str,
    ) -> Caller:
        """Who is asking, or Refused. Cheap checks run before the Turnstile network call."""
        device_id = self.devices.read(device_token)
        if authorization and authorization.startswith("Bearer "):
            try:
                user_id = self.verifier.user_id(authorization[7:])
            except jwt.PyJWTError:
                raise _sign_in("invalid_token") from None
            if self.store.total(f"user#{user_id}#d#{self._today()}") >= USER_PER_DAY:
                raise Refused(
                    Denied("daily_limit", 429, next_midnight(self.now()).isoformat())
                )
            return Caller(user_id, device_id or uuid.uuid4().hex, ip)

        if self.store.total(f"free#ip#{ip}") or (
            device_id and self.store.total(f"free#dev#{device_id}")
        ):
            raise _sign_in("free_used")
        if self.store.total(f"anon#d#{self._today()}") >= ANON_POOL_PER_DAY:
            raise _sign_in("pool_exhausted")
        if not turnstile_token or not await self.turnstile(turnstile_token, ip):
            raise _sign_in("turnstile_failed")
        return Caller(None, device_id or uuid.uuid4().hex, ip)

    def record_success(self, caller: Caller) -> None:
        now = self.now()
        day_end = expires_after(next_midnight(now))
        if caller.user_id:
            self.store.add(f"user#{caller.user_id}#d#{self._today()}", 1, day_end)
            return
        free_end = int((now + timedelta(days=FREE_MARK_DAYS)).timestamp())
        self.store.add(f"free#ip#{caller.ip}", 1, free_end)
        self.store.add(f"free#dev#{caller.device_id}", 1, free_end)
        self.store.add(f"anon#d#{self._today()}", 1, day_end)


async def turnstile_siteverify(secret: str, token: str, ip: str) -> bool:
    """Cloudflare's server-side check (no SDK). Any failure, including a network error, fails closed."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={"secret": secret, "response": token, "remoteip": ip},
            )
        return bool(resp.json().get("success"))
    except Exception:  # noqa: BLE001
        return False
