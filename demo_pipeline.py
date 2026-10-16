from core.policy.engine import PolicyEngine
from core.policy.models import PurchaseIntent
from core.executor.paypal_client import PayPalExecutor, PolicyViolation

engine = PolicyEngine()
executor = PayPalExecutor()

intents = [
    PurchaseIntent(merchant="acme-store", total=12.00, description="Coffee filters"),
    PurchaseIntent(merchant="sketchy-shop", total=499.00, description="Mystery bundle"),
]

for intent in intents:
    print(f"\n--- {intent.description} (${intent.total:.2f} at {intent.merchant})")
    decision = engine.evaluate(intent)
    print(f"Policy: {decision.verdict.value} — {decision.reasons[0]}")

    try:
        order = executor.create_order(decision)
        print(f"PayPal order created: {order['id']}")
        print(f"Approve at: {executor.approval_url(order)}")
    except PolicyViolation as e:
        print(f"Executor refused: {e}")