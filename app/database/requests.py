from app.database.models import async_session
from app.database.models import User, PaymentTerm
from sqlalchemy import select, update


async def set_user(tg_id: int, nikname: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id, name=nikname))
            await session.commit()


async def update_user_name(tg_id: int, name: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            await session.execute(update(User).where(User.tg_id == tg_id).values(name=name))
            await session.commit()
