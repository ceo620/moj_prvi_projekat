from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import ConflictError
from app.models import Tenant
from app.schemas import TenantCreate


class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload: TenantCreate) -> Tenant:
        existing = await self.session.exec(select(Tenant).where(Tenant.slug == payload.slug))
        if existing.first():
            raise ConflictError("Tenant slug already exists")
        tenant = Tenant(slug=payload.slug, name=payload.name, is_active=True)
        self.session.add(tenant)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant
