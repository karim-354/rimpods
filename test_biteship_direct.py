"""Direct Biteship API test to diagnose the issue"""
import os
import requests
import json

# Load env
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

BITESHIP_KEY = os.getenv("BITESHIP_KEY")
BITESHIP_API = "https://api.biteship.com/v1"

ORIGIN_LAT = -6.259636
ORIGIN_LON = 106.906426
ORIGIN_POSTAL = "17411"

print(f"Biteship Key: {BITESHIP_KEY[:30]}...")
print(f"Testing Biteship rates API directly")
print("="*80)

# Test payload matching what server.py sends
payload = {
    "origin_latitude": ORIGIN_LAT,
    "origin_longitude": ORIGIN_LON,
    "origin_postal_code": int(ORIGIN_POSTAL),
    "destination_postal_code": 10110,
    "couriers": "grab,gojek,jne,jnt,sicepat,paxel,lalamove",
    "items": [
        {
            "name": "Live Coral Food",
            "value": 50000,
            "weight": 1000,
            "quantity": 1
        }
    ]
}

print("Payload:")
print(json.dumps(payload, indent=2))
print("\n" + "="*80)

headers = {
    "Authorization": f"Bearer {BITESHIP_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{BITESHIP_API}/rates/couriers",
    json=payload,
    headers=headers,
    timeout=20
)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print(f"\nResponse Body:")
print(json.dumps(response.json(), indent=2))
