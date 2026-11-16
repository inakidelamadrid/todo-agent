"""Test fakes for the session-token port (BE-060).

No test ever needs a real key: the fake decoder maps token strings to claim
dicts, and unknown tokens decode to ``None`` (not validly signed).
"""

from typing import Any

from app.session_token import Claims, DecodeToken


def make_claims(**overrides: Any) -> dict[str, Any]:
    """A valid claim set; tests tweak it with overrides."""
    return {
        "sub": "user_owner",
        "azp": "http://localhost:5173",
        "exp": 4_000_000_000,  # far in the future, no clock needed
        **overrides,
    }


def fake_decoder(table: "dict[str, Claims]") -> DecodeToken:
    """Return claims for tokens in ``table``; ``None`` for anything else."""

    def decode(token: str) -> "Claims | None":
        return table.get(token)

    return decode
