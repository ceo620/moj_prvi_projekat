from datetime import datetime, timezone
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.audit import write_audit_log
from app.exceptions import NotFoundError
from app.models import Milestone, MilestoneStatus, Project, User
from app.pagination import paginate
from app.schemas import MilestoneCreate, MilestoneUpdate


class MilestoneService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload: MilestoneCreate, actor: User) -> Milestone:
        project = await self.session.get(Project, payload.project_id)
        if not project or project.tenant_id != actor.tenant_id:
            raise NotFoundError("Project not found")
        milestone = Milestone(**payload.model_dump(), tenant_id=actor.tenant_id)
        self.session.add(milestone)
        await self.session.flush()
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Milestone", entity_id=milestone.id, action="create", actor=actor.email, after=milestone)
        await self.session.commit()
        await self.session.refresh(milestone)
        return milestone

    async def list(self, *, actor: User, page: int, size: int, project_id: Optional[int] = None, status_filter: Optional[MilestoneStatus] = None):
        statement = select(Milestone).where(Milestone.tenant_id == actor.tenant_id)
        if project_id is not None:
            statement = statement.where(Milestone.project_id == project_id)
        if status_filter is not None:
            statement = statement.where(Milestone.status == status_filter)
        statement = statement.order_by(Milestone.id.desc())
        return await paginate(self.session, statement, page, size)

    async def get(self, milestone_id: int, actor: User) -> Milestone:
        result = await self.session.exec(select(Milestone).where(Milestone.id == milestone_id, Milestone.tenant_id == actor.tenant_id))
        milestone = result.first()
        if not milestone:
            raise NotFoundError("Milestone not found")
        return milestone

    async def update(self, milestone_id: int, payload: MilestoneUpdate, actor: User) -> Milestone:
        milestone = await self.get(milestone_id, actor)
        before = Milestone.model_validate(milestone)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(milestone, field, value)
        milestone.updated_at = datetime.now(timezone.utc)
        self.session.add(milestone)
        await self.session.flush()
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Milestone", entity_id=milestone.id, action="update", actor=actor.email, before=before, after=milestone)
        await self.session.commit()
        await self.session.refresh(milestone)
        return milestone

    async def delete(self, milestone_id: int, actor: User) -> None:
        milestone = await self.get(milestone_id, actor)
        before = Milestone.model_validate(milestone)
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Milestone", entity_id=milestone.id, action="delete", actor=actor.email, before=before)
        await self.session.delete(milestone)
        await self.session.commit()
