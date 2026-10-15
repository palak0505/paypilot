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

ORDER_ID = open("last_order.txt").read().strip()
print("Capturing order:", ORDER_ID)

res = client.post(
    f"{BASE}/v2/checkout/orders/{ORDER_ID}/capture",
    headers={"Authorization": f"Bearer {token}",
             "Content-Type": "application/json"},
).json()

if res.get("status") != "COMPLETED":
    print("Capture did not complete:\n")
    print(json.dumps(res, indent=2))
    raise SystemExit(1)

print("Status:", res["status"])