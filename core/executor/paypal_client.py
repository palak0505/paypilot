import os, base64, json, httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv
from core.policy.models import Decision, Verdict

load_dotenv()


class PolicyViolation(Exception):
    """Raised when execution is attempted without an ALLOW decision."""


class PayPalExecutor:
    """The only component permitted to hold PayPal credentials."""

    def __init__(self):
        self.base = os.getenv("PAYPAL_BASE_URL")
        self._cid = os.getenv("PAYPAL_CLIENT_ID")
        self._secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self._token = None
        self._token_expires = datetime.min
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            transport=httpx.HTTPTransport(retries=3),
        )

    def _get_token(self) -> str:
        if self._token and datetime.utcnow() < self._token_expires:
            return self._token

        auth = base64.b64encode(f"{self._cid}:{self._secret}".encode()).decode()
        r = self.client.post(
            f"{self.base}/v1/oauth2/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
        )
        r.raise_for_status()
        data = r.json()
        self._token = data["access_token"]
        self._token_expires = datetime.utcnow() + timedelta(
            seconds=data.get("expires_in", 3600) - 60
        )
        return self._token

    def create_order(self, decision: Decision) -> dict:
        """Create a PayPal order. Requires an ALLOW decision."""
        if not isinstance(decision, Decision):
            raise PolicyViolation("A Decision object is required")
        if decision.verdict != Verdict.ALLOW:
            raise PolicyViolation(
                f"Cannot execute: verdict is {decision.verdict.value} — "
                f"{'; '.join(decision.reasons)}"
            )

        intent = decision.intent
        r = self.client.post(
            f"{self.base}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {self._get_token()}",
                     "Content-Type": "application/json"},
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": intent.currency,
                        "value": f"{intent.total:.2f}",
                    },
                    "description": intent.description[:127] or "PayPilot purchase",
                }],
                "payment_source": {"paypal": {
                    "experience_context": {
                        "return_url": "https://example.com/return",
                        "cancel_url": "https://example.com/cancel",
                    }
                }},
            },
        )
        order = r.json()
        if "id" not in order:
            raise RuntimeError(f"PayPal rejected the order:\n{json.dumps(order, indent=2)}")
        return order

    def capture_order(self, order_id: str) -> dict:
        r = self.client.post(
            f"{self.base}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {self._get_token()}",
                     "Content-Type": "application/json"},
        )
        return r.json()

    @staticmethod
    def approval_url(order: dict) -> str | None:
        for link in order.get("links", []):
            if link["rel"] == "payer-action":
                return link["href"]
        return None