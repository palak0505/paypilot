from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"


@dataclass
class PurchaseIntent:
    """What the agent proposes. It cannot execute this itself."""
    merchant: str
    total: float
    currency: str = "USD"
    category: str = "general"
    description: str = ""
    rationale: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Decision:
    verdict: Verdict
    reasons: list[str]
    triggered_rules: list[str]
    intent: PurchaseIntent

    @property
    def is_executable(self) -> bool:
        return self.verdict == Verdict.ALLOW