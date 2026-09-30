from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditAction, AuditLog


def model_to_dict(instance: Any, fields: list[str]) -> dict:
    payload: dict[str, Any] = {}
    for field in fields:
        value = getattr(instance, field)
        payload[field] = value.value if hasattr(value, 'value') else value
    return payload


async def write_audit_log(
    session: AsyncSession,
    *,
    table_name: str,
    record_id: int,
    action: AuditAction,
    changed_by: Optional[str],
    before_data: Optional[dict],
    after_data: Optional[dict],
) -> None:
    session.add(
        AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            changed_by=changed_by,
            before_data=before_data,
            after_data=after_data,
        )
    )
