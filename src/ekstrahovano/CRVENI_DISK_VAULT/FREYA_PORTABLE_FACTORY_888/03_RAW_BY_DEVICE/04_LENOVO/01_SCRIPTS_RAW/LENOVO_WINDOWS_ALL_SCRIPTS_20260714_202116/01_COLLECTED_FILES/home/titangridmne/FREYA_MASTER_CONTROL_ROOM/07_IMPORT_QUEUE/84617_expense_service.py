from datetime import datetime, timezone
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.audit import write_audit_log
from app.exceptions import NotFoundError
from app.models import Expense, ExpenseCategory, Project, User
from app.pagination import paginate
from app.schemas import ExpenseCreate, ExpenseUpdate


class ExpenseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload: ExpenseCreate, actor: User) -> Expense:
        project = await self.session.get(Project, payload.project_id)
        if not project or project.tenant_id != actor.tenant_id:
            raise NotFoundError("Project not found")
        expense = Expense(**payload.model_dump(), tenant_id=actor.tenant_id)
        self.session.add(expense)
        await self.session.flush()
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Expense", entity_id=expense.id, action="create", actor=actor.email, after=expense)
        await self.session.commit()
        await self.session.refresh(expense)
        return expense

    async def list(self, *, actor: User, page: int, size: int, project_id: Optional[int] = None, category: Optional[ExpenseCategory] = None, currency: Optional[str] = None):
        statement = select(Expense).where(Expense.tenant_id == actor.tenant_id)
        if project_id is not None:
            statement = statement.where(Expense.project_id == project_id)
        if category is not None:
            statement = statement.where(Expense.category == category)
        if currency:
            statement = statement.where(Expense.currency.ilike(currency))
        statement = statement.order_by(Expense.id.desc())
        return await paginate(self.session, statement, page, size)

    async def get(self, expense_id: int, actor: User) -> Expense:
        result = await self.session.exec(select(Expense).where(Expense.id == expense_id, Expense.tenant_id == actor.tenant_id))
        expense = result.first()
        if not expense:
            raise NotFoundError("Expense not found")
        return expense

    async def update(self, expense_id: int, payload: ExpenseUpdate, actor: User) -> Expense:
        expense = await self.get(expense_id, actor)
        before = Expense.model_validate(expense)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(expense, field, value)
        expense.updated_at = datetime.now(timezone.utc)
        self.session.add(expense)
        await self.session.flush()
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Expense", entity_id=expense.id, action="update", actor=actor.email, before=before, after=expense)
        await self.session.commit()
        await self.session.refresh(expense)
        return expense

    async def delete(self, expense_id: int, actor: User) -> None:
        expense = await self.get(expense_id, actor)
        before = Expense.model_validate(expense)
        await write_audit_log(self.session, tenant_id=actor.tenant_id, entity_name="Expense", entity_id=expense.id, action="delete", actor=actor.email, before=before)
        await self.session.delete(expense)
        await self.session.commit()
