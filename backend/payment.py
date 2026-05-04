"""Midtrans Snap payment integration for Rimpods.

Flow:
  1. Frontend POST /api/payment/midtrans/snap-token with existing order_id
  2. Backend creates Snap transaction, returns token + redirect_url
  3. Frontend opens snap.pay(token) popup
  4. On completion, Midtrans sends webhook to /api/payment/midtrans/notification
  5. Backend verifies signature (SHA512) + updates order status in MongoDB

Env vars:
  MIDTRANS_SERVER_KEY     (required) — for API calls + signature check
  MIDTRANS_CLIENT_KEY     (used frontend side)
  MIDTRANS_MERCHANT_ID    (informational)
  MIDTRANS_IS_PRODUCTION  ("true" / "false")
"""
import os
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

try:
    import midtransclient  # type: ignore
except ImportError:  # pragma: no cover
    midtransclient = None

logger = logging.getLogger(__name__)

# Status mapping from Midtrans transaction_status -> internal order status
_STATUS_MAP = {
    "capture": "paid",        # credit card only (usually followed by settlement)
    "settlement": "paid",
    "pending": "pending",
    "deny": "failed",
    "cancel": "cancelled",
    "expire": "expired",
    "refund": "refunded",
    "partial_refund": "refunded",
    "failure": "failed",
    "authorize": "pending",
}


def _config_ok() -> bool:
    return bool(os.environ.get("MIDTRANS_SERVER_KEY")) and midtransclient is not None


def _make_snap():
    if not _config_ok():
        raise HTTPException(status_code=503, detail="Midtrans belum dikonfigurasi.")
    return midtransclient.Snap(
        is_production=os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true",
        server_key=os.environ["MIDTRANS_SERVER_KEY"],
        client_key=os.environ.get("MIDTRANS_CLIENT_KEY", ""),
    )


class SnapTokenRequest(BaseModel):
    order_id: str = Field(..., description="Internal order id (UUID) from POST /api/orders")


def build_payment_router(db) -> APIRouter:
    router = APIRouter(prefix="/api/payment/midtrans", tags=["payment"])

    @router.get("/config")
    async def get_public_config():
        """Frontend can call this to know if Midtrans is available & which mode."""
        return {
            "enabled": _config_ok(),
            "client_key": os.environ.get("MIDTRANS_CLIENT_KEY", ""),
            "is_production": os.environ.get("MIDTRANS_IS_PRODUCTION", "false").lower() == "true",
            "merchant_id": os.environ.get("MIDTRANS_MERCHANT_ID", ""),
        }

    @router.post("/snap-token")
    async def create_snap_token(payload: SnapTokenRequest):
        """Fetch an order from Mongo, build a Snap transaction, return token + redirect_url."""
        snap = _make_snap()
        order = await db.orders.find_one({"id": payload.order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order tidak ditemukan")

        items = order.get("items") or []
        item_details = [
            {
                "id": (it.get("product_id") or "item")[:50],
                "price": int(it.get("price") or 0),
                "quantity": int(it.get("quantity") or 0),
                "name": (it.get("name") or "Rimpods Item")[:50],
            }
            for it in items
        ]
        # Line for shipping fee (Midtrans requires sum(items.price*qty) == gross_amount)
        shipping = int(order.get("shipping") or 0)
        if shipping > 0:
            item_details.append({
                "id": "SHIPPING",
                "price": shipping,
                "quantity": 1,
                "name": "Ongkos Kirim",
            })
        discount = int(order.get("discount") or 0)
        if discount > 0:
            item_details.append({
                "id": "DISCOUNT",
                "price": -discount,
                "quantity": 1,
                "name": f"Voucher {order.get('voucher_code') or ''}".strip(),
            })

        contact = order.get("contact") or {}
        full_name = (contact.get("name") or "").strip() or "Pelanggan Rimpods"
        parts = full_name.split(" ", 1)
        first_name = parts[0][:20]
        last_name = parts[1][:20] if len(parts) > 1 else ""

        gross_amount = int(order.get("total") or sum(i["price"] * i["quantity"] for i in item_details))

        params = {
            "transaction_details": {
                "order_id": order["order_number"],
                "gross_amount": gross_amount,
            },
            "item_details": item_details,
            "customer_details": {
                "first_name": first_name,
                "last_name": last_name,
                "email": contact.get("email") or "noreply@rimpods.co",
                "phone": contact.get("phone") or "",
                "billing_address": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": contact.get("phone") or "",
                    "address": contact.get("address") or "",
                    "city": contact.get("city") or "",
                    "country_code": "IDN",
                },
                "shipping_address": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": contact.get("phone") or "",
                    "address": contact.get("address") or "",
                    "city": contact.get("city") or "",
                    "country_code": "IDN",
                },
            },
            "credit_card": {"secure": True},
        }

        try:
            result = snap.create_transaction(params)
        except Exception as e:  # midtransclient.error.MidtransAPIError
            logger.exception("Midtrans snap create_transaction failed")
            raise HTTPException(status_code=502, detail=f"Midtrans error: {e}")

        token = result.get("token")
        redirect_url = result.get("redirect_url")
        if not token:
            raise HTTPException(status_code=502, detail="Midtrans tidak mengembalikan token")

        await db.orders.update_one(
            {"id": order["id"]},
            {"$set": {
                "midtrans_token": token,
                "midtrans_redirect_url": redirect_url,
                "payment_channel": "midtrans",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        return {"token": token, "redirect_url": redirect_url, "order_number": order["order_number"]}

    def _verify_signature(order_id: str, status_code: str, gross_amount: str, server_key: str,
                          received_signature: str) -> bool:
        raw = f"{order_id}{status_code}{gross_amount}{server_key}"
        expected = hashlib.sha512(raw.encode("utf-8")).hexdigest()
        # constant-time comparison
        if len(expected) != len(received_signature or ""):
            return False
        ok = 0
        for a, b in zip(expected, received_signature):
            ok |= ord(a) ^ ord(b)
        return ok == 0

    @router.post("/notification")
    async def webhook_notification(request: Request):
        """Receive async payment status updates from Midtrans.

        Midtrans sends JSON with signature_key = SHA512(order_id + status_code + gross_amount + server_key).
        """
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Body bukan JSON valid")

        server_key = os.environ.get("MIDTRANS_SERVER_KEY", "")
        if not server_key:
            logger.warning("Midtrans webhook received but MIDTRANS_SERVER_KEY not set")
            return {"status": "ignored", "reason": "not_configured"}

        order_number = data.get("order_id") or ""
        status_code = str(data.get("status_code") or "")
        gross_amount = str(data.get("gross_amount") or "")
        signature = data.get("signature_key") or ""

        if not _verify_signature(order_number, status_code, gross_amount, server_key, signature):
            logger.warning("Midtrans webhook signature mismatch for order %s", order_number)
            # 200 so Midtrans doesn't retry infinitely — but do NOT mutate state
            return {"status": "signature_mismatch"}

        trx_status = (data.get("transaction_status") or "").lower()
        fraud = (data.get("fraud_status") or "").lower()
        payment_type = data.get("payment_type") or ""
        transaction_id = data.get("transaction_id") or ""

        # Credit-card "capture" with fraud_status=challenge is suspicious, hold as pending
        if trx_status == "capture" and fraud == "challenge":
            new_status = "review"
        elif trx_status == "capture" and fraud == "deny":
            new_status = "failed"
        else:
            new_status = _STATUS_MAP.get(trx_status, "pending")

        update = {
            "status": new_status,
            "payment_type": payment_type,
            "midtrans_transaction_id": transaction_id,
            "midtrans_fraud_status": fraud or None,
            "midtrans_transaction_status": trx_status,
            "midtrans_raw": data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if new_status == "paid":
            update["paid_at"] = datetime.now(timezone.utc).isoformat()

        result = await db.orders.update_one({"order_number": order_number}, {"$set": update})
        if result.matched_count == 0:
            logger.warning("Midtrans webhook: order_number %s not found", order_number)
            return {"status": "order_not_found"}

        logger.info("Midtrans webhook processed: %s -> %s", order_number, new_status)
        return {"status": "ok", "new_status": new_status}

    @router.get("/status/{order_number}")
    async def get_payment_status(order_number: str):
        """Frontend can poll this after Snap popup closes to confirm latest status."""
        order = await db.orders.find_one({"order_number": order_number}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order tidak ditemukan")
        return {
            "order_number": order["order_number"],
            "status": order.get("status", "pending"),
            "payment_type": order.get("payment_type"),
            "midtrans_transaction_status": order.get("midtrans_transaction_status"),
        }

    return router
