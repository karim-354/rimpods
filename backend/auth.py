"""Emergent Google Auth + Admin whitelist for Rimpods."""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)

EMERGENT_SESSION_ENDPOINT = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
SESSION_TTL_DAYS = 7


def _parse_admin_emails() -> set[str]:
    raw = os.environ.get("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _is_admin(email: str) -> bool:
    return (email or "").lower() in _parse_admin_emails()


class SessionExchangeBody(BaseModel):
    session_id: str


def build_auth_router(db) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["auth"])

    async def _resolve_session_token(request: Request, authorization: Optional[str]) -> Optional[str]:
        # Prefer httpOnly cookie, fallback to Authorization bearer (for CLI tests)
        token = request.cookies.get("session_token")
        if token:
            return token
        if authorization and authorization.lower().startswith("bearer "):
            return authorization.split(" ", 1)[1].strip()
        return None

    async def current_user(request: Request, authorization: Optional[str] = Header(default=None)):
        token = await _resolve_session_token(request, authorization)
        if not token:
            raise HTTPException(status_code=401, detail="Tidak terautentikasi")
        session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=401, detail="Sesi tidak ditemukan")
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < datetime.now(timezone.utc):
            await db.user_sessions.delete_one({"session_token": token})
            raise HTTPException(status_code=401, detail="Sesi telah berakhir")
        user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User tidak ditemukan")
        return user

    async def require_admin(user=Depends(current_user)):
        if not _is_admin(user.get("email", "")):
            raise HTTPException(status_code=403, detail="Akses admin tidak diizinkan")
        return user

    @router.post("/session")
    async def exchange_session(payload: SessionExchangeBody, response: Response):
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                EMERGENT_SESSION_ENDPOINT,
                headers={"X-Session-ID": payload.session_id},
            )
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Session Google tidak valid")
        data = r.json()
        email = (data.get("email") or "").lower()
        if not email:
            raise HTTPException(status_code=400, detail="Email tidak tersedia dari Google")

        # Upsert user by email
        existing = await db.users.find_one({"email": email}, {"_id": 0})
        if existing:
            user_id = existing["user_id"]
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "name": data.get("name") or existing.get("name"),
                    "picture": data.get("picture") or existing.get("picture"),
                    "last_login_at": datetime.now(timezone.utc).isoformat(),
                }}
            )
        else:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            await db.users.insert_one({
                "user_id": user_id,
                "email": email,
                "name": data.get("name") or "",
                "picture": data.get("picture") or "",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login_at": datetime.now(timezone.utc).isoformat(),
            })

        # Persist session
        session_token = data.get("session_token") or uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=SESSION_TTL_DAYS * 24 * 3600,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
        )
        return {
            "user": {
                "user_id": user_id,
                "email": email,
                "name": data.get("name") or "",
                "picture": data.get("picture") or "",
                "is_admin": _is_admin(email),
            },
        }

    @router.get("/me")
    async def me(user=Depends(current_user)):
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user.get("name") or "",
            "picture": user.get("picture") or "",
            "is_admin": _is_admin(user["email"]),
        }

    @router.post("/logout")
    async def logout(request: Request, response: Response,
                     authorization: Optional[str] = Header(default=None)):
        token = request.cookies.get("session_token") or (
            authorization.split(" ", 1)[1].strip() if authorization and authorization.lower().startswith("bearer ") else None
        )
        if token:
            await db.user_sessions.delete_one({"session_token": token})
        response.delete_cookie("session_token", path="/", samesite="none", secure=True)
        return {"ok": True}

    return router, current_user, require_admin
