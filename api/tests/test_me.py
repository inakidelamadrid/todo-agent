"""GET /me (BE-064): owner identity in camelCase; machines get 403."""

from fastapi.testclient import TestClient

from app.principal import Machine, User
from app.security import require_user
from tests.conftest import KEY_ONE, sign_token


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_me_returns_user_for_owner_token(client: TestClient) -> None:
    response = client.get("/me", headers=bearer(sign_token()))
    assert response.status_code == 200
    assert response.json() == {"userId": "user_owner", "kind": "user"}


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
