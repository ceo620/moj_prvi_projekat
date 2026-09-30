from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user, require_roles
from app.exceptions import NotFoundError
from app.models import MilestoneStatus, User, UserRole
from app.schemas import MilestoneCreate, MilestoneRead, MilestoneUpdate, Page
from app.services.milestone_service import MilestoneService

router = APIRouter(prefix="/milestones", tags=["Milestones"])


@router.post("", response_model=MilestoneRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO, UserRole.PM))])
async def create_milestone(payload: MilestoneCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await MilestoneService(session).create(payload, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("", response_model=Page[MilestoneRead])
async def list_milestones(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    project_id: Optional[int] = Query(default=None),
    status_filter: Optional[MilestoneStatus] = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await MilestoneService(session).list(actor=current_user, page=page, size=size, project_id=project_id, status_filter=status_filter)


@router.get("/{milestone_id}", response_model=MilestoneRead)
async def get_milestone(milestone_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await MilestoneService(session).get(milestone_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{milestone_id}", response_model=MilestoneRead, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO, UserRole.PM))])
async def update_milestone(milestone_id: int, payload: MilestoneUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await MilestoneService(session).update(milestone_id, payload, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO))])
async def delete_milestone(milestone_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        await MilestoneService(session).delete(milestone_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
