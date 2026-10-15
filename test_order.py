import os, base64, json, httpx
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("PAYPAL_BASE_URL")
auth = base64.b64encode(
    f"{os.getenv('PAYPAL_CLIENT_ID')}:{os.getenv('PAYPAL_CLIENT_SECRET')}".encode()
).decode()

client = httpx.Client(timeout=30.0, transport=httpx.HTTPTransport(retries=3))

token = client.post(
    f"{BASE}/v1/oauth2/token",
    headers={"Authorization": f"Basic {auth}"},
    data={"grant_type": "client_credentials"},
).json()["access_token"]

order = client.post(
    f"{BASE}/v2/checkout/orders",
    headers={"Authorization": f"Bearer {token}",
             "Content-Type": "application/json"},
    json={
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "USD", "value": "42.00"},
            "description": "PayPilot test purchase",
        }],
        "payment_source": {"paypal": {
            "experience_context": {
                "return_url": "https://example.com/return",
                "cancel_url": "https://example.com/cancel",
            }
        }},
    },
).json()

if "id" not in order:
    print("PayPal rejected the order:\n")
    print(json.dumps(order, indent=2))
    raise SystemExit(1)

with open("last_order.txt", "w") as f:
    f.write(order["id"])

print("Order ID:", order["id"], "(saved to last_order.txt)")
for link in order["links"]:
    if link["rel"] == "payer-action":
        print("\nOpen this URL in an incognito window:\n")
        print(link["href"])