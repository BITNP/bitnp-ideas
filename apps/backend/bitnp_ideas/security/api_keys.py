import base64
import hashlib
import hmac


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
