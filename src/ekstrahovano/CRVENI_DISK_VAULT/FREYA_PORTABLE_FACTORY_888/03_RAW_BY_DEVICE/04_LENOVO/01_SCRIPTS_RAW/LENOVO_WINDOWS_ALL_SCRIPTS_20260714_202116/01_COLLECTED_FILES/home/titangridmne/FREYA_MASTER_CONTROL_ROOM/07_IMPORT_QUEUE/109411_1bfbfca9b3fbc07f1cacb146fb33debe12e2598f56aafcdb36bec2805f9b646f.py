from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models import Tenant, User, UserRole
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise unauthorized
        email = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not email or not tenant_id:
            raise unauthorized
    except Exception as exc:
        raise unauthorized from exc

    result = await session.exec(
        select(User).where(
            User.email == email,
            User.tenant_id == tenant_id,
            User.is_active == True,  # noqa: E712
        )
    )
    user = result.first()
    if not user:
        raise unauthorized
    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Tenant:
    tenant = await session.get(Tenant, current_user.tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant inactive or not found")
    return tenant


def require_roles(*allowed_roles: UserRole) -> Callable:
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return checker
