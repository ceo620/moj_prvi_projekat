from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user, require_roles
from app.exceptions import NotFoundError
from app.models import ProjectStatus, User, UserRole
from app.pdf import render_pdf_from_html
from app.reporting import build_report_context, templates
from app.schemas import Page, ProjectCreate, ProjectRead, ProjectReadDetailed, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO, UserRole.PM))])
async def create_project(payload: ProjectCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    return await ProjectService(session).create(payload, current_user)


@router.get("", response_model=Page[ProjectRead])
async def list_projects(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ProjectStatus] = Query(default=None, alias="status"),
    sponsor: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await ProjectService(session).list(actor=current_user, page=page, size=size, status_filter=status_filter, sponsor=sponsor, country=country, search=search)


@router.get("/{project_id}", response_model=ProjectReadDetailed)
async def get_project(project_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await ProjectService(session).get(project_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{project_id}", response_model=ProjectRead, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO, UserRole.PM))])
async def update_project(project_id: int, payload: ProjectUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await ProjectService(session).update(project_id, payload, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO))])
async def delete_project(project_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        await ProjectService(session).delete(project_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{project_id}/report", response_class=HTMLResponse)
async def project_report(project_id: int, request: Request, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        project = await ProjectService(session).get(project_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    context = build_report_context(project)
    context["request"] = request
    return templates.TemplateResponse(request=request, name="investment_memorandum.html", context=context)


@router.get("/{project_id}/report.pdf")
async def project_report_pdf(project_id: int, request: Request, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        project = await ProjectService(session).get(project_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    context = build_report_context(project)
    context["request"] = request
    html = templates.get_template("investment_memorandum.html").render(**context)
    pdf_bytes = render_pdf_from_html(html)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="project_{project_id}_memorandum.pdf"'})
