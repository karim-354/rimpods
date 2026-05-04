"""Admin dashboard routes — protected by Google Auth + email whitelist."""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from typing import Optional


def build_admin_router(db, require_admin) -> APIRouter:
    router = APIRouter(prefix="/api/admin", tags=["admin"])

    @router.get("/orders")
    async def list_orders(
        limit: int = Query(100, ge=1, le=500),
        skip: int = Query(0, ge=0),
        voucher_only: bool = False,
        admin=Depends(require_admin),
    ):
        filter_q = {}
        if voucher_only:
            filter_q["voucher_code"] = {"$ne": None}
        cursor = db.orders.find(filter_q, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        orders = await cursor.to_list(length=limit)
        total = await db.orders.count_documents(filter_q)
        return {"orders": orders, "total": total, "skip": skip, "limit": limit}

    @router.get("/stats")
    async def stats(days: int = Query(30, ge=1, le=365), admin=Depends(require_admin)):
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        pipeline_all = [
            {"$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$total"},
                "total_discount": {"$sum": {"$ifNull": ["$discount", 0]}},
            }}
        ]
        all_agg = await db.orders.aggregate(pipeline_all).to_list(1)
        overall = all_agg[0] if all_agg else {"total_orders": 0, "total_revenue": 0, "total_discount": 0}
        overall.pop("_id", None)

        pipeline_window = [
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {
                "_id": None,
                "orders": {"$sum": 1},
                "revenue": {"$sum": "$total"},
                "discount": {"$sum": {"$ifNull": ["$discount", 0]}},
            }}
        ]
        win_agg = await db.orders.aggregate(pipeline_window).to_list(1)
        window = win_agg[0] if win_agg else {"orders": 0, "revenue": 0, "discount": 0}
        window.pop("_id", None)

        vouchers_redeemed = await db.orders.count_documents({"voucher_code": {"$ne": None}})
        voucher_agg = await db.orders.aggregate([
            {"$match": {"voucher_code": {"$ne": None}}},
            {"$group": {
                "_id": "$voucher_code",
                "count": {"$sum": 1},
                "total_discount": {"$sum": "$discount"},
            }},
            {"$sort": {"count": -1}},
        ]).to_list(20)
        voucher_breakdown = [{"code": v["_id"], "count": v["count"], "total_discount": v["total_discount"]} for v in voucher_agg]

        channel_agg = await db.orders.aggregate([
            {"$group": {"_id": "$payment_channel", "count": {"$sum": 1}}},
        ]).to_list(10)
        channel_breakdown = {c["_id"]: c["count"] for c in channel_agg}

        return {
            "overall": overall,
            "window_days": days,
            "window": window,
            "vouchers_redeemed": vouchers_redeemed,
            "voucher_breakdown": voucher_breakdown,
            "channel_breakdown": channel_breakdown,
        }

    @router.patch("/orders/{order_id}/status")
    async def update_status(order_id: str, status: str, admin=Depends(require_admin)):
        valid = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
        if status not in valid:
            return {"ok": False, "error": f"status harus salah satu: {sorted(valid)}"}
        result = await db.orders.update_one({"id": order_id}, {"$set": {"status": status}})
        return {"ok": result.modified_count > 0}

    @router.post("/orders/{order_id}/ship")
    async def ship_order(order_id: str, courier: str, tracking: str, eta: str = "",
                         admin=Depends(require_admin)):
        """Mark order as shipped with courier/tracking/eta + trigger shipping email."""
        import asyncio as _asyncio
        import email_service

        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            return {"ok": False, "error": "Order tidak ditemukan"}

        await db.orders.update_one(
            {"id": order_id},
            {"$set": {
                "status": "shipped",
                "shipping_courier": courier,
                "shipping_tracking": tracking,
                "shipping_eta": eta,
            }},
        )
        refreshed = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if refreshed:
            _asyncio.create_task(email_service.send_shipping(refreshed, courier, tracking, eta or "3-5 hari"))
        return {"ok": True, "courier": courier, "tracking": tracking}

    return router
