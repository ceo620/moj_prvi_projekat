from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Numeric, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    ADMIN = "admin"
    CFO = "cfo"
    PM = "pm"
    VIEWER = "viewer"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MilestoneStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class ExpenseCategory(str, Enum):
    LAND = "land"
    CIVIL_WORKS = "civil_works"
    MACHINERY = "machinery"
    ENGINEERING = "engineering"
    UTILITIES = "utilities"
    LABOR = "labor"
    PERMITS = "permits"
    FINANCING = "financing"
    OTHER = "other"


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=100)
    name: str = Field(max_length=200)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    users: list["User"] = Relationship(back_populates="tenant")
    projects: list["Project"] = Relationship(back_populates="tenant")


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    email: str = Field(index=True, max_length=255)
    full_name: str = Field(max_length=150)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.VIEWER, index=True)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    tenant: Optional["Tenant"] = Relationship(back_populates="users")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_jti: str = Field(default_factory=lambda: str(uuid4()), unique=True, index=True, max_length=64)
    hashed_token: str = Field(max_length=255)
    is_revoked: bool = Field(default=False, index=True)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    user: Optional["User"] = Relationship(back_populates="refresh_tokens")


class ProjectBase(SQLModel):
    name: str = Field(max_length=150, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    sponsor: Optional[str] = Field(default=None, max_length=150)
    sector: Optional[str] = Field(default=None, max_length=100)
    country: str = Field(default="Montenegro", max_length=100)
    currency: str = Field(default="EUR", max_length=10)
    budget: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(18, 2), nullable=False, default=Decimal("0.00")))
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT, index=True)


class Project(ProjectBase, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    tenant: Optional["Tenant"] = Relationship(back_populates="projects")
    expenses: list["Expense"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    milestones: list["Milestone"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class Expense(SQLModel, table=True):
    __tablename__ = "expenses"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    category: ExpenseCategory = Field(index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    amount: Decimal = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    expense_date: date
    currency: str = Field(default="EUR", max_length=10)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    project: Optional["Project"] = Relationship(back_populates="expenses")


class Milestone(SQLModel, table=True):
    __tablename__ = "milestones"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    title: str = Field(max_length=150, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    due_date: date
    status: MilestoneStatus = Field(default=MilestoneStatus.PLANNED, index=True)
    completion_percent: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(5, 2), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    project: Optional["Project"] = Relationship(back_populates="milestones")


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(index=True)
    entity_name: str = Field(max_length=100, index=True)
    entity_id: int = Field(index=True)
    action: str = Field(max_length=20, index=True)
    actor: str = Field(max_length=255, index=True)
    before_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    after_json: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
