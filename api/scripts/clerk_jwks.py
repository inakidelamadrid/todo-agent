"""Inspect and repair CLERK_JWT_PUBLIC_KEY in api/.env (never edits the file).

The failure mode this exists for: a PEM pasted with REAL newlines is not
valid dotenv — python-dotenv fails at the line and the app cannot start
(BE-063 makes the key mandatory). The valid storage form is one line with
``\\n`` escapes (or the whole value quoted).

Commands (via Makefile):
  ``make clerk-key-check``  → ``check``  (exit 0 iff the key parses AND is a
                                         valid RSA public key; prints a message)
  ``make clerk-key-fix``    → ``fix``    (prints a paste-ready one-line
                                         ``CLERK_JWT_PUBLIC_KEY=…``)

Pure core, thin CLI: every diagnoser is a function over the file text.
"""

import argparse
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

KEY_NAME = "CLERK_JWT_PUBLIC_KEY"
BEGIN = "-----BEGIN PUBLIC KEY-----"
END = "-----END PUBLIC KEY-----"

DEFAULT_ENV = Path(__file__).resolve().parent.parent / ".env"


def extract_raw(env_text: str) -> tuple[str, str | None]:
    """Locate the configured value. Returns (form, value):

    form ``missing``      — no such line            (value None)
    form ``multiline``    — PEM pasted with real newlines (value = whole PEM)
    form ``ok``           — value on a single line  (quoted or with \\n escapes)
    """
    lines = env_text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(f"{KEY_NAME}="):
            continue
        value = line.split("=", 1)[1].strip()
        if BEGIN in value and END not in value:
            # Real-newline paste: gather the following lines through the END.
            collected = [value]
            for follow in lines[index + 1 :]:
                collected.append(follow)
                if END in follow:
                    break
            if END not in collected[-1]:
                return "multiline", None  # no END marker: not salvageable
            return "multiline", "\n".join(collected)
        return "ok", value
    return "missing", None


def to_pem(raw: str) -> str | None:
    """A one-line value to a real PEM, or None when it cannot be one."""
    value = raw.strip()
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        value = value[1:-1]
    value = value.replace("\\n", "\n").strip()
    return value if BEGIN in value and END in value else None


def rsa_key_size(pem: str) -> int | None:
    """Bits of the RSA public key in the PEM; None when it won't load."""
    try:
        key = serialization.load_pem_public_key(pem.encode())
    except (ValueError, TypeError):
        return None
    if not isinstance(key, rsa.RSAPublicKey):
        return None
    return key.key_size


def check(env_text: str) -> tuple[bool, str]:
    """Validate the configured key. Returns (ok, message)."""
    form, raw = extract_raw(env_text)
    if form == "missing":
        return False, f"✗ {KEY_NAME} is not set in api/.env — see api/.env.example"
    if form == "multiline":
        if raw is None:
            return False, (
                f"✗ {KEY_NAME} spans multiple lines in api/.env and has no\n"
                f"  {END} marker — it cannot be salvaged. Re-copy the PEM\n"
                "  from the Clerk dashboard."
            )
        return False, (
            f"✗ {KEY_NAME} is pasted with real newlines — dotenv cannot parse\n"
            "  that (this breaks the app). Run: make clerk-key-fix, then paste\n"
            "  the printed line into api/.env."
        )
    pem = to_pem(raw or "")
    if pem is None:
        return False, f"✗ {KEY_NAME} does not look like a PEM public key."
    bits = rsa_key_size(pem)
    if bits is None:
        return False, f"✗ {KEY_NAME} is PEM-shaped but not a loadable RSA public key."
    multiline_note = ""  # single-line, parseable
    return True, f"✓ {KEY_NAME} is a valid {bits}-bit RSA public key.{multiline_note}"


def fix(env_text: str) -> tuple[bool, str]:
    """A paste-ready one-line assignment, or why there isn't one."""
    form, raw = extract_raw(env_text)
    pem = to_pem(raw or "") if form != "missing" else None
    if pem is None:
        return False, f"✗ Nothing to fix ({check(env_text)[1]})"
    if rsa_key_size(pem) is None:
        return False, "✗ The value is not a loadable RSA public key; re-copy it."
    one_line = pem.replace("\n", "\\n")
    return True, f"{KEY_NAME}={one_line}"


def main() -> None:
    parser = argparse.ArgumentParser(prog="clerk_jwks")
    parser.add_argument("command", choices=["check", "fix"])
    parser.add_argument(
        "--env-file", type=Path, default=DEFAULT_ENV, help=argparse.SUPPRESS
    )
    args = parser.parse_args()

    run = check if args.command == "check" else fix
    if not args.env_file.exists():
        print(f"✗ {args.env_file} does not exist — copy api/.env.example first")
        raise SystemExit(1)
    ok, message = run(args.env_file.read_text())
    print(message)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
