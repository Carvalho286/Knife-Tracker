import collections

# Fix para MutableSet (Python 3.11+)
if not hasattr(collections, "MutableSet"):
    from collections.abc import MutableSet
    collections.MutableSet = MutableSet

# Fix para MutableMapping (Python 3.11+)
if not hasattr(collections, "MutableMapping"):
    from collections.abc import MutableMapping
    collections.MutableMapping = MutableMapping

# Fix para MutableSequence (só por segurança)
if not hasattr(collections, "MutableSequence"):
    from collections.abc import MutableSequence
    collections.MutableSequence = MutableSequence
    
import time
import jwt
import httpx

TEAM_ID = "W97A2UZW7H"
KEY_ID = "Q9KK88WVNZ"
BUNDLE_ID = "com.knife-tracker-app"

with open("AuthKey_Q9KK88WVNZ.p8", "r") as f:
    PRIVATE_KEY = f.read()

def make_jwt():
    now = int(time.time())
    payload = {
        "iss": TEAM_ID,
        "iat": now
    }
    headers = {
        "alg": "ES256",
        "kid": KEY_ID
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="ES256", headers=headers)


async def send_apns_push(device_token: str, title: str, body: str):
    url = f"https://api.push.apple.com/3/device/{device_token}"

    headers = {
        "authorization": f"bearer {make_jwt()}",
        "apns-topic": BUNDLE_ID,
        "apns-push-type": "alert",
        "content-type": "application/json"
    }

    payload = {
        "aps": {
            "alert": {
                "title": title,
                "body": body
            },
            "sound": "default"
        }
    }

    async with httpx.AsyncClient(http2=True) as client:
        r = await client.post(url, json=payload, headers=headers)
        print("APNs Response:", r.status_code, r.text)
