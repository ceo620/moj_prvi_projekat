from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.audit import write_audit_log
from app.exceptions import NotFoundError
from app.models import Project, ProjectStatus, User
from app.pagination import paginate
from app.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload: ProjectCreate, actor: User) -> Project:
        project = Project(**payload.model_dump(), tenant_id=actor.tenant_id, created_by_user_id=actor.id)
        self.session.add(project)
        await self.session.flush()
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Project", entity_id=project.id, action="create", actor=actor.email, after=project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def list(self, *, actor: User, page: int, size: int, status_filter: Optional[ProjectStatus] = None, sponsor: Optional[str] = None, country: Optional[str] = None, search: Optional[str] = None):
        statement = select(Project).where(Project.tenant_id == actor.tenant_id)
        if status_filter:
            statement = statement.where(Project.status == status_filter)
        if sponsor:
            statement = statement.where(Project.sponsor.ilike(f"%{sponsor}%"))
        if country:
            statement = statement.where(Project.country.ilike(f"%{country}%"))
        if search:
            statement = statement.where(Project.name.ilike(f"%{search}%"))
        statement = statement.order_by(Project.id.desc())
        return await paginate(self.session, statement, page, size)

    async def get(self, project_id: int, actor: User) -> Project:
        statement = select(Project).where(Project.id == project_id, Project.tenant_id == actor.tenant_id).options(selectinload(Project.expenses), selectinload(Project.milestones))
        result = await self.session.exec(statement)
        project = result.first()
        if not project:
            raise NotFoundError("Project not found")
        return project

    async def update(self, project_id: int, payload: ProjectUpdate, actor: User) -> Project:
        project = await self.get(project_id, actor)
        before = Project.model_validate(project)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        project.updated_at = datetime.now(timezone.utc)
        self.session.add(project)
        await self.session.flush()
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Project", entity_id=project.id, action="update", actor=actor.email, before=before, after=project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete(self, project_id: int, actor: User) -> None:
        project = await self.get(project_id, actor)
        before = Project.model_validate(project)
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Project", entity_id=project.id, action="delete", actor=actor.email, before=before)
        await self.session.delete(project)
        await self.session.commit()
