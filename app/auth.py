from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import time

from fastapi import HTTPException, status


DEMO_USERS: dict[str, str] = {
    "alice": "Alice Analyst",
    "bob": "Bob Manager",
}


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: str


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def issue_demo_token(
    user_id: str,
    *,
    secret: str,
    ttl_seconds: int,
    now: int | None = None,
) -> str:
    if user_id not in DEMO_USERS:
        raise ValueError("unknown demo user")

    issued_at = int(time.time() if now is None else now)
    payload = {
        "sub": user_id,
        "iat": issued_at,
        "exp": issued_at + ttl_seconds,
        "kind": "demo-access",
    }
    encoded_payload = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{_b64encode(signature)}"


def verify_demo_token(
    token: str,
    *,
    secret: str,
    now: int | None = None,
) -> AuthenticatedIdentity:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        supplied_signature = _b64decode(encoded_signature)
    except (ValueError, TypeError):
        _unauthorized("invalid access token")

    expected_signature = hmac.new(
        secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(supplied_signature, expected_signature):
        _unauthorized("invalid access token")

    try:
        payload = json.loads(_b64decode(encoded_payload))
        user_id = str(payload["sub"])
        expires_at = int(payload["exp"])
        kind = payload["kind"]
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        _unauthorized("invalid access token")

    current_time = int(time.time() if now is None else now)
    if kind != "demo-access" or expires_at <= current_time or user_id not in DEMO_USERS:
        _unauthorized("expired or invalid access token")

    return AuthenticatedIdentity(user_id=user_id)


def _unauthorized(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
