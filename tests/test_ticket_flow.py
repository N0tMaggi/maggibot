import datetime

from utils.ticket_flow import decide_inactivity_action


def test_no_action_when_not_open():
    decision = decide_inactivity_action(
        status="Closed",
        inactivity=datetime.timedelta(hours=10),
        reminder_threshold=datetime.timedelta(hours=1),
        escalation_threshold=datetime.timedelta(hours=2),
    )
    assert decision.send_reminder is False
    assert decision.escalate is False


def test_reminder_window():
    decision = decide_inactivity_action(
        status="Open",
        inactivity=datetime.timedelta(hours=1, minutes=1),
        reminder_threshold=datetime.timedelta(hours=1),
        escalation_threshold=datetime.timedelta(hours=2),
    )
    assert decision.send_reminder is True
    assert decision.escalate is False


def test_escalation_threshold():
    decision = decide_inactivity_action(
        status="Open",
        inactivity=datetime.timedelta(hours=2),
        reminder_threshold=datetime.timedelta(hours=1),
        escalation_threshold=datetime.timedelta(hours=2),
    )
    assert decision.send_reminder is False
    assert decision.escalate is True


def test_before_reminder_threshold():
    decision = decide_inactivity_action(
        status="Open",
        inactivity=datetime.timedelta(minutes=30),
        reminder_threshold=datetime.timedelta(hours=1),
        escalation_threshold=datetime.timedelta(hours=2),
    )
    assert decision.send_reminder is False
    assert decision.escalate is False
