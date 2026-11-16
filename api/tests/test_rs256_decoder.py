"""Tests for the real RS256 decoder (BE-061).

Keys are generated in-test with `cryptography` — never a real Clerk key —
and no token or key is ever printed.
"""

import base64
import hashlib
import hmac
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.session_token import get_token_decoder, make_rs256_decoder
from app.settings import Settings
from tests.fakes import make_claims


def _key_pair() -> tuple[str, str]:
    """Fresh RSA key pair as PEM strings: (private, public)."""
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


PRIVATE_PEM, PUBLIC_PEM = _key_pair()
OTHER_PRIVATE_PEM, _ = _key_pair()

CLAIMS = make_claims()


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(claims: dict, *, key: str = PRIVATE_PEM, algorithm: str = "RS256", headers=None) -> str:
    return jwt.encode(claims, key, algorithm=algorithm, headers=headers)


def test_valid_signature_returns_claims() -> None:
    decode = make_rs256_decoder(PUBLIC_PEM)
    out = decode(_sign(CLAIMS))
    assert out is not None
    assert out["sub"] == CLAIMS["sub"]
    assert out["azp"] == CLAIMS["azp"]


def test_wrong_key_signature_returns_none() -> None:
    decode = make_rs256_decoder(PUBLIC_PEM)
    assert decode(_sign(CLAIMS, key=OTHER_PRIVATE_PEM)) is None


def test_tampered_payload_returns_none() -> None:
    token = _sign(CLAIMS)
    header, payload, signature = token.split(".")
    # Flip the first character of the payload segment.
    forged = f"{header}.{'a' if payload[0] != 'a' else 'b'}{payload[1:]}.{signature}"
    assert make_rs256_decoder(PUBLIC_PEM)(forged) is None


def test_hs256_signed_with_public_key_returns_none() -> None:
    # Classic algorithm-confusion attempt: HS256 with the public key as the
    # HMAC secret. PyJWT refuses to *encode* such a token (asymmetric-key
    # guard), so build the forgery by hand the way an attacker would.
    header = b64url(b'{"alg":"HS256","typ":"JWT"}')
    payload = b64url(json.dumps(CLAIMS).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = b64url(
        hmac.new(PUBLIC_PEM.encode(), signing_input, hashlib.sha256).digest()
    )
    forged = f"{signing_input.decode()}.{signature}"
    assert make_rs256_decoder(PUBLIC_PEM)(forged) is None


def test_alg_none_returns_none() -> None:
    forged = jwt.encode(CLAIMS, None, algorithm="none")
    assert make_rs256_decoder(PUBLIC_PEM)(forged) is None


@pytest.mark.parametrize("garbage", ["not.a.jwt", "", "a", "a.b"])
def test_garbage_returns_none(garbage: str) -> None:
    assert make_rs256_decoder(PUBLIC_PEM)(garbage) is None


def test_expired_token_still_decodes() -> None:
    # Expiry is check_claims' job (it takes `now`); this function only signs.
    expired = {**CLAIMS, "exp": int(time.time()) - 3600}
    out = make_rs256_decoder(PUBLIC_PEM)(_sign(expired))
    assert out is not None and out["exp"] == expired["exp"]


def test_get_token_decoder_is_closed_when_key_is_empty() -> None:
    settings = Settings(_env_file=None, api_keys="k", clerk_jwt_public_key="")
    assert get_token_decoder(settings)("anything") is None


def test_get_token_decoder_accepts_configured_key() -> None:
    # Also proves the one-line \n PEM form works end to end.
    one_line = PUBLIC_PEM.strip().replace("\n", "\\n")
    settings = Settings(_env_file=None, api_keys="k", clerk_jwt_public_key=one_line)
    claims = get_token_decoder(settings)(_sign(CLAIMS))
    assert claims is not None and claims["sub"] == CLAIMS["sub"]


def test_get_token_decoder_caches_per_key() -> None:
    settings = Settings(_env_file=None, api_keys="k", clerk_jwt_public_key=PUBLIC_PEM)
    assert get_token_decoder(settings) is get_token_decoder(settings)
