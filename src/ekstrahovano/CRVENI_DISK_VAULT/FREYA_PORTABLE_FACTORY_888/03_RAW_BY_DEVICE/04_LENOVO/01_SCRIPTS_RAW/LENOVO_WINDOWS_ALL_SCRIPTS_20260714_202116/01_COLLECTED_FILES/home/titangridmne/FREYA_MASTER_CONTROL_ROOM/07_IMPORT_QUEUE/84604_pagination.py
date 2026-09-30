from math import ceil

from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession


async def paginate(session: AsyncSession, statement, page: int, size: int):
    subq = statement.order_by(None).subquery()
    total_stmt = select(func.count()).select_from(subq)
    total = (await session.exec(total_stmt)).one()

    paged_stmt = statement.offset((page - 1) * size).limit(size)
    items = list((await session.exec(paged_stmt)).all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": ceil(total / size) if total else 0,
    }
