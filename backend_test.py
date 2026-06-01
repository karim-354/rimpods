"""
Rimpods E-commerce Backend API Test Suite
Pre-deployment verification with LIVE keys (Midtrans production, Biteship live)
"""
import os
import requests
import json

# Get backend URL from environment (same as frontend uses)
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://api-frontend-base.preview.emergentagent.com").rstrip("/")
API_BASE = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE}")
print("=" * 80)

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(name, passed, details=""):
    """Log test result"""
    if passed:
        test_results["passed"].append(name)
        print(f"✅ {name}")
    else:
        test_results["failed"].append({"name": name, "details": details})
        print(f"❌ {name}")
        if details:
            print(f"   Details: {details}")

def log_warning(name, details):
    """Log warning"""
    test_results["warnings"].append({"name": name, "details": details})
    print(f"⚠️  {name}: {details}")

# ==========================================
# 1. Customer Lookup (Retention Engine)
# ==========================================
print("\n1. Testing Customer Lookup (Retention)")
print("-" * 80)
try:
    response = requests.get(f"{API_BASE}/customer/lookup", params={"phone": "08123456789"}, timeout=20)
    if response.status_code == 200:
        data = response.json()
        log_test("Customer lookup endpoint", True, f"Status: {response.status_code}, Found: {data.get('found', False)}")
        if not data.get("found"):
            print("   Note: No previous orders for this phone (expected for new customer)")
    else:
        log_test("Customer lookup endpoint", False, f"Expected 200, got {response.status_code}: {response.text}")
except Exception as e:
    log_test("Customer lookup endpoint", False, f"Exception: {str(e)}")

# ==========================================
# 2. Shipping Search Area (Biteship LIVE)
# ==========================================
print("\n2. Testing Shipping Search Area (Biteship LIVE)")
print("-" * 80)
try:
    response = requests.get(f"{API_BASE}/shipping/search-area", params={"query": "Jakarta"}, timeout=20)
    if response.status_code == 200:
        data = response.json()
        areas = data.get("areas", [])
        log_test("Shipping search-area endpoint", True, f"Status: {response.status_code}, Areas found: {len(areas)}")
        if len(areas) > 0:
            print(f"   Sample area: {areas[0].get('name', 'N/A')}")
        else:
            log_warning("Shipping search-area", "No areas returned (Biteship may have issues)")
    else:
        log_test("Shipping search-area endpoint", False, f"Expected 200, got {response.status_code}: {response.text}")
except Exception as e:
    log_test("Shipping search-area endpoint", False, f"Exception: {str(e)}")

# ==========================================
# 3. Shipping Rates (Biteship LIVE)
# ==========================================
print("\n3. Testing Shipping Rates (Biteship LIVE)")
print("-" * 80)
try:
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
    response = requests.post(f"{API_BASE}/shipping/rates", json=payload, timeout=20)
    if response.status_code == 200:
        data = response.json()
        rates = data.get("rates", [])
        log_test("Shipping rates endpoint", True, f"Status: {response.status_code}, Rates found: {len(rates)}")
        if len(rates) > 0:
            print(f"   Sample rate: {rates[0].get('courier', 'N/A')} - Rp{rates[0].get('cost', 0):,}")
        else:
            log_warning("Shipping rates", "No rates returned (Biteship may have issues)")
    else:
        log_test("Shipping rates endpoint", False, f"Expected 200, got {response.status_code}: {response.text}")
except Exception as e:
    log_test("Shipping rates endpoint", False, f"Exception: {str(e)}")

# ==========================================
# 4. Create Order
# ==========================================
print("\n4. Testing Create Order")
print("-" * 80)
created_order_id = None
try:
    # First get shipping rates to get a valid courier
    rates_payload = {
        "items": [
            {
                "product_id": "coral-food-1",
                "quantity": 2,
                "name": "Live Coral Food Premium",
                "price": 89999
            }
        ],
        "postalCode": "10110"
    }
    rates_response = requests.post(f"{API_BASE}/shipping/rates", json=rates_payload, timeout=20)
    
    shipping_courier = "jne_reg"  # default
    if rates_response.status_code == 200:
        rates = rates_response.json().get("rates", [])
        if rates:
            shipping_courier = rates[0]["id"]
    
    order_payload = {
        "items": [
            {
                "product_id": "coral-food-1",
                "quantity": 2,
                "name": "Live Coral Food Premium",
                "price": 89999
            }
        ],
        "contact": {
            "name": "Budi Santoso",
            "phone": "081234567890",
            "email": "budi.santoso@example.com",
            "address": "Jl. Sudirman No. 123",
            "city": "Jakarta Pusat",
            "kecamatan": "Tanah Abang",
            "postalCode": "10110"
        },
        "payment_channel": "midtrans",
        "shipping_courier": shipping_courier
    }
    
    response = requests.post(f"{API_BASE}/orders", json=order_payload, timeout=20)
    if response.status_code == 200:
        data = response.json()
        created_order_id = data.get("id")
        order_number = data.get("order_number", "N/A")
        total = data.get("total", 0)
        log_test("Create order endpoint", True, f"Status: {response.status_code}, Order: {order_number}, Total: Rp{total:,}")
        print(f"   Order ID: {created_order_id}")
    else:
        log_test("Create order endpoint", False, f"Expected 200, got {response.status_code}: {response.text}")
except Exception as e:
    log_test("Create order endpoint", False, f"Exception: {str(e)}")

# ==========================================
# 5. Midtrans Snap Token (LIVE - SAFE, no charge)
# ==========================================
print("\n5. Testing Midtrans Snap Token (LIVE - token creation is SAFE)")
print("-" * 80)
if created_order_id:
    try:
        payload = {"order_id": created_order_id}
        response = requests.post(f"{API_BASE}/payment/midtrans/snap-token", json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", "")
            redirect_url = data.get("redirect_url", "")
            log_test("Midtrans snap-token endpoint", True, f"Status: {response.status_code}, Token received: {len(token) > 0}")
            if redirect_url:
                print(f"   Redirect URL: {redirect_url[:60]}...")
        else:
            log_test("Midtrans snap-token endpoint", False, f"Expected 200, got {response.status_code}: {response.text}")
    except Exception as e:
        log_test("Midtrans snap-token endpoint", False, f"Exception: {str(e)}")
else:
    log_test("Midtrans snap-token endpoint", False, "Skipped - no order created in previous step")

# ==========================================
# 6. Auth Router - Verify Registered & Protected
# ==========================================
print("\n6. Testing Auth Router (Google OAuth)")
print("-" * 80)
try:
    response = requests.get(f"{API_BASE}/auth/me", timeout=20)
    if response.status_code == 401:
        log_test("Auth /me endpoint (protected)", True, f"Correctly returns 401 (unauthenticated)")
    elif response.status_code == 404:
        log_test("Auth /me endpoint (protected)", False, "Returns 404 - auth router may not be registered!")
    else:
        log_test("Auth /me endpoint (protected)", False, f"Expected 401, got {response.status_code}: {response.text}")
except Exception as e:
    log_test("Auth /me endpoint (protected)", False, f"Exception: {str(e)}")

# ==========================================
# 7. Admin Router - Verify Registered & Protected
# ==========================================
print("\n7. Testing Admin Router (Order Monitoring)")
print("-" * 80)

# Test /api/admin/stats
try:
    response = requests.get(f"{API_BASE}/admin/stats", timeout=20)
    if response.status_code == 401:
        log_test("Admin /stats endpoint (protected)", True, f"Correctly returns 401 (unauthenticated)")
    elif response.status_code == 404:
        log_test("Admin /stats endpoint (protected)", False, "Returns 404 - admin router may not be registered!")
    else:
        log_test("Admin /stats endpoint (protected)", False, f"Expected 401, got {response.status_code}: {response.text}")
except Exception as e:
    log_test("Admin /stats endpoint (protected)", False, f"Exception: {str(e)}")

# Test /api/admin/orders
try:
    response = requests.get(f"{API_BASE}/admin/orders", timeout=20)
    if response.status_code == 401:
        log_test("Admin /orders endpoint (protected)", True, f"Correctly returns 401 (unauthenticated)")
    elif response.status_code == 404:
        log_test("Admin /orders endpoint (protected)", False, "Returns 404 - admin router may not be registered!")
    else:
        log_test("Admin /orders endpoint (protected)", False, f"Expected 401, got {response.status_code}: {response.text}")
except Exception as e:
    log_test("Admin /orders endpoint (protected)", False, f"Exception: {str(e)}")

# ==========================================
# SUMMARY
# ==========================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"✅ Passed: {len(test_results['passed'])}")
for test in test_results['passed']:
    print(f"   - {test}")

if test_results['warnings']:
    print(f"\n⚠️  Warnings: {len(test_results['warnings'])}")
    for warning in test_results['warnings']:
        print(f"   - {warning['name']}: {warning['details']}")

if test_results['failed']:
    print(f"\n❌ Failed: {len(test_results['failed'])}")
    for failure in test_results['failed']:
        print(f"   - {failure['name']}")
        if failure['details']:
            print(f"     {failure['details']}")
    print("\n⚠️  DEPLOYMENT BLOCKED - Fix failed tests before deploying")
else:
    print("\n✅ ALL TESTS PASSED - Ready for deployment")

print("=" * 80)
