"""Protected /bills and /payments routes.

Thin layer: validate → repository → schema. Mounted with
``dependencies=[Depends(require_api_key)]`` in ``app/main.py``.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.bills import repository
from app.bills.domain import MONTH_PATTERN, is_due_in_month
from app.bills.models import Bill
from app.bills.schemas import (
    BillCreate,
    BillOut,
    BillUpdate,
    PaymentIn,
    PaymentOut,
)
from app.db import get_session

Session = Annotated[AsyncSession, Depends(get_session)]

bills_router = APIRouter(prefix="/bills", tags=["bills"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])

MonthQuery = Annotated[str, Query(pattern=MONTH_PATTERN)]
PeriodPath = Annotated[str, Path(pattern=MONTH_PATTERN)]


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found"
    )


async def _bill_or_404(session: AsyncSession, bill_id: UUID) -> Bill:
    bill = await repository.get_bill(session, bill_id)
    if bill is None:
        raise _not_found()
    return bill


@bills_router.get(
    "", response_model=list[BillOut], summary="List bills, optionally filtered by line"
)
async def list_bills(session: Session, line: str | None = None) -> list[Bill]:
    return await repository.list_bills(session, line)


@bills_router.post("", status_code=status.HTTP_201_CREATED, summary="Create a bill")
async def create_bill(
    session: Session, data: BillCreate, response: Response
) -> BillOut:
    bill = await repository.create_bill(session, data)
    response.headers["Location"] = f"/bills/{bill.id}"
    return BillOut.model_validate(bill)


@bills_router.get("/{bill_id}", response_model=BillOut, summary="Get one bill")
async def get_bill(session: Session, bill_id: UUID) -> BillOut:
    return BillOut.model_validate(await _bill_or_404(session, bill_id))


@bills_router.patch("/{bill_id}", response_model=BillOut, summary="Partially update a bill")
async def update_bill(session: Session, bill_id: UUID, patch: BillUpdate) -> BillOut:
    bill = await _bill_or_404(session, bill_id)
    return BillOut.model_validate(await repository.update_bill(session, bill, patch))


@bills_router.delete(
    "/{bill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a bill and its payments"
)
async def delete_bill(session: Session, bill_id: UUID) -> None:
    bill = await _bill_or_404(session, bill_id)
    await repository.delete_bill(session, bill)


@bills_router.put(
    "/{bill_id}/payments/{period}",
    response_model=PaymentOut,
    tags=["payments"],
    summary="Mark a bill paid for a period (idempotent upsert)",
)
async def pay_bill(
    session: Session, bill_id: UUID, period: PeriodPath, data: PaymentIn
) -> PaymentOut:
    bill = await _bill_or_404(session, bill_id)
    if not is_due_in_month(bill.recurrence, bill.start_month, period):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Bill {bill_id} is not due in {period}",
        )
    payment = await repository.upsert_payment(session, bill, period, data)
    return PaymentOut.model_validate(payment)


@bills_router.delete(
    "/{bill_id}/payments/{period}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["payments"],
    summary="Undo paid for a period (idempotent)",
)
async def unpay_bill(session: Session, bill_id: UUID, period: PeriodPath) -> None:
    await _bill_or_404(session, bill_id)
    await repository.delete_payment(session, bill_id, period)


@payments_router.get(
    "",
    response_model=list[PaymentOut],
    summary="List payments for a month (month is required)",
)
async def list_payments(session: Session, month: MonthQuery) -> list[Payment]:
    return await repository.payments_for_month(session, month)
