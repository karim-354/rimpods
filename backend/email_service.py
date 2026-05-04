"""Email service via Resend for Rimpods.

Non-blocking (asyncio.to_thread) + graceful fallback: if RESEND_API_KEY is missing
or delivery fails, it logs and returns — never raises in a way that blocks the order flow.

IMPORTANT — sender limits:
  • Resend only lets you send FROM a verified domain. Without domain verification,
    `onboarding@resend.dev` is the only allowed FROM address.
  • We set reply-to to `rimpods@gmail.com` so replies still reach the admin inbox.
  • Resend testing mode ALSO limits TO addresses to the account-owner email. Once the
    user verifies a domain, other recipients will go through.
"""
import os
import asyncio
import logging
from typing import Optional

try:
    import resend  # type: ignore
except ImportError:  # pragma: no cover
    resend = None

logger = logging.getLogger(__name__)

BRAND_COLORS = {
    "navy": "#082233",
    "mid": "#0d3a52",
    "coral": "#ff6a52",
    "glow": "#31d4c4",
    "foam": "#e8f4f6",
    "muted": "#6b9aac",
}

_LOGO_URL = "https://customer-assets.emergentagent.com/job_coral-product-hub/artifacts/5gz4ojsf_Logo%20Transparant%20%284%29.png"

_STYLE_WRAP = f"""
<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width"/>
<title>Rimpods</title></head>
<body style="margin:0;padding:0;background-color:{BRAND_COLORS['navy']};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:{BRAND_COLORS['foam']};">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{BRAND_COLORS['navy']};padding:24px 12px;">
<tr><td align="center">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="560" style="max-width:560px;background-color:{BRAND_COLORS['mid']};border-radius:18px;overflow:hidden;">
<tr><td style="padding:28px 32px 4px;background-color:{BRAND_COLORS['navy']};" align="left">
<img src="{_LOGO_URL}" alt="Rimpods" height="44" style="display:block;height:44px;width:auto;border:0;outline:none;" />
</td></tr>
"""

_STYLE_FOOTER = f"""
<tr><td style="padding:28px 32px 32px;background-color:rgba(0,0,0,0.25);text-align:center;">
<img src="{_LOGO_URL}" alt="Rimpods" height="28" style="display:inline-block;height:28px;width:auto;border:0;outline:none;opacity:0.7;margin-bottom:12px;" /><br/>
<div style="color:{BRAND_COLORS['muted']};font-size:11px;line-height:1.7;">
Live coral food · Dikultur dengan penuh perhatian di Bekasi<br/>
Balas email ini untuk berdiskusi langsung — kami mendengarkan.
</div>
</td></tr>
</table>
</td></tr></table>
</body></html>
"""


def _header(eyebrow: str, title: str, intro: str) -> str:
    return f"""
<tr><td style="padding:24px 32px 0;background-color:{BRAND_COLORS['mid']};">
<div style="letter-spacing:3px;text-transform:uppercase;color:{BRAND_COLORS['glow']};font-size:11px;font-weight:600;margin-bottom:12px;">{eyebrow}</div>
<h1 style="margin:0 0 14px;color:{BRAND_COLORS['foam']};font-size:26px;font-weight:700;letter-spacing:-0.01em;line-height:1.25;">{title}</h1>
<p style="margin:0;color:rgba(232,244,246,0.85);font-size:15px;line-height:1.65;">{intro}</p>
</td></tr>
"""


def _rupiah(n) -> str:
    try:
        return "Rp" + f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def _items_table(items: list) -> str:
    rows = ""
    for it in items or []:
        name = it.get("name", "")
        qty = int(it.get("quantity") or 0)
        line = _rupiah(it.get("line_total") or (it.get("price", 0) * qty))
        rows += f"""
<tr>
<td style="padding:10px 0;color:{BRAND_COLORS['foam']};font-size:14px;border-bottom:1px solid rgba(49,212,196,0.12);">{name} <span style="color:{BRAND_COLORS['muted']};">× {qty}</span></td>
<td style="padding:10px 0;color:{BRAND_COLORS['foam']};font-size:14px;text-align:right;border-bottom:1px solid rgba(49,212,196,0.12);font-weight:600;">{line}</td>
</tr>"""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:12px;">
{rows}
</table>"""


def _summary_rows(order: dict) -> str:
    subtotal = order.get("subtotal", 0)
    shipping = order.get("shipping", 0)
    discount = order.get("discount", 0)
    voucher = order.get("voucher_code")
    total = order.get("total", 0)
    rows = [
        ("Subtotal", _rupiah(subtotal), False),
        ("Pengiriman", "Gratis" if shipping == 0 else _rupiah(shipping), False),
    ]
    if discount > 0 and voucher:
        rows.append((f"Voucher {voucher}", f"-{_rupiah(discount)}", False))
    rows.append(("Total", _rupiah(total), True))
    html = ""
    for label, val, bold in rows:
        weight = "700" if bold else "500"
        color = BRAND_COLORS["glow"] if bold else BRAND_COLORS["foam"]
        fs = "17px" if bold else "13px"
        border = f"border-top:1px solid rgba(49,212,196,0.3);padding-top:14px;" if bold else ""
        html += f"""
<tr>
<td style="padding:6px 0;color:{BRAND_COLORS['muted']};font-size:13px;{border}">{label}</td>
<td style="padding:6px 0;color:{color};font-size:{fs};text-align:right;font-weight:{weight};{border}">{val}</td>
</tr>"""
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:18px;">
{html}
</table>"""


def _address_block(order: dict) -> str:
    contact = order.get("contact") or {}
    return f"""
<tr><td style="padding:6px 32px 0;">
<div style="background-color:rgba(8,34,51,0.55);border:1px solid rgba(49,212,196,0.15);border-radius:12px;padding:18px 20px;">
<div style="letter-spacing:2px;text-transform:uppercase;color:{BRAND_COLORS['glow']};font-size:10px;font-weight:600;margin-bottom:8px;">Alamat Pengiriman</div>
<div style="color:{BRAND_COLORS['foam']};font-size:14px;line-height:1.55;">
<b>{contact.get('name','—')}</b> &nbsp;·&nbsp; <span style="color:{BRAND_COLORS['muted']};">{contact.get('phone','')}</span><br/>
{contact.get('address','—')}, {contact.get('city','')}
</div>
</div>
</td></tr>"""


def _items_block(order: dict) -> str:
    return f"""
<tr><td style="padding:24px 32px 4px;">
<div style="letter-spacing:2px;text-transform:uppercase;color:{BRAND_COLORS['muted']};font-size:10px;font-weight:600;margin-bottom:6px;">Detail Pesanan</div>
{_items_table(order.get('items', []))}
{_summary_rows(order)}
</td></tr>"""


def _cta_button(label: str, href: str, variant: str = "coral") -> str:
    bg = BRAND_COLORS["coral"] if variant == "coral" else BRAND_COLORS["glow"]
    color = "#ffffff" if variant == "coral" else BRAND_COLORS["navy"]
    return f"""
<tr><td style="padding:20px 32px 8px;" align="center">
<a href="{href}" style="display:inline-block;background-color:{bg};color:{color};text-decoration:none;font-weight:600;font-size:15px;padding:14px 28px;border-radius:999px;">{label}</a>
</td></tr>"""


def _order_number_block(order: dict) -> str:
    return f"""
<tr><td style="padding:22px 32px 0;">
<div style="background-color:rgba(49,212,196,0.08);border:1px dashed rgba(49,212,196,0.35);border-radius:10px;padding:12px 16px;text-align:center;">
<div style="letter-spacing:2px;text-transform:uppercase;color:{BRAND_COLORS['muted']};font-size:10px;font-weight:600;margin-bottom:4px;">No. Order</div>
<div style="font-family:'SF Mono',Menlo,monospace;color:{BRAND_COLORS['glow']};font-size:16px;font-weight:700;letter-spacing:0.05em;">{order.get('order_number','')}</div>
</div>
</td></tr>"""


def render_order_confirmation(order: dict) -> str:
    first = (order.get("contact", {}).get("name") or "").split(" ")[0] or "Kak"
    intro = (
        f"Halo {first}, terima kasih sudah memilih Rimpods. Pesanan kamu sudah kami terima "
        "dan sedang kami siapkan dengan penuh perhatian."
    )
    wa = order.get("whatsapp_url") or ""
    cta = _cta_button("Konfirmasi via WhatsApp", wa) if wa else ""
    return _STYLE_WRAP + _header("PESANAN DITERIMA", "Coral kamu sudah dekat.", intro) + \
        _order_number_block(order) + _items_block(order) + _address_block(order) + cta + _STYLE_FOOTER


def render_payment_success(order: dict) -> str:
    first = (order.get("contact", {}).get("name") or "").split(" ")[0] or "Kak"
    ptype = (order.get("payment_type") or "").replace("_", " ").title() or "pembayaran online"
    intro = (
        f"Halo {first}, pembayaran kamu via {ptype} sudah kami terima dengan baik. "
        "Tim kami akan segera menyiapkan pengiriman — kamu akan menerima nomor resi dalam email berikutnya."
    )
    return _STYLE_WRAP + _header("PEMBAYARAN BERHASIL", "Terima kasih — kami sudah menerima pembayaran kamu.", intro) + \
        _order_number_block(order) + _items_block(order) + _address_block(order) + _STYLE_FOOTER


def render_shipping_notification(order: dict, courier: str, tracking: str, eta: str) -> str:
    first = (order.get("contact", {}).get("name") or "").split(" ")[0] or "Kak"
    intro = (
        f"Halo {first}, pesanan kamu sudah dalam perjalanan. Di bawah ini detail pengirimannya — "
        "mohon pastikan ada yang menerima saat kurir tiba."
    )
    track_block = f"""
<tr><td style="padding:22px 32px 4px;">
<div style="background-color:rgba(255,106,82,0.08);border:1px solid rgba(255,106,82,0.3);border-radius:12px;padding:18px 20px;">
<div style="letter-spacing:2px;text-transform:uppercase;color:{BRAND_COLORS['coral']};font-size:10px;font-weight:600;margin-bottom:10px;">Informasi Pengiriman</div>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
<tr><td style="color:{BRAND_COLORS['muted']};font-size:13px;padding:4px 0;">Kurir</td><td style="color:{BRAND_COLORS['foam']};font-size:14px;text-align:right;font-weight:600;">{courier}</td></tr>
<tr><td style="color:{BRAND_COLORS['muted']};font-size:13px;padding:4px 0;">No. Resi</td><td style="color:{BRAND_COLORS['glow']};font-size:14px;text-align:right;font-weight:700;font-family:'SF Mono',Menlo,monospace;">{tracking}</td></tr>
<tr><td style="color:{BRAND_COLORS['muted']};font-size:13px;padding:4px 0;">Estimasi Tiba</td><td style="color:{BRAND_COLORS['foam']};font-size:14px;text-align:right;font-weight:600;">{eta}</td></tr>
</table></div></td></tr>"""
    return _STYLE_WRAP + _header("DALAM PERJALANAN", "Coral kamu sedang menuju tank baru.", intro) + \
        _order_number_block(order) + track_block + _items_block(order) + _address_block(order) + _STYLE_FOOTER


def render_admin_notification(order: dict) -> str:
    contact = order.get("contact") or {}
    first = contact.get("name", "—")
    voucher = order.get("voucher_code")
    voucher_line = f" · voucher <b>{voucher}</b>" if voucher else ""
    channel = order.get("payment_channel", "—")
    intro = (
        f"Order baru masuk dari <b>{first}</b> via <b>{channel}</b>{voucher_line}. "
        "Detail lengkap ada di bawah — silakan follow-up di admin dashboard."
    )
    wa_phone = contact.get("phone", "").lstrip("0").replace("+", "")
    if wa_phone.startswith("8"):
        wa_phone = "62" + wa_phone
    elif not wa_phone.startswith("62"):
        wa_phone = wa_phone
    cta = _cta_button(f"Chat {first} di WhatsApp", f"https://wa.me/{wa_phone}") if wa_phone else ""
    return _STYLE_WRAP + _header("ORDER BARU", f"Order masuk — {_rupiah(order.get('total',0))}", intro) + \
        _order_number_block(order) + _items_block(order) + _address_block(order) + cta + _STYLE_FOOTER


# === Sender ===

_TEMPLATES = {
    "order_confirmation": (render_order_confirmation, "Pesanan kamu sudah kami terima — Rimpods"),
    "payment_success": (render_payment_success, "Pembayaran berhasil — Rimpods"),
    "shipping": (render_shipping_notification, "Pesanan kamu dalam perjalanan — Rimpods"),
    "admin_new_order": (render_admin_notification, "[Rimpods] Order baru masuk"),
}


def _configured() -> bool:
    return bool(os.environ.get("RESEND_API_KEY")) and resend is not None


async def _send(to_email: str, subject: str, html: str) -> Optional[str]:
    if not _configured():
        logger.warning("Resend not configured, skipping email to %s", to_email)
        return None
    resend.api_key = os.environ["RESEND_API_KEY"]
    from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    from_name = os.environ.get("RESEND_FROM_NAME", "Rimpods")
    reply_to = os.environ.get("RESEND_REPLY_TO")

    params = {
        "from": f"{from_name} <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "html": html,
    }
    if reply_to:
        params["reply_to"] = reply_to

    # Retry once on rate-limit (Resend free tier: 2 req/sec)
    for attempt in (0, 1):
        try:
            res = await asyncio.to_thread(resend.Emails.send, params)
            email_id = res.get("id") if isinstance(res, dict) else None
            logger.info("Resend sent to %s (id=%s)", to_email, email_id)
            return email_id
        except Exception as e:
            msg = str(e).lower()
            if attempt == 0 and ("rate" in msg or "too many" in msg):
                await asyncio.sleep(1.1)
                continue
            logger.error("Resend send failure to %s: %s", to_email, e)
            return None
    return None


async def send_order_confirmation(order: dict) -> Optional[str]:
    to = (order.get("contact") or {}).get("email")
    if not to:
        logger.info("Skipping order_confirmation email: no customer email")
        return None
    render, subj = _TEMPLATES["order_confirmation"]
    return await _send(to, subj, render(order))


async def send_payment_success(order: dict) -> Optional[str]:
    to = (order.get("contact") or {}).get("email")
    if not to:
        return None
    render, subj = _TEMPLATES["payment_success"]
    return await _send(to, subj, render(order))


async def send_shipping(order: dict, courier: str, tracking: str, eta: str) -> Optional[str]:
    to = (order.get("contact") or {}).get("email")
    if not to:
        return None
    render, subj = _TEMPLATES["shipping"]
    return await _send(to, subj, render(order, courier, tracking, eta))


async def send_admin_new_order(order: dict) -> Optional[str]:
    admin_to = os.environ.get("EMAIL_ADMIN_NOTIFY")
    if not admin_to:
        return None
    render, subj = _TEMPLATES["admin_new_order"]
    return await _send(admin_to, subj, render(order))
