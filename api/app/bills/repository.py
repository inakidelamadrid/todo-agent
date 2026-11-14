"""Async persistence for bills and payments.

Functions take a session and do exactly one thing. No HTTP, no FastAPI.
"""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bills.models import Bill, Payment
from app.bills.schemas import BillCreate, BillUpdate, PaymentIn


async def list_bills(session: AsyncSession, line: str | None = None) -> list[Bill]:
    stmt = select(Bill).order_by(Bill.due_day, Bill.name)
    if line is not None:
        stmt = stmt.where(Bill.line == line)
    return list((await session.scalars(stmt)).all())


async def get_bill(session: AsyncSession, bill_id: UUID) -> Bill | None:
    return await session.get(Bill, bill_id)


async def create_bill(session: AsyncSession, data: BillCreate) -> Bill:
    bill = Bill(**data.model_dump())
    session.add(bill)
    await session.flush()
    return bill


async def update_bill(session: AsyncSession, bill: Bill, patch: BillUpdate) -> Bill:
    for field, value in patch.model_dump(exclude_unset=True).items():
        setattr(bill, field, value)
    await session.flush()
    await session.refresh(bill)  # reload server-side onupdate columns (updated_at)
    return bill


async def delete_bill(session: AsyncSession, bill: Bill) -> None:
    await session.delete(bill)


async def payments_for_month(session: AsyncSession, month: str) -> list[Payment]:
    stmt = select(Payment).where(Payment.period == month).order_by(Payment.bill_id)
    return list((await session.scalars(stmt)).all())


async def get_payment(session: AsyncSession, bill_id: UUID, period: str) -> Payment | None:
    return await session.get(Payment, (bill_id, period))


async def upsert_payment(
    session: AsyncSession, bill: Bill, period: str, data: PaymentIn
) -> Payment:
    """Idempotent: re-paying the same period replaces the amount/date."""
    payment = await get_payment(session, bill.id, period)
    if payment is None:
        payment = Payment(bill_id=bill.id, period=period, **data.model_dump())
        session.add(payment)
    else:
        payment.actual_cents = data.actual_cents
        payment.paid_at = data.paid_at
    await session.flush()
    return payment


async def delete_payment(session: AsyncSession, bill_id: UUID, period: str) -> None:
    """Idempotent delete: succeeds whether or not the payment existed."""
    await session.execute(
        delete(Payment).where(Payment.bill_id == bill_id, Payment.period == period)
    )
