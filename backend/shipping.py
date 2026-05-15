"""Shipping rate calculator for Rimpods (weight-aware).

Each courier zone has:
  - first_kg : cost for first 1 kg
  - next_kg  : cost per additional kg (rounded UP to whole kg)

Formula: total = first_kg + max(0, ceil(weight_kg) - 1) * next_kg

Live coral food benefits from same-day couriers (Paxel) where available.
Admin can tune RATES dict below + redeploy.
"""
import math
from typing import List, Dict, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

ZONE_KEYWORDS = {
    1: [  # Jabodetabek + same-day Paxel coverage
        "jakarta", "depok", "bekasi", "tangerang", "bogor", "tangsel", "banten",
        "jakarta selatan", "jakarta utara", "jakarta barat", "jakarta timur", "jakarta pusat",
    ],
    2: [  # Jawa lainnya
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

# Rates per zone per courier: first_kg + next_kg (in IDR)
RATES: Dict[int, List[dict]] = {
    1: [
        {"courier": "Paxel", "service": "Same Day",  "first_kg": 25000, "next_kg": 10000, "etd": "Hari ini, 4-8 jam"},
        {"courier": "JNT",   "service": "Reguler",   "first_kg": 15000, "next_kg":  6000, "etd": "1-2 hari kerja"},
        {"courier": "Tiki",  "service": "Reguler",   "first_kg": 16000, "next_kg":  7000, "etd": "1-2 hari kerja"},
    ],
    2: [
        {"courier": "Paxel", "service": "Next Day",  "first_kg": 45000, "next_kg": 18000, "etd": "1 hari kerja"},
        {"courier": "JNT",   "service": "Reguler",   "first_kg": 25000, "next_kg":  9000, "etd": "2-3 hari kerja"},
        {"courier": "Tiki",  "service": "Reguler",   "first_kg": 27000, "next_kg": 10000, "etd": "2-3 hari kerja"},
    ],
    3: [
        {"courier": "Paxel", "service": "Next Day",  "first_kg": 70000, "next_kg": 30000, "etd": "1-2 hari kerja"},
        {"courier": "JNT",   "service": "Reguler",   "first_kg": 45000, "next_kg": 18000, "etd": "3-5 hari kerja"},
        {"courier": "Tiki",  "service": "Reguler",   "first_kg": 48000, "next_kg": 19000, "etd": "3-5 hari kerja"},
    ],
    4: [
        {"courier": "Paxel", "service": "Express",   "first_kg": 100000, "next_kg": 45000, "etd": "2-3 hari kerja"},
        {"courier": "JNT",   "service": "Reguler",   "first_kg":  70000, "next_kg": 28000, "etd": "4-7 hari kerja"},
        {"courier": "Tiki",  "service": "Reguler",   "first_kg":  75000, "next_kg": 30000, "etd": "4-7 hari kerja"},
    ],
}

DEFAULT_ZONE = 3


def resolve_zone(*texts: str) -> int:
    blob = " ".join(t.lower() for t in texts if t).strip()
    if not blob:
        return DEFAULT_ZONE
    for zone, keywords in ZONE_KEYWORDS.items():
        for kw in keywords:
            if kw in blob:
                return zone
    return DEFAULT_ZONE


def billable_kg(weight_kg: float) -> int:
    """Round UP to nearest whole kg, minimum 1."""
    if weight_kg <= 0:
        return 1
    return max(1, math.ceil(weight_kg))


def compute_cost(first_kg: int, next_kg: int, weight_kg: float) -> int:
    bkg = billable_kg(weight_kg)
    return int(first_kg + max(0, bkg - 1) * next_kg)


def get_rates(city: str = "", kecamatan: str = "", address: str = "",
              weight_kg: float = 1.0) -> List[dict]:
    zone = resolve_zone(city, kecamatan, address)
    bkg = billable_kg(weight_kg)
    out = []
    for r in RATES[zone]:
        cost = compute_cost(r["first_kg"], r["next_kg"], weight_kg)
        out.append({
            "courier": r["courier"],
            "service": r["service"],
            "cost": cost,
            "etd": r["etd"],
            "zone": zone,
            "weight_kg": round(weight_kg, 2),
            "billable_kg": bkg,
        })
    return out


def get_rate_by_choice(courier: str, city: str = "", kecamatan: str = "",
                       address: str = "", weight_kg: float = 1.0) -> dict:
    rates = get_rates(city, kecamatan, address, weight_kg)
    courier_lc = (courier or "").lower()
    for r in rates:
        if r["courier"].lower() == courier_lc:
            return r
    return rates[0] if rates else {"courier": courier, "service": "Reguler", "cost": 0, "etd": "—"}


class RatesPayload(BaseModel):
    city: Optional[str] = ""
    kecamatan: Optional[str] = ""
    address: Optional[str] = ""
    weight_kg: float = 1.0


def build_shipping_router() -> APIRouter:
    router = APIRouter(prefix="/api/shipping", tags=["shipping"])

    @router.get("/rates")
    async def list_rates(
        city: str = Query(default=""),
        kecamatan: str = Query(default=""),
        address: str = Query(default=""),
        weight_kg: float = Query(default=1.0, ge=0),
    ):
        rates = get_rates(city, kecamatan, address, weight_kg)
        return {
            "zone": rates[0]["zone"] if rates else DEFAULT_ZONE,
            "weight_kg": round(weight_kg, 2),
            "billable_kg": billable_kg(weight_kg),
            "rates": rates,
        }

    @router.post("/rates")
    async def list_rates_post(payload: RatesPayload):
        """POST variant for clients that prefer to send weight in body."""
        rates = get_rates(payload.city or "", payload.kecamatan or "",
                          payload.address or "", payload.weight_kg)
        return {
            "zone": rates[0]["zone"] if rates else DEFAULT_ZONE,
            "weight_kg": round(payload.weight_kg, 2),
            "billable_kg": billable_kg(payload.weight_kg),
            "rates": rates,
        }

    return router
