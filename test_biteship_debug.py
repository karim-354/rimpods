"""Debug Biteship rates API call"""
import requests
import json

BACKEND_URL = "https://api-frontend-base.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

payload = {
    "items": [
        {
            "product_id": "coral-food-1",
            "quantity": 1,
            "name": "Live Coral Food",
            "price": 50000
        }
    ],
    "postalCode": "10110"
}

print("Testing shipping rates with payload:")
print(json.dumps(payload, indent=2))
print("\n" + "="*80)

response = requests.post(f"{API_BASE}/shipping/rates", json=payload, timeout=20)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

# Also test with latitude/longitude
print("\n" + "="*80)
print("Testing with lat/lon:")
payload_with_coords = {
    "items": [
        {
            "product_id": "coral-food-1",
            "quantity": 1,
            "name": "Live Coral Food",
            "price": 50000
        }
    ],
    "postalCode": "10110",
    "latitude": "-6.1751",
    "longitude": "106.8650"
}
print(json.dumps(payload_with_coords, indent=2))
response2 = requests.post(f"{API_BASE}/shipping/rates", json=payload_with_coords, timeout=20)
print(f"Status Code: {response2.status_code}")
print(f"Response: {response2.text}")
