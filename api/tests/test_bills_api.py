"""Integration tests for /bills and /payments against real Postgres.

Each xdist worker runs against its own migrated database (see conftest).
"""

import uuid
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.settings import Settings
from tests.conftest import KEY_ONE, _admin_exec

BILL = {
    "name": "Electricity",
    "note": "CFE",
    "line": "utilities",
    "currency": "MXN",
    "estimatedCents": 150_000,
    "dueDay": 15,
    "recurrence": "monthly",
    "startMonth": "2026-01",
}

AUTH = {"X-API-Key": KEY_ONE}


@pytest.fixture(autouse=True)
def _clean_tables(migrated_test_db: str) -> None:
    """Isolation per test: worker DB is shared, tables start empty."""
    import asyncio

    settings = Settings(api_keys="test-suite")
    asyncio.run(
        _admin_exec(settings, "TRUNCATE bills CASCADE", database=migrated_test_db)
    )


def _create_bill(client: TestClient, **overrides) -> dict:
    response = client.post("/bills", json={**BILL, **overrides}, headers=AUTH)
    assert response.status_code == 201, response.text
    return response.json()


# --------------------------------------------------------------------------
# CRUD
# --------------------------------------------------------------------------


def test_create_bill_returns_201_location_and_camel_case(db_client: TestClient) -> None:
    response = db_client.post("/bills", json=BILL, headers=AUTH)

    assert response.status_code == 201
    assert response.headers["Location"].startswith("/bills/")
    body = response.json()
    assert body["name"] == "Electricity"
    assert body["estimatedCents"] == 150_000
    assert body["dueDay"] == 15
    assert body["startMonth"] == "2026-01"
    assert isinstance(body["estimatedCents"], int)  # integer cents, never float
    uuid.UUID(body["id"])  # valid UUID
    assert body["createdAt"] and body["updatedAt"]


def test_list_bills_orders_by_due_day_then_name_and_filters_line(db_client: TestClient) -> None:
    _create_bill(db_client, name="Zeta", dueDay=20)
    _create_bill(db_client, name="Alpha", dueDay=5)
    _create_bill(db_client, name="Beta", dueDay=5, line="streaming")

    bills = db_client.get("/bills", headers=AUTH).json()
    assert [b["name"] for b in bills] == ["Alpha", "Beta", "Zeta"]

    streaming = db_client.get("/bills?line=streaming", headers=AUTH).json()
    assert [b["name"] for b in streaming] == ["Beta"]


def test_get_patch_delete_bill(db_client: TestClient) -> None:
    bill = _create_bill(db_client)

    fetched = db_client.get(f"/bills/{bill['id']}", headers=AUTH)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Electricity"

    patched = db_client.patch(
        f"/bills/{bill['id']}", json={"dueDay": 28}, headers=AUTH
    )
    assert patched.status_code == 200
    assert patched.json()["dueDay"] == 28
    assert patched.json()["name"] == "Electricity"  # untouched fields kept

    assert db_client.delete(f"/bills/{bill['id']}", headers=AUTH).status_code == 204
    gone = db_client.get(f"/bills/{bill['id']}", headers=AUTH)
    assert gone.status_code == 404
    assert gone.json() == {"detail": "Bill not found"}


def test_get_missing_bill_is_404(db_client: TestClient) -> None:
    response = db_client.get(f"/bills/{uuid.uuid4()}", headers=AUTH)
    assert response.status_code == 404
    assert response.json() == {"detail": "Bill not found"}


def test_bad_uuid_and_bad_month_never_500(db_client: TestClient) -> None:
    assert db_client.get("/bills/not-a-uuid", headers=AUTH).status_code == 422
    assert db_client.get("/payments", headers=AUTH).status_code == 422  # month required
    assert db_client.get("/payments?month=2026-1", headers=AUTH).status_code == 422
    bill = _create_bill(db_client)
    assert (
        db_client.put(
            f"/bills/{bill['id']}/payments/26-01",
            json={"actualCents": 1, "paidAt": "2026-01-15"},
            headers=AUTH,
        ).status_code
        == 422
    )


# --------------------------------------------------------------------------
# Payments
# --------------------------------------------------------------------------


def test_payment_lifecycle_and_idempotency(db_client: TestClient) -> None:
    bill = _create_bill(db_client)

    paid = db_client.put(
        f"/bills/{bill['id']}/payments/2026-01",
        json={"actualCents": 140_000, "paidAt": "2026-01-15"},
        headers=AUTH,
    )
    assert paid.status_code == 200
    assert paid.json() == {
        "billId": bill["id"],
        "period": "2026-01",
        "actualCents": 140_000,
        "paidAt": "2026-01-15",
    }

    # Upsert replaces the amount (still exactly one payment).
    repaid = db_client.put(
        f"/bills/{bill['id']}/payments/2026-01",
        json={"actualCents": 145_500, "paidAt": "2026-01-16"},
        headers=AUTH,
    )
    assert repaid.status_code == 200
    assert repaid.json()["actualCents"] == 145_500
    payments = db_client.get("/payments?month=2026-01", headers=AUTH).json()
    assert len(payments) == 1
    assert payments[0]["actualCents"] == 145_500

    # Undo is idempotent: 204 both times.
    url = f"/bills/{bill['id']}/payments/2026-01"
    assert db_client.delete(url, headers=AUTH).status_code == 204
    assert db_client.delete(url, headers=AUTH).status_code == 204
    assert db_client.get("/payments?month=2026-01", headers=AUTH).json() == []


def test_cannot_pay_in_a_not_due_month(db_client: TestClient) -> None:
    bill = _create_bill(db_client, recurrence="bimonthly", startMonth="2026-01")

    response = db_client.put(
        f"/bills/{bill['id']}/payments/2026-02",  # off-cycle for bimonthly
        json={"actualCents": 100, "paidAt": "2026-02-15"},
        headers=AUTH,
    )
    assert response.status_code == 422
    assert db_client.put(
        f"/bills/{bill['id']}/payments/2026-03",
        json={"actualCents": 100, "paidAt": "2026-03-15"},
        headers=AUTH,
    ).status_code == 200


def test_payments_filtered_by_month(db_client: TestClient) -> None:
    bill = _create_bill(db_client)
    for month in ("2026-01", "2026-02"):
        db_client.put(
            f"/bills/{bill['id']}/payments/{month}",
            json={"actualCents": 100, "paidAt": f"{month}-15"},
            headers=AUTH,
        )

    only = db_client.get("/payments?month=2026-02", headers=AUTH).json()
    assert [p["period"] for p in only] == ["2026-02"]


def test_delete_bill_cascades_its_payments(db_client: TestClient) -> None:
    bill = _create_bill(db_client)
    db_client.put(
        f"/bills/{bill['id']}/payments/2026-01",
        json={"actualCents": 100, "paidAt": "2026-01-15"},
        headers=AUTH,
    )
    assert db_client.delete(f"/bills/{bill['id']}", headers=AUTH).status_code == 204
    assert db_client.get("/payments?month=2026-01", headers=AUTH).json() == []


# --------------------------------------------------------------------------
# Auth: every route rejects missing/wrong keys
# --------------------------------------------------------------------------

BILL_ID = str(uuid.uuid4())


@pytest.mark.parametrize(
    "do_request",
    [
        lambda c, h: c.get("/bills", headers=h),
        lambda c, h: c.post("/bills", json=BILL, headers=h),
        lambda c, h: c.get(f"/bills/{BILL_ID}", headers=h),
        lambda c, h: c.patch(f"/bills/{BILL_ID}", json={"dueDay": 3}, headers=h),
        lambda c, h: c.delete(f"/bills/{BILL_ID}", headers=h),
        lambda c, h: c.get("/payments?month=2026-01", headers=h),
        lambda c, h: c.put(
            f"/bills/{BILL_ID}/payments/2026-01",
            json={"actualCents": 1, "paidAt": "2026-01-15"},
            headers=h,
        ),
        lambda c, h: c.delete(f"/bills/{BILL_ID}/payments/2026-01", headers=h),
    ],
    ids=["list", "create", "get", "patch", "delete", "payments", "pay", "unpay"],
)
def test_every_route_401s_without_or_with_wrong_key(
    db_client: TestClient, do_request: Callable
) -> None:
    assert do_request(db_client, {}).status_code == 401
    assert do_request(db_client, {"X-API-Key": "wrong"}).status_code == 401
