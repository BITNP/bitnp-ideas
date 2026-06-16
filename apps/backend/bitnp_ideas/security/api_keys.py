import base64
import hashlib
import hmac
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.core.config import settings
from bitnp_ideas.models.entities import ApiKey, ApiKeyNonce, AuditLog


def body_sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def build_canonical_request(
    method: str,
    path: str,
    canonical_query_string: str,
    body_hash: str,
    timestamp: str,
    nonce: str,
) -> str:
    return "\n".join([method.upper(), path, canonical_query_string, body_hash, timestamp, nonce])


def sign_canonical_request(secret: str, canonical_request: str) -> str:
    digest = hmac.new(secret.encode(), canonical_request.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def constant_time_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def canonical_query_string(raw_query_string: bytes) -> str:
    pairs = parse_qsl(raw_query_string.decode(), keep_blank_values=True)
    pairs.sort(key=lambda item: (item[0], item[1]))
    return urlencode(pairs)


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def scope_allowed(api_key: ApiKey, required_scope: str) -> bool:
    return required_scope in api_key.scopes


async def audit_api_key_failure(
    session: AsyncSession,
    action: str,
    metadata: dict,
) -> None:
    session.add(
        AuditLog(
            action=action,
            entity_type="api_key",
            entity_id=None,
            metadata_=metadata,
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()


async def verify_api_key_request(request: Request, session: AsyncSession) -> ApiKey | None:
    key_id = request.headers.get("X-Api-Key")
    if not key_id:
        return None

    timestamp = request.headers.get("X-Api-Timestamp")
    nonce = request.headers.get("X-Api-Nonce")
    signature_version = request.headers.get("X-Api-Signature-Version")
    signature = request.headers.get("X-Api-Signature")
    failure_metadata = {
        "key_id": key_id,
        "path": request.url.path,
        "method": request.method,
    }

    if not timestamp or not nonce or signature_version != "v1" or not signature:
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "missing_headers"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key headers."
        )

    result = await session.scalars(select(ApiKey).where(ApiKey.key_id == key_id))
    api_key = result.one_or_none()
    now = datetime.now(UTC)
    if api_key is None or not api_key.is_active or api_key.revoked_at is not None:
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "inactive_or_unknown"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")

    if api_key.expires_at and api_key.expires_at < now:
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "expired"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired.")

    if api_key.allowed_entities != settings.api_keys.allowed_entities:
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "disallowed_entities"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API key entity boundary invalid."
        )

    try:
        request_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "invalid_timestamp"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key timestamp."
        ) from exc

    if request_time.tzinfo is None:
        request_time = request_time.replace(tzinfo=UTC)
    skew = abs((now - request_time.astimezone(UTC)).total_seconds())
    if skew > settings.api_keys.timestamp_tolerance_seconds:
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "timestamp_skew"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key timestamp expired."
        )

    existing_nonce = await session.scalar(
        select(ApiKeyNonce).where(ApiKeyNonce.key_id == key_id, ApiKeyNonce.nonce == nonce)
    )
    if existing_nonce is not None:
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "nonce_replay"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key nonce replay."
        )

    body = await request.body()
    canonical = build_canonical_request(
        method=request.method,
        path=request.url.path,
        canonical_query_string=canonical_query_string(request.scope.get("query_string", b"")),
        body_hash=body_sha256_hex(body),
        timestamp=timestamp,
        nonce=nonce,
    )
    expected_signature = sign_canonical_request(api_key.secret_hash, canonical)
    if not constant_time_compare(signature, expected_signature):
        await audit_api_key_failure(
            session,
            "api_key.signature_failed",
            failure_metadata | {"reason": "signature_mismatch"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key signature."
        )

    session.add(
        ApiKeyNonce(
            key_id=key_id,
            nonce=nonce,
            timestamp=request_time,
            created_at=now,
        )
    )
    api_key.last_used_at = now
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key nonce replay."
        ) from exc

    return api_key
