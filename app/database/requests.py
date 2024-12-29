from datetime import datetime

from app.database.models import async_session
from app.database.models import User, PaymentTerm
from sqlalchemy import select, update, and_
from dateutil.relativedelta import relativedelta


async def set_user(tg_id: int, nikname: str) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id, name=nikname))
            await session.commit()
            return True
    return False


async def update_user_name(tg_id: int, name: str) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            await session.execute(update(User).where(User.tg_id == tg_id).values(name=name))
            await session.commit()
            return True
    return False


async def set_payment_term(tg_id: int, start_time: str, count_months: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        pt = await session.scalar(select(PaymentTerm).
                                  where(and_(PaymentTerm.id_user == user.id,
                                             PaymentTerm.active == True)))
        if pt:
            if not start_time:
                start_time = datetime.now().date()
            else:
                start_time = start_time.split('.')
                day, month, year = int(start_time[0]), int(start_time[1]), int(start_time[2])
                start_time = datetime(year, month, day)
            end_time = start_time + relativedelta(months=count_months)
            session.add(PaymentTerm(id_user=user.id, start_time=start_time, end_time=end_time))
            await session.commit()
            return True
    return False


async def select_payment_terms() -> list:
    async with async_session() as session:
        users_terms = await session.execute(select(User, PaymentTerm).
                                            join(PaymentTerm, User.id == PaymentTerm.id_user).
                                            where(PaymentTerm.active == True))
        data = users_terms.all()
        return data


async def set_active_pay_term(pay_term_id: int) -> None:
    async with async_session() as session:
        await session(update(PaymentTerm).where(PaymentTerm.id == pay_term_id).values(active=False))
        await session.commit()
