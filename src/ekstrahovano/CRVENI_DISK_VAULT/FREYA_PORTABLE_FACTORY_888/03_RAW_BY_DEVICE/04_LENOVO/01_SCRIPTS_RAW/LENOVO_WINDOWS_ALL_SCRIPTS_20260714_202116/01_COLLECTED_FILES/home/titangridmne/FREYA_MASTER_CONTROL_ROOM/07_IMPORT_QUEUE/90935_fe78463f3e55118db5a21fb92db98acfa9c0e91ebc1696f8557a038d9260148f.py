from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user, require_roles
from app.exceptions import NotFoundError
from app.models import ExpenseCategory, User, UserRole
from app.schemas import ExpenseCreate, ExpenseRead, ExpenseUpdate, Page
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO, UserRole.PM))])
async def create_expense(payload: ExpenseCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await ExpenseService(session).create(payload, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("", response_model=Page[ExpenseRead])
async def list_expenses(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    project_id: Optional[int] = Query(default=None),
    category: Optional[ExpenseCategory] = Query(default=None),
    currency: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await ExpenseService(session).list(actor=current_user, page=page, size=size, project_id=project_id, category=category, currency=currency)


@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(expense_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await ExpenseService(session).get(expense_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{expense_id}", response_model=ExpenseRead, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO, UserRole.PM))])
async def update_expense(expense_id: int, payload: ExpenseUpdate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        return await ExpenseService(session).update(expense_id, payload, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO))])
async def delete_expense(expense_id: int, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        await ExpenseService(session).delete(expense_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
