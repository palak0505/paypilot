import os, base64, httpx
from dotenv import load_dotenv

load_dotenv()
CID = os.getenv("PAYPAL_CLIENT_ID")
SEC = os.getenv("PAYPAL_CLIENT_SECRET")
BASE = os.getenv("PAYPAL_BASE_URL")

auth = base64.b64encode(f"{CID}:{SEC}".encode()).decode()

r = httpx.post(
    f"{BASE}/v1/oauth2/token",
    headers={"Authorization": f"Basic {auth}"},
    data={"grant_type": "client_credentials"},
)
r.raise_for_status()
print("Connected. Token starts with:", r.json()["access_token"][:20], "...")