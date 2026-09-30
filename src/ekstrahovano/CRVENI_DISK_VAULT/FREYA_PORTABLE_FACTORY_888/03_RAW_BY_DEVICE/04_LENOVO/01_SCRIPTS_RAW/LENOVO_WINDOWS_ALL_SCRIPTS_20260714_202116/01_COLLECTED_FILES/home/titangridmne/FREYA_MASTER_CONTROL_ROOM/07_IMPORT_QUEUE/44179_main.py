from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import AuditLog, AuditAction, Expense, Milestone, Project
from app.schemas import (
    AuditLogRead,
    ExpenseCreate,
    ExpenseRead,
    ExpenseUpdate,
    MilestoneCreate,
    MilestoneRead,
    MilestoneUpdate,
    ProjectCreate,
    ProjectDetail,
    ProjectRead,
    ProjectUpdate,
)
from app.services.audit_service import model_to_dict, write_audit_log
from app.services.export_service import build_project_workbook, forensic_findings

app = FastAPI(title='CAPEX/OPEX Master System v3', version='3.0.0')


def get_actor(x_actor: str | None = Header(default=None)) -> str | None:
    return x_actor


async def get_project_or_404(session: AsyncSession, project_id: int) -> Project:
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.expenses), selectinload(Project.milestones))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    return project


@app.get('/health')
async def health() -> dict:
    return {'status': 'ok'}


@app.post('/projects', response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    project = Project(**payload.model_dump())
    session.add(project)
    await session.flush()
    await write_audit_log(
        session,
        table_name='project',
        record_id=project.id,
        action=AuditAction.INSERT,
        changed_by=actor,
        before_data=None,
        after_data=model_to_dict(project, ['name', 'description', 'start_date', 'budget']),
    )
    await session.commit()
    await session.refresh(project)
    return project


@app.get('/projects', response_model=list[ProjectRead])
async def list_projects(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    result = await session.execute(select(Project).offset(skip).limit(limit).order_by(Project.id.desc()))
    return list(result.scalars().all())


@app.get('/projects/{project_id}', response_model=ProjectDetail)
async def get_project(project_id: int, session: AsyncSession = Depends(get_session)):
    return await get_project_or_404(session, project_id)


@app.put('/projects/{project_id}', response_model=ProjectRead)
async def update_project(project_id: int, payload: ProjectUpdate, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    project = await get_project_or_404(session, project_id)
    before = model_to_dict(project, ['name', 'description', 'start_date', 'budget'])
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    await session.flush()
    after = model_to_dict(project, ['name', 'description', 'start_date', 'budget'])
    await write_audit_log(session, table_name='project', record_id=project.id, action=AuditAction.UPDATE, changed_by=actor, before_data=before, after_data=after)
    await session.commit()
    await session.refresh(project)
    return project


@app.delete('/projects/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    project = await get_project_or_404(session, project_id)
    before = model_to_dict(project, ['name', 'description', 'start_date', 'budget'])
    await write_audit_log(session, table_name='project', record_id=project.id, action=AuditAction.DELETE, changed_by=actor, before_data=before, after_data=None)
    await session.delete(project)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post('/expenses', response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(payload: ExpenseCreate, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    _ = await get_project_or_404(session, payload.project_id)
    expense = Expense(**payload.model_dump())
    session.add(expense)
    await session.flush()
    await write_audit_log(session, table_name='expense', record_id=expense.id, action=AuditAction.INSERT, changed_by=actor, before_data=None, after_data=model_to_dict(expense, ['description', 'amount', 'type', 'date', 'project_id']))
    await session.commit()
    await session.refresh(expense)
    return expense


@app.get('/expenses', response_model=list[ExpenseRead])
async def list_expenses(
    session: AsyncSession = Depends(get_session),
    project_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    stmt = select(Expense)
    if project_id is not None:
        stmt = stmt.where(Expense.project_id == project_id)
    result = await session.execute(stmt.order_by(Expense.date.desc()).offset(skip).limit(limit))
    return list(result.scalars().all())


@app.put('/expenses/{expense_id}', response_model=ExpenseRead)
async def update_expense(expense_id: int, payload: ExpenseUpdate, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    result = await session.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail='Expense not found')
    before = model_to_dict(expense, ['description', 'amount', 'type', 'date', 'project_id'])
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)
    await session.flush()
    after = model_to_dict(expense, ['description', 'amount', 'type', 'date', 'project_id'])
    await write_audit_log(session, table_name='expense', record_id=expense.id, action=AuditAction.UPDATE, changed_by=actor, before_data=before, after_data=after)
    await session.commit()
    await session.refresh(expense)
    return expense


@app.delete('/expenses/{expense_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    result = await session.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail='Expense not found')
    before = model_to_dict(expense, ['description', 'amount', 'type', 'date', 'project_id'])
    await write_audit_log(session, table_name='expense', record_id=expense.id, action=AuditAction.DELETE, changed_by=actor, before_data=before, after_data=None)
    await session.delete(expense)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post('/milestones', response_model=MilestoneRead, status_code=status.HTTP_201_CREATED)
async def create_milestone(payload: MilestoneCreate, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    _ = await get_project_or_404(session, payload.project_id)
    milestone = Milestone(**payload.model_dump())
    session.add(milestone)
    await session.flush()
    await write_audit_log(session, table_name='milestone', record_id=milestone.id, action=AuditAction.INSERT, changed_by=actor, before_data=None, after_data=model_to_dict(milestone, ['name', 'due_date', 'status', 'project_id']))
    await session.commit()
    await session.refresh(milestone)
    return milestone


@app.get('/milestones', response_model=list[MilestoneRead])
async def list_milestones(
    session: AsyncSession = Depends(get_session),
    project_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    stmt = select(Milestone)
    if project_id is not None:
        stmt = stmt.where(Milestone.project_id == project_id)
    result = await session.execute(stmt.order_by(Milestone.due_date.asc()).offset(skip).limit(limit))
    return list(result.scalars().all())


@app.put('/milestones/{milestone_id}', response_model=MilestoneRead)
async def update_milestone(milestone_id: int, payload: MilestoneUpdate, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    result = await session.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail='Milestone not found')
    before = model_to_dict(milestone, ['name', 'due_date', 'status', 'project_id'])
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(milestone, key, value)
    await session.flush()
    after = model_to_dict(milestone, ['name', 'due_date', 'status', 'project_id'])
    await write_audit_log(session, table_name='milestone', record_id=milestone.id, action=AuditAction.UPDATE, changed_by=actor, before_data=before, after_data=after)
    await session.commit()
    await session.refresh(milestone)
    return milestone


@app.delete('/milestones/{milestone_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(milestone_id: int, session: AsyncSession = Depends(get_session), actor: str | None = Depends(get_actor)):
    result = await session.execute(select(Milestone).where(Milestone.id == milestone_id))
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail='Milestone not found')
    before = model_to_dict(milestone, ['name', 'due_date', 'status', 'project_id'])
    await write_audit_log(session, table_name='milestone', record_id=milestone.id, action=AuditAction.DELETE, changed_by=actor, before_data=before, after_data=None)
    await session.delete(milestone)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get('/projects/{project_id}/forensic')
async def project_forensic(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await get_project_or_404(session, project_id)
    findings = forensic_findings(project)
    return {
        'project_id': project.id,
        'project_name': project.name,
        'total_checks': len(findings),
        'fail_count': sum(1 for x in findings if x['status'] == 'FAIL'),
        'critical_fail_count': sum(1 for x in findings if x['status'] == 'FAIL' and x['severity'] == 'CRITICAL'),
        'checks': findings,
    }


@app.get('/projects/{project_id}/export/excel')
async def export_excel(project_id: int, session: AsyncSession = Depends(get_session)):
    project = await get_project_or_404(session, project_id)
    workbook = build_project_workbook(project)
    filename = f'Project_Export_{project.name.replace(" ", "_")}.xlsx'
    return StreamingResponse(
        workbook,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@app.get('/audit-logs', response_model=list[AuditLogRead])
async def list_audit_logs(
    session: AsyncSession = Depends(get_session),
    table_name: str | None = Query(default=None),
    record_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    stmt = select(AuditLog)
    if table_name:
        stmt = stmt.where(AuditLog.table_name == table_name)
    if record_id is not None:
        stmt = stmt.where(AuditLog.record_id == record_id)
    result = await session.execute(stmt.order_by(AuditLog.changed_at.desc()).offset(skip).limit(limit))
    return list(result.scalars().all())
