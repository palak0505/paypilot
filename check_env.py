import os
from dotenv import load_dotenv
load_dotenv()

for key in ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "PAYPAL_BASE_URL"]:
    v = os.getenv(key)
    if v is None:
        print(f"{key}: MISSING")
    else:
        print(f"{key}: length={len(v)} start={v[:6]!r} end={v[-4:]!r}")