"""Tests for the CLERK_JWT_PUBLIC_KEY .env inspector/repairer.

The PEM values are the static test-only public half from tests/keys.py —
the public key is not a secret.
"""

from scripts.clerk_jwks import BEGIN, END, KEY_NAME, check, extract_raw, fix, to_pem
from tests.keys import TEST_PUBLIC_PEM

ONE_LINE = TEST_PUBLIC_PEM.strip().replace("\n", "\\n")
QUOTED = f'"{TEST_PUBLIC_PEM.strip().replace(chr(10), chr(92) + "n")}"'


def _env(assignment: str) -> str:
    return f"API_KEYS=x\n{assignment}\nOTHER=1\n"


def test_check_accepts_one_line_escaped_form() -> None:
    ok, message = check(_env(f"{KEY_NAME}={ONE_LINE}"))
    assert ok
    assert "valid" in message and "2048-bit" in message


def test_check_accepts_quoted_form() -> None:
    ok, _ = check(_env(f"{KEY_NAME}={QUOTED}"))
    assert ok


def test_check_flags_real_newlines_as_unsalvageable_but_fixable() -> None:
    broken = _env(f"{KEY_NAME}={TEST_PUBLIC_PEM.rstrip()}")  # real newlines
    ok, message = check(broken)
    assert not ok
    assert "clerk-key-fix" in message  # tells the human the repair command

    # …and the fix recovers the exact original PEM.
    ok, fixed = fix(broken)
    assert ok
    assert to_pem(fixed.split("=", 1)[1]) == TEST_PUBLIC_PEM.strip()


def test_check_missing_key() -> None:
    ok, message = check(_env(""))
    assert not ok and "not set" in message


def test_check_garbage_value() -> None:
    ok, message = check(_env(f"{KEY_NAME}=not-a-pem"))
    assert not ok and "not look like a PEM" in message


def test_check_multiline_without_end_marker_is_unfixable() -> None:
    broken = _env(f"{KEY_NAME}={BEGIN}\nMIIBbroken")
    ok, message = check(broken)
    assert not ok and "cannot be salvaged" in message
    ok, _ = fix(broken)
    assert not ok


def test_extract_raw_finds_key_after_other_lines() -> None:
    form, raw = extract_raw(_env(f"{KEY_NAME}={ONE_LINE}"))
    assert form == "ok" and raw == ONE_LINE


def test_fix_on_already_valid_value_is_stable() -> None:
    ok, fixed = fix(_env(f"{KEY_NAME}={ONE_LINE}"))
    assert ok
    assert to_pem(fixed.split("=", 1)[1]) == TEST_PUBLIC_PEM.strip()
