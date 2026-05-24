"""AlertHook: integrates alert policy evaluation into the daemon cycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.alert_policy import AlertDecision, AlertPolicy, evaluate_policy
from depwatch.notifier import NotifierBackend
from depwatch.reporter import Report


@dataclass
class AlertHookResult:
    decision: AlertDecision
    notification_sent: bool


@dataclass
class AlertHook:
    """Evaluates the alert policy and dispatches notifications when warranted."""
    policy: AlertPolicy
    notifiers: List[NotifierBackend] = field(default_factory=list)
    _decisions: List[AlertDecision] = field(default_factory=list, init=False, repr=False)

    def after_cycle(self, report: Report) -> AlertHookResult:
        decision = evaluate_policy(report, self.policy)
        self._decisions.append(decision)
        sent = False
        if decision.should_alert:
            for notifier in self.notifiers:
                notifier.send(report)
            sent = bool(self.notifiers)
        return AlertHookResult(decision=decision, notification_sent=sent)

    @property
    def total_alerts_sent(self) -> int:
        return sum(1 for d in self._decisions if d.should_alert)

    @property
    def total_suppressed(self) -> int:
        return sum(1 for d in self._decisions if not d.should_alert)

    def summary(self) -> str:
        return (
            f"AlertHook: {self.total_alerts_sent} alert(s) sent, "
            f"{self.total_suppressed} suppressed"
        )
