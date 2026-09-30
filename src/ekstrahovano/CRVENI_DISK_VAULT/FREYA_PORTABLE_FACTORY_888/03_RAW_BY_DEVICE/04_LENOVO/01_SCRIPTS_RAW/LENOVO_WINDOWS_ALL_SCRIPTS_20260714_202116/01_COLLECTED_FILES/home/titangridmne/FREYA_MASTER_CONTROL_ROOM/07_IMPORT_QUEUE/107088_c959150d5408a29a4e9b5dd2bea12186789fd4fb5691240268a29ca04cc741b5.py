import json
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import AuditLog


def to_jsonable_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    data = {}
    for key, value in getattr(obj, "__dict__", {}).items():
        if not key.startswith("_"):
            data[key] = value
    return data


async def write_audit_log(
    session: AsyncSession,
    *,
    tenant_id: int,
    entity_name: str,
    entity_id: int,
    action: str,
    actor: str,
    before: Any = None,
    after: Any = None,
) -> None:
    log = AuditLog(
        tenant_id=tenant_id,
        entity_name=entity_name,
        entity_id=entity_id,
        action=action,
        actor=actor,
        before_json=json.dumps(to_jsonable_dict(before), default=str) if before else None,
        after_json=json.dumps(to_jsonable_dict(after), default=str) if after else None,
    )
    session.add(log)
