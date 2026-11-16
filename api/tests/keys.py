"""The test-only RSA key pair (BE-063), as STATIC constants.

Why static, not generated: the pytest-xdist controller imports our conftest
when collecting, and each worker inherits that process's environment at
spawn. A generated pair differs per process, so the public key baked into
the environment by the controller and the private key a worker later
generates never match (observed: InvalidSignatureError only under
``pytest -n auto``). A fixed pair is identical in every process.

This pair exists solely to stand in for Clerk in tests. It is not and never
was a real credential; committing it is intentional.
"""

import time
from typing import Any

import jwt

TEST_PRIVATE_PEM = """\
-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDuakVOEUga7fMV
fAFxrqFY9qP8seZMWOr9FlmbBwuSVTgfG9zVEz0KKWMOxwLhcXxS65X+knCwXc4B
Ivw8vCVOQ4AZWB/98S8SU+q2ib4kj+R7wxsefcjOx9vfnVASNSldVmrQD+akezKu
nOUnu4XZZlDuG0+EoUPNuOzzS4ffGVeh5uyVe4YUPljAP1CDe2Q2H9mUtzp5iEDi
q5cn63kRwVY8Olq3OHWE5U3CgFWZioXRxjt1ImVFh03kiHVhXGmdCnEN9haapyuP
6L6ATus7b0oRAfnaU3hcuW8/4rF0UdIiu3TahJ+IfSHGA+1xGbqu95Lz1orbfIz2
EiCZTLoHAgMBAAECggEAZDQNEd0okYztzFtUnguX67SpwqSglvkONrXkjkg9QFEJ
5+VFgNZ3oqQ3angRSWBxsMYsQhUZQL8EPK0QF5S6FzU+iyhjNc9fCdR0QykMXgCO
NsgPR1b1hZcxXcAX7bcjPgP6m5z7Qqk26XWuyG7DuFYM8K5Q0v0Wasns6OqXXhfQ
V+7KcYkD9WDgPRl4mwBe6iwM/gn7Uz/MzpD+6MCGXzuTJf8Kx/LVI+c7A70VAFJX
LtdnTRsGDLuf2wzQAOL2wU5tdzSIF5lonT2byi79PlG2p7JU2Dx3RTLZQcFQrYDE
rkRyTVdqneR8dzNc5S5NTQf2tZpEMTbNOVtUC2C7rQKBgQD/ikNYugxKxU236R6l
uF9qJl4Bl34sp7PMbCN4vhcd1a0c0xDSMzluMeIBJRKDqrOYh80Wp7DRQZk5ZqCG
RfWn1rlqzhGbYQ0CDymt+0Q8+hW43oMAdseTfTNWkUxlezStLiBtwmHpVRY7QVty
EnqtrPuHpfkVYgc829DM6UVHQwKBgQDu2B4Wl/Nl1ZM7NJm/h1eIq0i//ufDy4cB
0BYdEW81RB5s80ZUC88ispzaCcYDg1KipZC256i/CP5fJ2n7A/itR14K+D/Ubshi
VHs6Gmwjh4Zm5D1+F+UHULvJ30JmZdTeEcYWHr3bku4OTeYwWi56DnDV6yOlEvkJ
vsAHazCr7QKBgQCkDMYpet8TTVEUhTMonpGamuD00qWs00ipLq8i/53liFynSZTd
7QasiJeXto4JOxgrDtuJ9MOdwygz4n+hU95eDopgV8ST5J0uOj++srVfFAnH8glV
zetX8yN3KrZJ2+u4Vgl5jTXATuCDz/R96gEZ6BheQB4FLTaKSm/kbMkN8wKBgQC5
gSeVWr1TiZcJs+f6Jw8oeghN/phZrPkVwl16hDEAiQCslCI6YtWlWF6UxmSCE/wZ
kUgdlz2r6jtPAljA+iupwbVcBcXlo4mFPaJb1WvKCJet0HWmOr7KeLzxpLJ4v3ye
YeWdBpFlOfAlMgGn6lMQv6iJrVCJBHxiQkH5QRqTXQKBgQDKS+KLxD3zYsCdXPRG
6Yd5vlegF3H/xUNpv3O4JGvGeA2FhJbbPxGZdGnf+Q0SqZ7mRDjtwbsh8KwePmyQ
d8sL9ybsZjuXltEgZmPoeaEGbKp28SkVAbWtljXbGmupx1gkQEYQndis7jki/ZdY
56FIPwi9+gQvcuNrH1OiHIpwgw==
-----END PRIVATE KEY-----
"""

TEST_PUBLIC_PEM = """\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7mpFThFIGu3zFXwBca6h
WPaj/LHmTFjq/RZZmwcLklU4Hxvc1RM9CiljDscC4XF8UuuV/pJwsF3OASL8PLwl
TkOAGVgf/fEvElPqtom+JI/ke8MbHn3Izsfb351QEjUpXVZq0A/mpHsyrpzlJ7uF
2WZQ7htPhKFDzbjs80uH3xlXoebslXuGFD5YwD9Qg3tkNh/ZlLc6eYhA4quXJ+t5
EcFWPDpatzh1hOVNwoBVmYqF0cY7dSJlRYdN5Ih1YVxpnQpxDfYWmqcrj+i+gE7r
O29KEQH52lN4XLlvP+KxdFHSIrt02oSfiH0hxgPtcRm6rveS89aK23yM9hIgmUy6
BwIDAQAB
-----END PUBLIC KEY-----
"""

OWNER_USER_ID = "user_owner"
TEST_ORIGIN = "http://localhost:5173"


def sign_token(**overrides: Any) -> str:
    """Sign a session token with the static test key (real RS256)."""
    claims = {
        "sub": OWNER_USER_ID,
        "azp": TEST_ORIGIN,
        "exp": int(time.time()) + 3600,
        **overrides,
    }
    return jwt.encode(claims, TEST_PRIVATE_PEM, algorithm="RS256")
