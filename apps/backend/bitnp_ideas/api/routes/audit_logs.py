from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bitnp_ideas.db.session import get_db_session
from bitnp_ideas.models.entities import AuditLog
from bitnp_ideas.models.enums import GlobalRole
from bitnp_ideas.schemas.common import AuditLogRead, CurrentUser, Page
from bitnp_ideas.security.rbac import require_roles
from bitnp_ideas.services.backend import normalized_limit, normalized_offset, total_for_statement

router = APIRouter()
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
SuperuserDep = Annotated[CurrentUser, Depends(require_roles(GlobalRole.SUPERUSER))]


def read_audit_log(log: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=log.id,
        actor_user_id=log.actor_user_id,
        actor_api_key_id=log.actor_api_key_id,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        before=log.before,
        after=log.after,
        metadata=log.metadata_,
        created_at=log.created_at,
    )


@router.get("", response_model=Page[AuditLogRead])
async def list_audit_logs(
    _: SuperuserDep,
    session: DbSessionDep,
    actor_user_id: str | None = None,
    actor_api_key_id: str | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
    offset: int = 0,
    limit: int = 50,
) -> Page[AuditLogRead]:
    if created_from and created_to and created_from > created_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="created_from must be before or equal to created_to.",
        )

    statement = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if actor_user_id:
        statement = statement.where(AuditLog.actor_user_id == actor_user_id)
    if actor_api_key_id:
        statement = statement.where(AuditLog.actor_api_key_id == actor_api_key_id)
    if action:
        statement = statement.where(AuditLog.action == action)
    if entity_type:
        statement = statement.where(AuditLog.entity_type == entity_type)
    if entity_id:
        statement = statement.where(AuditLog.entity_id == entity_id)
    if created_from:
        statement = statement.where(
            AuditLog.created_at >= datetime.combine(created_from, time.min, tzinfo=UTC)
        )
    if created_to:
        to_exclusive = datetime.combine(created_to + timedelta(days=1), time.min, tzinfo=UTC)
        statement = statement.where(AuditLog.created_at < to_exclusive)
    total = await total_for_statement(session, statement)
    result = await session.scalars(
        statement.offset(normalized_offset(offset)).limit(normalized_limit(limit))
    )
    return Page(data=[read_audit_log(log) for log in result], total=total)
