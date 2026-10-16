import pytest
from core.policy.engine import PolicyEngine
from core.policy.models import PurchaseIntent, Verdict
from core.executor.paypal_client import PayPalExecutor, PolicyViolation


def test_blocked_intent_never_reaches_paypal():
    engine = PolicyEngine()
    decision = engine.evaluate(
        PurchaseIntent(merchant="sketchy-shop", total=500.0)
    )
    assert decision.verdict == Verdict.BLOCK

    with pytest.raises(PolicyViolation):
        PayPalExecutor().create_order(decision)


def test_needs_approval_cannot_execute_directly():
    engine = PolicyEngine()
    decision = engine.evaluate(
        PurchaseIntent(merchant="acme-store", total=30.0)
    )
    assert decision.verdict == Verdict.NEEDS_APPROVAL

    with pytest.raises(PolicyViolation):
        PayPalExecutor().create_order(decision)


def test_raw_dict_rejected():
    """You cannot fake a decision with a plain object."""
    with pytest.raises(PolicyViolation):
        PayPalExecutor().create_order({"verdict": "ALLOW"})