"""Test Midtrans with a manually created order"""
import os
import requests
import json
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid

# Load env
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "test_database")
BACKEND_URL = "https://api-frontend-base.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Connect to MongoDB and create a test order
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Create a test order directly in the database
order_id = str(uuid.uuid4())
order_number = f"RMP{datetime.now(timezone.utc).strftime('%y%m%d')}{uuid.uuid4().hex[:5].upper()}"

test_order = {
    "_id": order_id,
    "id": order_id,
    "order_number": order_number,
    "status": "pending",
    "items": [
        {
            "product_id": "test-coral-1",
            "name": "Live Coral Food Premium",
            "price": 89999,
            "quantity": 2,
            "line_total": 179998
        }
    ],
    "contact": {
        "name": "Budi Santoso",
        "phone": "6281234567890",
        "email": "budi.santoso@example.com",
        "address": "Jl. Sudirman No. 123",
        "city": "Jakarta Pusat",
        "kecamatan": "Tanah Abang",
        "postalCode": "10110"
    },
    "subtotal": 179998,
    "discount": 0,
    "shipping": 15000,
    "total": 194998,
    "payment_channel": "midtrans",
    "shipping_courier": "jne_reg",
    "created_at": datetime.now(timezone.utc).isoformat()
}

print("Creating test order in database...")
print(f"Order ID: {order_id}")
print(f"Order Number: {order_number}")
print(f"Total: Rp{test_order['total']:,}")

try:
    db.orders.insert_one(test_order)
    print("✅ Order created successfully")
except Exception as e:
    print(f"❌ Failed to create order: {e}")
    exit(1)

print("\n" + "="*80)
print("Testing Midtrans snap-token endpoint...")
print("="*80)

payload = {"order_id": order_id}
response = requests.post(f"{API_BASE}/payment/midtrans/snap-token", json=payload, timeout=20)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print("✅ Midtrans snap-token created successfully!")
    print(f"Token: {data.get('token', 'N/A')[:50]}...")
    print(f"Redirect URL: {data.get('redirect_url', 'N/A')}")
else:
    print(f"❌ Failed: {response.text}")

# Cleanup
print("\n" + "="*80)
print("Cleaning up test order...")
db.orders.delete_one({"_id": order_id})
print("✅ Test order deleted")
