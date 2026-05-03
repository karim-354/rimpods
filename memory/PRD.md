# Rimpods Live Coral Food — Sales Landing Page

## Original Problem Statement
"saya ingin buat landing page sales untuk produk2 yang ada di tokopedianya Rimpods live coral food"

User clarifications:
- Produk: 3 listing Tokopedia (Rotifera 2L+Phyto, Paket Hemat 5R+1P, Turn Back Nutrients)
- Tujuan: Edukasi + sales otomatis dengan checkout flow
- Bahasa: Indonesia native & friendly (anti-AI)
- Bonus: Sistem fingerprint_check.py (24 pola robotik) sebelum publish

## Architecture
- **Backend**: FastAPI (`/api/products`, `/api/orders`, `/api/content/verify`)
  - Static catalog of 3 products (data sourced from Tokopedia listings)
  - Order creation generates WhatsApp wa.me URL + Tokopedia URL (no payment gateway integrated; user completes purchase externally)
  - Anti-AI fingerprint module: `/app/backend/fingerprint_check.py` (24 patterns, score 0-100, min pass 55, hard-block corporate, auto-naturalize)
  - CLI version: `/app/scripts/fingerprint_check.py`
- **Frontend**: React + Tailwind + shadcn/ui
  - Routes: `/` (landing), `/checkout`, `/sukses`
  - Cart in localStorage (`rimpods_cart_v1`)
  - Aquatic premium aesthetic: deep navy + coral accent + teal glow, Fraunces + Manrope fonts, glass-morphism cards, bubble + caustics animations

## User Personas
- Reefer pemula: butuh edukasi, ingin ngerti coral food itu apa
- Reefer rajin: ngincer paket hemat untuk feeding rutin
- Reefer panik: tank crash, butuh TBN segera

## What's Implemented (Dec 2025)
### v1
- Hero with stat block + marquee bar
- 3 product cards with rating/sold/highlights/Tokopedia link
- Cerita, Cara Pakai, Testimoni, FAQ, CTA sections
- Cart drawer + Checkout form + Success page
- Anti-AI fingerprint check API + CLI

### v2 (latest)
- WhatsApp number live: +6282216594354 (env `RIMPODS_WHATSAPP`)
- Brand logo Rimpods (gold + tagline) di header, sumber dari customer-assets
- **Meta Pixel** sitewide id `354153630789298` — events: PageView, ViewContent (siap dipasang per produk), AddToCart, InitiateCheckout, Lead, Purchase
- **TikTok Pixel** sitewide id `CNQDS3JC77U0SCE9DUUG` — events: page, ViewContent, AddToCart, InitiateCheckout, SubmitForm, CompletePayment (siap closing dari ads GMV Max TikTok Shop)
- Helper `/app/frontend/src/lib/tracker.js` exposes `trackAddToCart`, `trackInitiateCheckout`, `trackLead`, `trackPurchase` — guarded against ad-blocker (no-throw)

## Backlog (P1/P2)
- P1: Real photos dari Rimpods (sekarang pakai stock Unsplash)
- P1: Logo Rimpods dari Google Drive (link disediakan, perlu download manual)
- P1: Editable WhatsApp number via env (sekarang placeholder 6281234567890)
- P2: Admin dashboard untuk lihat order masuk
- P2: Email confirmation via Resend/SMTP
- P2: Pixel tracking (Meta + Google Ads) untuk conversion attribution
- P2: Stripe / Midtrans integration untuk payment di-page
- P2: Multi-bahasa (English version)

### v3 (Feb 2026)
- **TBN photo swap** ke asset asli Rimpods (customer-assets emergentagent)
- **Upsell bundle split** — accept upsell masuk sebagai cart line terpisah (`${id}-bundle`), tidak merge dengan base item
- **Countdown urgency** 10 menit di UpsellModal (MM:SS, button disable + label "Promo Habis" saat expired)
- **Rimpods 2L photo swap** ke asset Rimpods (`a1.jpeg` + `aa.jpeg` sebagai hover/alt)
- **Backend bundle recognition** — POST `/api/orders` sekarang accept `${id}-bundle` product_id dan otomatis apply 10% discount + label `(Bundle -10%)` + flag `is_bundle: true`

### v4 (Feb 2026 — Conversion Polish)
- **Paket Hemat photo swap** ke asset asli Rimpods (Duo Maut + Saving Bundle)
- **Upsell countdown persistence** — timestamp di `sessionStorage[rimpods_upsell_ts_${id}]`, tidak reset saat modal ditutup-buka
- **Exit-intent popup** → voucher **FIRSTBUY20K** flat Rp20.000 off (min order Rp100.000). Trigger mouseout top viewport (desktop) / 25s timeout (mobile). Sekali per sesi.
- **Voucher backend** — `POST /api/orders` accept `voucher_code`, validate min subtotal, include diskon di WA message. Order schema sekarang punya `discount` + `voucher_code` fields.
- **Voucher frontend** — banner di Checkout (eligible/non-eligible state), auto-apply di payload, auto-clear setelah sukses, tombol remove manual.

## Test Status
- Backend: 22/22 pytest pass (iter 4 + iter 5)
- Frontend: iter 4 & 5 PASS — semua flow end-to-end verified, no regressions

## Next Action Items
1. **Pending user input**: TikTok Shop deep-link URL asli per produk (sekarang masih `tiktok.com/search?q=...`)
2. P2: Admin dashboard untuk lihat order masuk + redeemed voucher stats
3. P2: Email confirmation via Resend/SMTP
4. P2: Stripe / Midtrans integration untuk payment di-page
5. P2: Multi-bahasa (English version)
