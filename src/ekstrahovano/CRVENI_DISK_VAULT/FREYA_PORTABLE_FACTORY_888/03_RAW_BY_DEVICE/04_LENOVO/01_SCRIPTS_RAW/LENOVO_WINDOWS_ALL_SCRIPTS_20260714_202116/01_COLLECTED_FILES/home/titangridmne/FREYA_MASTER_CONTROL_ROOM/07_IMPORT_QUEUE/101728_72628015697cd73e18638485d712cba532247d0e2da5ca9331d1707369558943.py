from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

from .models import ExpenseType, MilestoneStatus


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: datetime
    budget: Decimal = Field(gt=0, max_digits=18, decimal_places=2)

    @field_validator('name')
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('name is required')
        return value


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: Optional[datetime] = None
    budget: Optional[Decimal] = Field(default=None, gt=0, max_digits=18, decimal_places=2)

    @field_validator('name')
    @classmethod
    def strip_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError('name cannot be blank')
        return value


class ExpenseBase(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    type: ExpenseType
    date: datetime


class ExpenseCreate(ExpenseBase):
    project_id: int


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    type: Optional[ExpenseType] = None
    date: Optional[datetime] = None


class MilestoneBase(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    due_date: datetime
    status: MilestoneStatus = MilestoneStatus.PENDING


class MilestoneCreate(MilestoneBase):
    project_id: int


class MilestoneUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=300)
    due_date: Optional[datetime] = None
    status: Optional[MilestoneStatus] = None


class ExpenseRead(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime


class MilestoneRead(MilestoneBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectRead):
    expenses: list[ExpenseRead] = []
    milestones: list[MilestoneRead] = []

    @computed_field
    @property
    def total_spent(self) -> Decimal:
        return sum((e.amount for e in self.expenses), Decimal('0.00'))

    @computed_field
    @property
    def capex_total(self) -> Decimal:
        return sum((e.amount for e in self.expenses if e.type == ExpenseType.CAPEX), Decimal('0.00'))

    @computed_field
    @property
    def opex_total(self) -> Decimal:
        return sum((e.amount for e in self.expenses if e.type == ExpenseType.OPEX), Decimal('0.00'))

    @computed_field
    @property
    def utilization_pct(self) -> Decimal:
        if self.budget == 0:
            return Decimal('0.00')
        return (self.total_spent / self.budget) * Decimal('100.00')


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    table_name: str
    record_id: int
    action: str
    changed_by: Optional[str]
    changed_at: datetime
    before_data: Optional[dict]
    after_data: Optional[dict]
