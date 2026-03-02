from __future__ import annotations

import datetime
from dataclasses import dataclass

import discord


@dataclass(frozen=True)
class AuditActor:
    user: discord.abc.User | None
    reason: str | None


def _matches_target(entry: discord.AuditLogEntry, target_id: int | None) -> bool:
    if target_id is None:
        return True
    target = getattr(entry, "target", None)
    return bool(target and getattr(target, "id", None) == target_id)


async def find_audit_actor(
    *,
    guild: discord.Guild,
    action: discord.AuditLogAction,
    target_id: int | None = None,
    max_entries: int = 6,
    max_age_seconds: int = 30,
) -> AuditActor:
    """Best-effort audit log lookup.

    Returns the most recent matching audit log entry (actor + reason).
    """

    cutoff = discord.utils.utcnow() - datetime.timedelta(seconds=max_age_seconds)

    try:
        async for entry in guild.audit_logs(limit=max_entries, action=action):
            created_at = getattr(entry, "created_at", None)
            if created_at and created_at < cutoff:
                break
            if not _matches_target(entry, target_id):
                continue
            return AuditActor(user=getattr(entry, "user", None), reason=getattr(entry, "reason", None))
    except Exception:
        return AuditActor(user=None, reason=None)

    return AuditActor(user=None, reason=None)
