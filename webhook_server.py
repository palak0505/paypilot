import os, base64, json, httpx
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("PAYPAL_BASE_URL")
WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID")

app = FastAPI()
client = httpx.Client(timeout=30.0, follow_redirects=True,
                      transport=httpx.HTTPTransport(retries=3))


def get_token():
    auth = base64.b64encode(
        f"{os.getenv('PAYPAL_CLIENT_ID')}:{os.getenv('PAYPAL_CLIENT_SECRET')}".encode()
    ).decode()
    return client.post(
        f"{BASE}/v1/oauth2/token",
        headers={"Authorization": f"Basic {auth}"},
        data={"grant_type": "client_credentials"},
    ).json()["access_token"]


def verify(headers, body):
    """Ask PayPal whether this webhook is genuinely from them."""
    if not WEBHOOK_ID:
        print("  WEBHOOK_ID not set, skipping verification")
        return False

    res = client.post(
        f"{BASE}/v1/notifications/verify-webhook-signature",
        headers={"Authorization": f"Bearer {get_token()}",
                 "Content-Type": "application/json"},
        json={
            "auth_algo": headers.get("paypal-auth-algo"),
            "cert_url": headers.get("paypal-cert-url"),
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "webhook_id": WEBHOOK_ID,
            "webhook_event": body,
        },
    ).json()
    return res.get("verification_status") == "SUCCESS"


@app.get("/")
def health():
    return {"status": "alive"}


@app.post("/webhook")
async def webhook(request: Request):
    body = json.loads(await request.body())
    event = body.get("event_type")

    verified = verify(request.headers, body)
    mark = "VERIFIED" if verified else "UNVERIFIED"

    print(f"\n[{mark}] {event}")

    if not verified:
        print("  Rejected — not processing")
        return {"status": "rejected"}

    resource = body.get("resource", {})
    if event == "CHECKOUT.ORDER.APPROVED":
        print(f"  Order {resource.get('id')} approved by buyer")
    elif event == "PAYMENT.CAPTURE.COMPLETED":
        amt = resource.get("amount", {})
        print(f"  Captured {amt.get('value')} {amt.get('currency_code')}")

    return {"status": "ok"}