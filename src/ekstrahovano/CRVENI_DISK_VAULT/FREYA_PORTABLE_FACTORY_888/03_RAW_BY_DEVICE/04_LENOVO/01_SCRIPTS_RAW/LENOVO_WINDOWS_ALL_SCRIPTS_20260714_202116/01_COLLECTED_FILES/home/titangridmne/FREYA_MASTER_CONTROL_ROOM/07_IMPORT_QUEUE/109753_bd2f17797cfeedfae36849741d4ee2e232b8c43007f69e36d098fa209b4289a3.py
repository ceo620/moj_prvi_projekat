from fastapi import APIRouter, Depends, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user, require_roles
from app.models import AuditLog, User, UserRole
from app.pagination import paginate
from app.schemas import AuditLogRead, Page

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", response_model=Page[AuditLogRead], dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.CFO))])
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id).order_by(AuditLog.id.desc())
    return await paginate(session, stmt, page, size)
