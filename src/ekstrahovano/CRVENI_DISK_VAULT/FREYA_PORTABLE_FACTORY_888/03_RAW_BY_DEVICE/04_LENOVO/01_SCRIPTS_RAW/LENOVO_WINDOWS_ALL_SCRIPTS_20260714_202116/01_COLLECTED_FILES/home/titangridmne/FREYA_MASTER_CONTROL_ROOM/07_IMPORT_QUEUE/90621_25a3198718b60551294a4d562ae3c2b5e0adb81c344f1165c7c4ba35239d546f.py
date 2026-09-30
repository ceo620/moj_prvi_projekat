from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.exceptions import ConflictError, NotFoundError
from app.schemas import RefreshRequest, TenantCreate, TenantRead, TokenPair, UserCreate, UserLogin, UserRead
from app.services.auth_service import AuthService
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/tenants", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(payload: TenantCreate, session: AsyncSession = Depends(get_session)):
    service = TenantService(session)
    try:
        return await service.create(payload)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    try:
        return await service.register(payload)
    except (ConflictError, NotFoundError) as e:
        status_code = 409 if isinstance(e, ConflictError) else 404
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    try:
        return await service.login(payload)
    except NotFoundError as e:
        raise HTTPException(status_code=401, detail="Invalid credentials") from e


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_session)):
    service = AuthService(session)
    try:
        return await service.refresh(payload)
    except NotFoundError as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from e
