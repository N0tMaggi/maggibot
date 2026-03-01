from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class TicketInactivityDecision:
    send_reminder: bool
    escalate: bool


def decide_inactivity_action(
    *,
    status: str,
    inactivity: datetime.timedelta,
    reminder_threshold: datetime.timedelta,
    escalation_threshold: datetime.timedelta,
) -> TicketInactivityDecision:
    if status != "Open":
        return TicketInactivityDecision(send_reminder=False, escalate=False)

    if inactivity >= escalation_threshold:
        return TicketInactivityDecision(send_reminder=False, escalate=True)

    if reminder_threshold < inactivity < escalation_threshold:
        return TicketInactivityDecision(send_reminder=True, escalate=False)

    return TicketInactivityDecision(send_reminder=False, escalate=False)
