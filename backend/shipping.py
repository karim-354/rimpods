"""Shipping rate calculator for Rimpods.

Strategy: zone-based pricing per courier. Customer types city/kecamatan,
backend matches keyword to zone, returns 3 courier options with their rates.

Rates can be tuned later via env or moved to MongoDB collection.
Live coral food benefits from same-day couriers (Paxel) where available.
"""
from typing import List, Dict
from fastapi import APIRouter, Query

# Zone definitions — keyword match (lowercased)
ZONE_KEYWORDS = {
    1: [  # Jabodetabek + same-day Paxel coverage
        "jakarta", "depok", "bekasi", "tangerang", "bogor", "tangsel", "banten",
        "south jakarta", "west jakarta", "east jakarta", "north jakarta", "central jakarta",
        "jakarta selatan", "jakarta utara", "jakarta barat", "jakarta timur", "jakarta pusat",
    ],
    2: [  # Jawa lainnya (Bandung, Surabaya, Semarang, dll)
        "bandung", "cimahi", "sukabumi", "cianjur", "cirebon", "garut", "tasikmalaya",
        "purwokerto", "yogyakarta", "jogja", "solo", "surakarta", "semarang", "magelang",
        "surabaya", "malang", "kediri", "madiun", "jember", "sidoarjo", "gresik",
        "jawa", "java",
    ],
    3: [  # Sumatera + Bali + Lombok
        "bali", "denpasar", "ubud", "gianyar", "tabanan",
        "lombok", "mataram", "bima", "sumbawa", "ntb",
        "medan", "padang", "palembang", "pekanbaru", "batam", "lampung",
        "jambi", "bengkulu", "aceh", "tanjung pinang", "sumatera",
    ],
    4: [  # Kalimantan, Sulawesi, Maluku, Papua, Indonesia Timur
        "kalimantan", "balikpapan", "samarinda", "pontianak", "banjarmasin", "tarakan",
        "sulawesi", "makassar", "manado", "palu", "kendari", "gorontalo",
        "maluku", "ambon", "ternate",
        "papua", "jayapura", "sorong", "manokwari",
        "kupang", "ntt", "flores",
    ],
}

# Rates per zone per courier (in IDR). Live coral kemasan ~1-3kg.
# Format: zone -> [{courier, service, cost, etd}]
RATES: Dict[int, List[dict]] = {
    1: [
        {"courier": "Paxel", "service": "Same Day", "cost": 25000, "etd": "Hari ini, 4-8 jam"},
        {"courier": "JNT", "service": "Reguler", "cost": 15000, "etd": "1-2 hari kerja"},
        {"courier": "Tiki", "service": "Reguler", "cost": 16000, "etd": "1-2 hari kerja"},
    ],
    2: [
        {"courier": "Paxel", "service": "Next Day", "cost": 45000, "etd": "1 hari kerja"},
        {"courier": "JNT", "service": "Reguler", "cost": 25000, "etd": "2-3 hari kerja"},
        {"courier": "Tiki", "service": "Reguler", "cost": 27000, "etd": "2-3 hari kerja"},
    ],
    3: [
        {"courier": "Paxel", "service": "Next Day", "cost": 70000, "etd": "1-2 hari kerja"},
        {"courier": "JNT", "service": "Reguler", "cost": 45000, "etd": "3-5 hari kerja"},
        {"courier": "Tiki", "service": "Reguler", "cost": 48000, "etd": "3-5 hari kerja"},
    ],
    4: [
        {"courier": "Paxel", "service": "Express", "cost": 100000, "etd": "2-3 hari kerja"},
        {"courier": "JNT", "service": "Reguler", "cost": 70000, "etd": "4-7 hari kerja"},
        {"courier": "Tiki", "service": "Reguler", "cost": 75000, "etd": "4-7 hari kerja"},
    ],
}

DEFAULT_ZONE = 3  # Conservative default for unknown cities


def resolve_zone(*texts: str) -> int:
    """Match any provided text (city, kecamatan, address) against keywords."""
    blob = " ".join(t.lower() for t in texts if t).strip()
    if not blob:
        return DEFAULT_ZONE
    for zone, keywords in ZONE_KEYWORDS.items():
        for kw in keywords:
            if kw in blob:
                return zone
    return DEFAULT_ZONE


def get_rates(city: str = "", kecamatan: str = "", address: str = "") -> List[dict]:
    zone = resolve_zone(city, kecamatan, address)
    return [{**r, "zone": zone} for r in RATES[zone]]


def get_rate_by_choice(courier: str, city: str = "", kecamatan: str = "", address: str = "") -> dict:
    """Find specific courier+rate for the resolved zone. Returns dict with cost+service+etd."""
    rates = get_rates(city, kecamatan, address)
    courier_lc = (courier or "").lower()
    for r in rates:
        if r["courier"].lower() == courier_lc:
            return r
    # fallback to first if courier name didn't match (defensive)
    return rates[0] if rates else {"courier": courier, "service": "Reguler", "cost": 0, "etd": "—"}


def build_shipping_router() -> APIRouter:
    router = APIRouter(prefix="/api/shipping", tags=["shipping"])

    @router.get("/rates")
    async def list_rates(
        city: str = Query(default=""),
        kecamatan: str = Query(default=""),
        address: str = Query(default=""),
    ):
        rates = get_rates(city, kecamatan, address)
        return {"zone": rates[0]["zone"] if rates else DEFAULT_ZONE, "rates": rates}

    return router
