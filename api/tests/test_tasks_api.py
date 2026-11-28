"""Integration tests for /tasks routes."""

import uuid
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.settings import Settings
from tests.conftest import KEY_ONE
from tests.keys import OWNER_USER_ID, sign_token

TASK = {
    "title": "Call dentist",
    "size": "S",
    "energy": "low",
    "context": "phone",
    "dueDate": "2026-11-28",
    "firstStep": "Find the number",
}
AUTH = {"X-API-Key": KEY_ONE}


@pytest.fixture(autouse=True)
def _clean_tasks(migrated_test_db: str) -> None:
    """Isolation per test: worker DB is shared, tasks table starts empty."""
    import asyncio

    from tests.conftest import _admin_exec

    settings = Settings(api_keys="test-suite")
    asyncio.run(
        _admin_exec(settings, "TRUNCATE tasks CASCADE", database=migrated_test_db)
    )


def _create_task(client: TestClient, **overrides) -> dict:
    response = client.post("/tasks", json={**TASK, **overrides}, headers=AUTH)
    assert response.status_code == 201, response.text
    return response.json()


# --------------------------------------------------------------------------
# BE-085: list and get
# --------------------------------------------------------------------------


def test_list_tasks_empty(db_client: TestClient) -> None:
    response = db_client.get("/tasks", headers=AUTH)
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filters_by_status(db_client: TestClient) -> None:
    _create_task(db_client, title="Active")
    done = _create_task(db_client, title="Done")
    db_client.post(f"/tasks/{done['id']}/complete", headers=AUTH)

    default_list = db_client.get("/tasks", headers=AUTH).json()
    assert [t["title"] for t in default_list] == ["Active"]

    done_list = db_client.get("/tasks?status=done&status=dropped", headers=AUTH).json()
    assert [t["title"] for t in done_list] == ["Done"]


def test_list_tasks_filters_by_parent_id(db_client: TestClient) -> None:
    parent = _create_task(db_client, title="Parent")
    _create_task(db_client, title="Child", parentId=parent["id"])
    _create_task(db_client, title="Other")

    children = db_client.get(f"/tasks?parentId={parent['id']}", headers=AUTH).json()
    assert [t["title"] for t in children] == ["Child"]


def test_list_tasks_top_level_only_by_default(db_client: TestClient) -> None:
    parent = _create_task(db_client, title="Parent")
    _create_task(db_client, title="Child", parentId=parent["id"])

    tasks = db_client.get("/tasks", headers=AUTH).json()
    assert [t["title"] for t in tasks] == ["Parent"]


def test_list_tasks_rejects_bogus_status(db_client: TestClient) -> None:
    response = db_client.get("/tasks?status=bogus", headers=AUTH)
    assert response.status_code == 422


def test_get_task_404(db_client: TestClient) -> None:
    response = db_client.get(f"/tasks/{uuid.uuid4()}", headers=AUTH)
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


# --------------------------------------------------------------------------
# BE-086: create
# --------------------------------------------------------------------------


def test_create_task_201(db_client: TestClient) -> None:
    response = db_client.post("/tasks", json=TASK, headers=AUTH)
    assert response.status_code == 201
    assert response.headers["Location"].startswith("/tasks/")
    body = response.json()
    assert body["title"] == "Call dentist"
    assert body["size"] == "S"
    assert body["status"] == "active"
    assert body["dueDate"] == "2026-11-28"


def test_create_task_invalid_title_422(db_client: TestClient) -> None:
    response = db_client.post("/tasks", json={**TASK, "title": ""}, headers=AUTH)
    assert response.status_code == 422


def test_create_subtask_too_deep(db_client: TestClient) -> None:
    parent = _create_task(db_client, title="Parent")
    sub = _create_task(db_client, title="Subtask", parentId=parent["id"])
    response = db_client.post(
        "/tasks", json={**TASK, "title": "Grandchild", "parentId": sub["id"]}, headers=AUTH
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Subtasks can only be one level deep"


def test_create_task_unknown_parent_422(db_client: TestClient) -> None:
    response = db_client.post(
        "/tasks", json={**TASK, "parentId": str(uuid.uuid4())}, headers=AUTH
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Parent task not found"


# --------------------------------------------------------------------------
# BE-087: patch and delete
# --------------------------------------------------------------------------


def test_patch_task_title(db_client: TestClient) -> None:
    task = _create_task(db_client)
    response = db_client.patch(f"/tasks/{task['id']}", json={"title": "Renamed"}, headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed"
    assert body["size"] == "S"


def test_patch_rejects_status_422(db_client: TestClient) -> None:
    task = _create_task(db_client)
    response = db_client.patch(f"/tasks/{task['id']}", json={"status": "done"}, headers=AUTH)
    assert response.status_code == 422


def test_patch_rejects_parent_id_422(db_client: TestClient) -> None:
    task = _create_task(db_client)
    response = db_client.patch(
        f"/tasks/{task['id']}", json={"parentId": str(uuid.uuid4())}, headers=AUTH
    )
    assert response.status_code == 422


def test_patch_done_task_allowed(db_client: TestClient) -> None:
    task = _create_task(db_client, title="Original")
    db_client.post(f"/tasks/{task['id']}/complete", headers=AUTH)
    response = db_client.patch(f"/tasks/{task['id']}", json={"title": "Renamed"}, headers=AUTH)
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"
    assert response.json()["status"] == "done"


def test_patch_null_clears_due_date(db_client: TestClient) -> None:
    task = _create_task(db_client)
    response = db_client.patch(f"/tasks/{task['id']}", json={"dueDate": None}, headers=AUTH)
    assert response.status_code == 200
    assert response.json()["dueDate"] is None


def test_delete_task_204_and_children_gone(db_client: TestClient) -> None:
    parent = _create_task(db_client, title="Parent")
    child = _create_task(db_client, title="Child", parentId=parent["id"])

    assert db_client.delete(f"/tasks/{parent['id']}", headers=AUTH).status_code == 204
    assert db_client.get(f"/tasks/{child['id']}", headers=AUTH).status_code == 404


def test_patch_delete_404(db_client: TestClient) -> None:
    missing = str(uuid.uuid4())
    assert db_client.patch(f"/tasks/{missing}", json={"title": "x"}, headers=AUTH).status_code == 404
    assert db_client.delete(f"/tasks/{missing}", headers=AUTH).status_code == 404


# --------------------------------------------------------------------------
# BE-088: status actions
# --------------------------------------------------------------------------


def test_complete_sets_completed_at(db_client: TestClient) -> None:
    task = _create_task(db_client)
    response = db_client.post(f"/tasks/{task['id']}/complete", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["completedAt"] is not None


def test_complete_twice_409(db_client: TestClient) -> None:
    task = _create_task(db_client)
    db_client.post(f"/tasks/{task['id']}/complete", headers=AUTH)
    response = db_client.post(f"/tasks/{task['id']}/complete", headers=AUTH)
    assert response.status_code == 409


def test_snooze_requires_until_422(db_client: TestClient) -> None:
    task = _create_task(db_client)
    response = db_client.post(f"/tasks/{task['id']}/snooze", json={}, headers=AUTH)
    assert response.status_code == 422


def test_snooze_rejects_past_date_422(db_client: TestClient) -> None:
    task = _create_task(db_client)
    response = db_client.post(
        f"/tasks/{task['id']}/snooze", json={"until": "2020-01-01"}, headers=AUTH
    )
    assert response.status_code == 422


def test_snooze_and_complete_from_snoozed(db_client: TestClient) -> None:
    task = _create_task(db_client)
    snoozed = db_client.post(
        f"/tasks/{task['id']}/snooze", json={"until": "2026-12-01"}, headers=AUTH
    )
    assert snoozed.status_code == 200
    assert snoozed.json()["status"] == "snoozed"
    assert snoozed.json()["snoozedUntil"] == "2026-12-01"

    # Reopen from snoozed is illegal.
    reopen = db_client.post(f"/tasks/{task['id']}/reopen", headers=AUTH)
    assert reopen.status_code == 409

    # Completing a snoozed task is legal.
    done = db_client.post(f"/tasks/{task['id']}/complete", headers=AUTH)
    assert done.status_code == 200
    assert done.json()["status"] == "done"


def test_reopen_dropped_task_clears_dropped_at(db_client: TestClient) -> None:
    task = _create_task(db_client)
    db_client.post(f"/tasks/{task['id']}/drop", headers=AUTH)
    response = db_client.post(f"/tasks/{task['id']}/reopen", headers=AUTH)
    body = response.json()
    assert body["status"] == "active"
    assert body["droppedAt"] is None


def test_actions_404(db_client: TestClient) -> None:
    missing = str(uuid.uuid4())
    assert db_client.post(f"/tasks/{missing}/complete", headers=AUTH).status_code == 404


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------

TASK_ID = str(uuid.uuid4())


@pytest.mark.parametrize(
    "do_request",
    [
        lambda c, h: c.get("/tasks", headers=h),
        lambda c, h: c.post("/tasks", json=TASK, headers=h),
        lambda c, h: c.get(f"/tasks/{TASK_ID}", headers=h),
        lambda c, h: c.patch(f"/tasks/{TASK_ID}", json={"title": "x"}, headers=h),
        lambda c, h: c.delete(f"/tasks/{TASK_ID}", headers=h),
        lambda c, h: c.post(f"/tasks/{TASK_ID}/complete", headers=h),
        lambda c, h: c.post(f"/tasks/{TASK_ID}/snooze", json={"until": "2026-11-28"}, headers=h),
        lambda c, h: c.post(f"/tasks/{TASK_ID}/drop", headers=h),
        lambda c, h: c.post(f"/tasks/{TASK_ID}/reopen", headers=h),
    ],
    ids=["list", "create", "get", "patch", "delete", "complete", "snooze", "drop", "reopen"],
)
def test_every_route_401s_without_or_with_wrong_key(
    db_client: TestClient, do_request: Callable
) -> None:
    assert do_request(db_client, {}).status_code == 401
    assert do_request(db_client, {"X-API-Key": "wrong"}).status_code == 401


def test_tasks_accept_owner_bearer_token(db_client: TestClient) -> None:
    token = sign_token(sub=OWNER_USER_ID)
    headers = {"Authorization": f"Bearer {token}"}
    response = db_client.get("/tasks", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
