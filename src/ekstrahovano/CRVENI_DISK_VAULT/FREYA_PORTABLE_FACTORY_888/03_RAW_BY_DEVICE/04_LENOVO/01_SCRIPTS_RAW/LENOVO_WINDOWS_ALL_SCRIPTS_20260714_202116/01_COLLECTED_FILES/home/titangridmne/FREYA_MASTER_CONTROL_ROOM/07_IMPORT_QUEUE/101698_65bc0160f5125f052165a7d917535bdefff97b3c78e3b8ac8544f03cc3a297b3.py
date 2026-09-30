from datetime import date, datetime
from decimal import Decimal
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import ExpenseCategory, MilestoneStatus, ProjectStatus, UserRole

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class TenantCreate(BaseModel):
    slug: str
    name: str


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    tenant_slug: str
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    role: UserRole = UserRole.VIEWER


class UserLogin(BaseModel):
    tenant_slug: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sponsor: Optional[str] = None
    sector: Optional[str] = None
    country: str = "Montenegro"
    currency: str = "EUR"
    budget: Decimal = Decimal("0.00")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.DRAFT


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sponsor: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    budget: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None


class ExpenseCreate(BaseModel):
    project_id: int
    category: ExpenseCategory
    description: Optional[str] = None
    amount: Decimal
    expense_date: date
    currency: str = "EUR"


class ExpenseUpdate(BaseModel):
    category: Optional[ExpenseCategory] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    currency: Optional[str] = None


class MilestoneCreate(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = None
    due_date: date
    status: MilestoneStatus = MilestoneStatus.PLANNED
    completion_percent: Decimal = Decimal("0.00")

    @field_validator("completion_percent")
    @classmethod
    def validate_completion(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 100:
            raise ValueError("completion_percent must be between 0 and 100")
        return v


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[MilestoneStatus] = None
    completion_percent: Optional[Decimal] = None


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    project_id: int
    category: ExpenseCategory
    description: Optional[str]
    amount: Decimal
    expense_date: date
    currency: str
    created_at: datetime
    updated_at: datetime


class MilestoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    project_id: int
    title: str
    description: Optional[str]
    due_date: date
    status: MilestoneStatus
    completion_percent: Decimal
    created_at: datetime
    updated_at: datetime


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    created_by_user_id: Optional[int]
    name: str
    description: Optional[str]
    sponsor: Optional[str]
    sector: Optional[str]
    country: str
    currency: str
    budget: Decimal
    start_date: Optional[date]
    end_date: Optional[date]
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectReadDetailed(ProjectRead):
    expenses: list[ExpenseRead] = []
    milestones: list[MilestoneRead] = []


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    entity_name: str
    entity_id: int
    action: str
    actor: str
    before_json: Optional[str]
    after_json: Optional[str]
    created_at: datetime
