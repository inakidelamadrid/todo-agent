"""GET /me (BE-064): owner identity in camelCase; machines get 403.

roles (BE-067): ["admin"] when the caller is listed in ADMIN_USER_IDS,
[] otherwise.
"""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.principal import Machine, User
from app.security import require_user
from tests.conftest import KEY_ONE, OWNER_USER_ID, sign_token

OTHER_USER_ID = "user_other"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_returns_user_for_owner_token(client: TestClient) -> None:
    response = client.get("/me", headers=bearer(sign_token()))
    assert response.status_code == 200
    assert response.json() == {"userId": "user_owner", "kind": "user", "roles": []}


def test_me_with_api_key_returns_403(client: TestClient) -> None:
    response = client.get("/me", headers={"X-API-Key": KEY_ONE})
    assert response.status_code == 403
    assert response.json() == {"detail": "A signed-in user is required"}


def test_me_without_credentials_returns_401(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer, ApiKey"


def test_me_with_wrong_api_key_returns_401(client: TestClient) -> None:
    assert client.get("/me", headers={"X-API-Key": "wrong"}).status_code == 401


def test_me_with_non_owner_token_returns_403(client: TestClient) -> None:
    response = client.get("/me", headers=bearer(sign_token(sub="user_stranger")))
    assert response.status_code == 403
    assert response.json() == {"detail": "Not allowed"}


def test_require_user_returns_the_user_object() -> None:
    user = User(user_id="user_x")
    assert require_user(user) is user


def test_require_user_rejects_machines() -> None:
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        require_user(Machine(key_label="api-key"))
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "A signed-in user is required"


# --- roles (BE-067) ---------------------------------------------------------


@pytest.fixture()
def admin_client(
    make_client: Callable[[str], TestClient], monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Real app where OWNER is admin and OTHER is signed-in but not admin."""
    monkeypatch.setenv("ADMIN_USER_IDS", OWNER_USER_ID)
    monkeypatch.setenv("CLERK_ALLOWED_USER_IDS", f"{OWNER_USER_ID},{OTHER_USER_ID}")
    return make_client(KEY_ONE)


def test_me_roles_is_admin_for_listed_user(admin_client: TestClient) -> None:
    response = admin_client.get("/me", headers=bearer(sign_token()))
    assert response.status_code == 200
    assert response.json() == {
        "userId": "user_owner",
        "kind": "user",
        "roles": ["admin"],
    }


def test_me_roles_is_empty_for_other_user(admin_client: TestClient) -> None:
    response = admin_client.get(
        "/me", headers=bearer(sign_token(sub=OTHER_USER_ID))
    )
    assert response.status_code == 200
    body = response.json()
    assert body["roles"] == []
    # No ID from the admin list leaks to a non-admin.
    assert OWNER_USER_ID not in response.text


def test_me_still_rejects_machine_with_403(admin_client: TestClient) -> None:
    response = admin_client.get("/me", headers={"X-API-Key": KEY_ONE})
    assert response.status_code == 403
