from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExpenseType(str, PyEnum):
    CAPEX = 'CAPEX'
    OPEX = 'OPEX'


class MilestoneStatus(str, PyEnum):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    DELAYED = 'DELAYED'


class AuditAction(str, PyEnum):
    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Project(TimestampMixin, Base):
    __tablename__ = 'project'
    __table_args__ = (CheckConstraint('budget > 0', name='ck_project_budget_positive'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    budget: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    expenses: Mapped[list['Expense']] = relationship(
        back_populates='project', cascade='all, delete-orphan', passive_deletes=True
    )
    milestones: Mapped[list['Milestone']] = relationship(
        back_populates='project', cascade='all, delete-orphan', passive_deletes=True
    )


class Expense(TimestampMixin, Base):
    __tablename__ = 'expense'
    __table_args__ = (CheckConstraint('amount > 0', name='ck_expense_amount_positive'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    type: Mapped[ExpenseType] = mapped_column(
        SAEnum(
            ExpenseType,
            name='expense_type_enum',
            native_enum=True,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    project_id: Mapped[int] = mapped_column(ForeignKey('project.id', ondelete='CASCADE'), nullable=False, index=True)

    project: Mapped['Project'] = relationship(back_populates='expenses')


class Milestone(TimestampMixin, Base):
    __tablename__ = 'milestone'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[MilestoneStatus] = mapped_column(
        SAEnum(
            MilestoneStatus,
            name='milestone_status_enum',
            native_enum=True,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
        default=MilestoneStatus.PENDING,
    )
    project_id: Mapped[int] = mapped_column(ForeignKey('project.id', ondelete='CASCADE'), nullable=False, index=True)

    project: Mapped['Project'] = relationship(back_populates='milestones')


class AuditLog(Base):
    __tablename__ = 'audit_log'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[AuditAction] = mapped_column(
        SAEnum(
            AuditAction,
            name='audit_action_enum',
            native_enum=True,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
    )
    changed_by: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    before_data: Mapped[Optional[dict]] = mapped_column(nullable=True)
    after_data: Mapped[Optional[dict]] = mapped_column(nullable=True)
