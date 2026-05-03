import { useState } from "react";
import { MessageCircle, Copy, Check } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../ui/dialog";
import { Input } from "../ui/input";
import { Button } from "../ui/button";

// Normalize Indonesian phone: strip non-digits, 08..  -> 628..
export const normalizePhoneID = (raw) => {
  const digits = String(raw || "").replace(/\D/g, "");
  if (!digits) return "";
  if (digits.startsWith("62")) return digits;
  if (digits.startsWith("0")) return "62" + digits.slice(1);
  if (digits.startsWith("8")) return "62" + digits;
  return digits;
};

const itemsSummary = (items = []) =>
  items.map((i) => `${i.name} x${i.quantity}`).join(", ");

const buildTemplates = (order) => {
  const name = order?.contact?.name?.split(" ")[0] || "Kak";
  const orderNo = order?.order_number || "";
  const total = order?.total || 0;
  const totalFmt = "Rp" + Math.round(total).toLocaleString("id-ID");
  const addr = [order?.contact?.address, order?.contact?.city].filter(Boolean).join(", ");
  const items = itemsSummary(order?.items);

  return [
    {
      key: "confirm",
      label: "Konfirmasi Order",
      body:
        `Halo ${name}, terima kasih sudah memilih Rimpods 🌊\n\n` +
        `Pesanan kamu dengan No. *${orderNo}* sudah kami terima:\n` +
        `${items}\n\n` +
        `Total: *${totalFmt}*\n\n` +
        `Mohon konfirmasi pembayaran dengan mengirimkan bukti transfer ke nomor ini ya. Kami akan segera proses pengiriman setelahnya. Terima kasih 🙏`,
    },
    {
      key: "address",
      label: "Cek Alamat Pengiriman",
      body:
        `Halo ${name}, sebelum kami proses pengiriman untuk pesanan *${orderNo}*, mohon dikonfirmasi alamat berikut sudah benar ya:\n\n` +
        `📍 ${addr || "(alamat kosong — mohon dikirim ulang)"}\n\n` +
        `Jika ada yang perlu dikoreksi, silakan balas pesan ini. Terima kasih 🙏`,
    },
    {
      key: "shipping",
      label: "Kirim Resi",
      body:
        `Halo ${name}, kabar baik — pesanan *${orderNo}* sudah dalam perjalanan ke alamat kamu 🚚\n\n` +
        `Kurir: {KURIR}\n` +
        `No. Resi: *{RESI}*\n` +
        `Estimasi sampai: {ETA}\n\n` +
        `Mohon pastikan ada yang menerima saat kurir tiba. Terima kasih sudah mempercayakan tank kamu pada Rimpods 🙏`,
      needsInput: true,
      fields: [
        { key: "KURIR", label: "Kurir", placeholder: "JNE / J&T / SiCepat / Anteraja" },
        { key: "RESI", label: "No. Resi", placeholder: "CNT12345678" },
        { key: "ETA", label: "Estimasi sampai", placeholder: "besok / 2-3 hari" },
      ],
    },
    {
      key: "followup",
      label: "Follow-up Setelah Diterima",
      body:
        `Halo ${name}, pesanan *${orderNo}* sudah sampai di tempat kamu ya. Semoga coral-coralnya menikmati ❤️\n\n` +
        `Kalau ada pertanyaan soal cara pakai, kami siap bantu kapan saja. Boleh juga kalau sempat tinggalkan review jujur di Tokopedia — sangat membantu reefer lain yang sedang mempertimbangkan.\n\n` +
        `Terima kasih, dan sampai jumpa di order berikutnya 🙏`,
    },
  ];
};

function ShippingTemplateDialog({ open, onOpenChange, onConfirm, template }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries((template?.fields || []).map((f) => [f.key, ""]))
  );

  if (!template) return null;

  const filled = template.body.replace(/\{(\w+)\}/g, (_, k) => values[k] || `{${k}}`);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[hsl(var(--reef-mid))] border-[hsla(174,70%,55%,0.3)] text-[hsl(var(--reef-foam))] sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-display text-xl">Lengkapi Data Pengiriman</DialogTitle>
          <DialogDescription className="text-[hsl(var(--reef-foam))]/70">
            Isi 3 field di bawah — kami akan masukkan ke template WhatsApp secara otomatis.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          {template.fields.map((f) => (
            <div key={f.key}>
              <label className="text-xs uppercase tracking-widest opacity-70 mb-1.5 block">{f.label}</label>
              <Input
                data-testid={`wa-tpl-field-${f.key.toLowerCase()}`}
                value={values[f.key]}
                onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}
                placeholder={f.placeholder}
                className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]"
              />
            </div>
          ))}
          <div>
            <label className="text-xs uppercase tracking-widest opacity-70 mb-1.5 block">Preview</label>
            <div className="text-xs bg-[hsla(192,55%,22%,0.5)] border border-[hsla(174,70%,55%,0.2)] rounded-lg p-3 whitespace-pre-wrap max-h-48 overflow-y-auto">
              {filled}
            </div>
          </div>
          <Button
            data-testid="wa-tpl-confirm-btn"
            onClick={() => onConfirm(filled)}
            className="w-full coral-pill hover:opacity-90 h-11 rounded-full font-semibold"
          >
            Buka WhatsApp
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function WhatsAppQuickActions({ order }) {
  const [shipOpen, setShipOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);

  const phone = normalizePhoneID(order?.contact?.phone);
  const templates = buildTemplates(order);

  const openWa = (body) => {
    if (!phone) {
      alert("Nomor customer tidak valid.");
      return;
    }
    const url = `https://wa.me/${phone}?text=${encodeURIComponent(body)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handlePick = (tpl) => {
    if (tpl.needsInput) {
      setShipOpen(true);
      return;
    }
    openWa(tpl.body);
  };

  const copyTemplate = async (tpl) => {
    try {
      await navigator.clipboard.writeText(tpl.body);
      setCopiedKey(tpl.key);
      setTimeout(() => setCopiedKey(null), 1200);
    } catch {
      /* ignore */
    }
  };

  const disabled = !phone;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            data-testid={`wa-quick-btn-${order?.id || order?.order_number}`}
            disabled={disabled}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-[hsla(142,70%,45%,0.15)] border border-[hsla(142,70%,45%,0.4)] text-[hsl(142,70%,60%)] text-xs font-semibold hover:bg-[hsla(142,70%,45%,0.25)] disabled:opacity-30 disabled:cursor-not-allowed transition"
            title={disabled ? "Nomor tidak valid" : "Kirim WA ke customer"}
          >
            <MessageCircle className="w-3.5 h-3.5" />
            WA
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          className="bg-[hsl(var(--reef-mid))] border-[hsla(174,70%,55%,0.3)] text-[hsl(var(--reef-foam))] min-w-[240px]"
        >
          <DropdownMenuLabel className="text-xs opacity-60 font-normal">
            Kirim ke {order?.contact?.name?.split(" ")[0] || "customer"}
            <div className="font-mono text-[10px] opacity-70 mt-0.5">+{phone || "???"}</div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator className="bg-[hsla(174,70%,55%,0.15)]" />
          {templates.map((tpl) => (
            <DropdownMenuItem
              key={tpl.key}
              data-testid={`wa-tpl-${tpl.key}`}
              onClick={() => handlePick(tpl)}
              className="cursor-pointer hover:bg-[hsla(174,70%,55%,0.1)] focus:bg-[hsla(174,70%,55%,0.1)] flex items-center justify-between gap-3"
            >
              <span>{tpl.label}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  copyTemplate(tpl);
                }}
                className="opacity-40 hover:opacity-100"
                title="Salin template"
                data-testid={`wa-copy-${tpl.key}`}
              >
                {copiedKey === tpl.key ? (
                  <Check className="w-3 h-3 text-[hsl(var(--reef-glow))]" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
              </button>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <ShippingTemplateDialog
        open={shipOpen}
        onOpenChange={setShipOpen}
        onConfirm={(body) => {
          setShipOpen(false);
          openWa(body);
        }}
        template={templates.find((t) => t.needsInput)}
      />
    </>
  );
}
