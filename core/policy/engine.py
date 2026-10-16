import yaml
from datetime import datetime, timedelta
from pathlib import Path
from .models import PurchaseIntent, Decision, Verdict


class PolicyEngine:
    """Deterministic. No LLM in this path, by design."""

    def __init__(self, rules_path: str | None = None, history: list | None = None):
        path = Path(rules_path or Path(__file__).parent / "rules.yaml")
        self.rules = yaml.safe_load(path.read_text())
        self.history: list[PurchaseIntent] = history or []

    def _spent_since(self, since: datetime) -> float:
        return sum(i.total for i in self.history if i.created_at >= since)

    def evaluate(self, intent: PurchaseIntent) -> Decision:
        reasons: list[str] = []
        triggered: list[str] = []
        now = datetime.utcnow()

        limits = self.rules.get("limits", {})
        merchants = self.rules.get("merchants", {})
        categories = self.rules.get("categories", {})

        # --- hard blocks ---
        allowed = merchants.get("allow", [])
        if allowed and intent.merchant not in allowed:
            reasons.append(f"Merchant '{intent.merchant}' is not on your allowlist")
            triggered.append("merchants.allow")

        if intent.category in categories.get("deny", []):
            reasons.append(f"Category '{intent.category}' is blocked")
            triggered.append("categories.deny")

        per_tx = limits.get("per_transaction")
        if per_tx is not None and intent.total > per_tx:
            reasons.append(
                f"${intent.total:.2f} exceeds your ${per_tx:.2f} per-transaction limit"
            )
            triggered.append("limits.per_transaction")

        daily = limits.get("daily")
        if daily is not None:
            spent = self._spent_since(now - timedelta(days=1))
            if spent + intent.total > daily:
                reasons.append(
                    f"Would bring today's spend to ${spent + intent.total:.2f}, "
                    f"over your ${daily:.2f} daily limit"
                )
                triggered.append("limits.daily")

        monthly = limits.get("monthly")
        if monthly is not None:
            spent = self._spent_since(now - timedelta(days=30))
            if spent + intent.total > monthly:
                reasons.append(
                    f"Would exceed your ${monthly:.2f} monthly limit"
                )
                triggered.append("limits.monthly")

        velocity = self.rules.get("velocity", {})
        max_hr = velocity.get("max_transactions_per_hour")
        if max_hr is not None:
            recent = [i for i in self.history
                      if i.created_at >= now - timedelta(hours=1)]
            if len(recent) >= max_hr:
                reasons.append(
                    f"Already made {len(recent)} purchases this hour (limit {max_hr})"
                )
                triggered.append("velocity.max_transactions_per_hour")

        if reasons:
            return Decision(Verdict.BLOCK, reasons, triggered, intent)

        # --- approval threshold ---
        threshold = self.rules.get("approval_required_above")
        if threshold is not None and intent.total > threshold:
            return Decision(
                Verdict.NEEDS_APPROVAL,
                [f"${intent.total:.2f} is above your ${threshold:.2f} "
                 f"auto-approve threshold"],
                ["approval_required_above"],
                intent,
            )

        return Decision(
            Verdict.ALLOW,
            [f"Within all limits for {intent.merchant}"],
            [],
            intent,
        )