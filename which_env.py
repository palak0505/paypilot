import os, base64, httpx
from dotenv import load_dotenv
load_dotenv()

auth = base64.b64encode(
    f"{os.getenv('PAYPAL_CLIENT_ID')}:{os.getenv('PAYPAL_CLIENT_SECRET')}".encode()
).decode()

for name, url in [
    ("SANDBOX", "https://api-m.sandbox.paypal.com"),
    ("LIVE",    "https://api-m.paypal.com"),
]:
    try:
        r = httpx.post(
            f"{url}/v1/oauth2/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
        )
        print(f"{name}: {r.status_code}")
    except Exception as e:
        print(f"{name}: error {e}")