import os, base64, httpx
from dotenv import load_dotenv

load_dotenv()
BASE = os.getenv("PAYPAL_BASE_URL")
auth = base64.b64encode(
    f"{os.getenv('PAYPAL_CLIENT_ID')}:{os.getenv('PAYPAL_CLIENT_SECRET')}".encode()
).decode()

client = httpx.Client(timeout=30.0, transport=httpx.HTTPTransport(retries=3))
r = client.post(
    f"{BASE}/v1/oauth2/token",
    headers={"Authorization": f"Basic {auth}"},
    data={"grant_type": "client_credentials"},
)

print("Status:", r.status_code)
print("Content-Type:", r.headers.get("content-type"))
print("Length:", len(r.content))
print("Body (first 400 chars):")
print(r.text[:400])