import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai import AuditLog

logger = logging.getLogger(__name__)


async def log_audit_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log critical user/system activity to audit_logs table."""
    try:
        # Sanitize details to ensure no credentials or secrets are logged
        clean_details = {}
        if details:
            for k, v in details.items():
                if any(secret in k.lower() for secret in ["password", "token", "secret", "key", "authorization"]):
                    clean_details[k] = "[REDACTED]"
                else:
                    clean_details[k] = v

        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=clean_details,
            created_at=datetime.now(timezone.utc)
        )
        db.add(audit_entry)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to record audit event for {action}: {e}")
