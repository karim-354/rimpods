import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./ui/dialog";
import { Button } from "./ui/button";
import { Gift, X, Copy, Check } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  saveVoucher,
  exitIntentSeen,
  markExitIntentSeen,
  VOUCHER_CODE,
  VOUCHER_VALUE,
  getVoucher,
} from "../lib/voucher";
import { formatRupiah } from "../lib/cart";

export default function ExitIntentModal() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const armedRef = useRef(false);

  useEffect(() => {
    // Skip if user already saw the offer this session or already has voucher saved
    if (exitIntentSeen() || getVoucher()) return;

    // Arm after 4s so we don't popup before user explores
    const armTimer = setTimeout(() => {
      armedRef.current = true;
    }, 4000);

    const onLeave = (e) => {
      if (!armedRef.current) return;
      // Trigger only when mouse exits top of viewport (going to URL bar / close tab)
      if (e.clientY <= 0 && !e.relatedTarget) {
        armedRef.current = false;
        markExitIntentSeen();
        setOpen(true);
      }
    };

    // Mobile fallback: trigger after 25s of active scrolling without voucher saved
    const onMobileTimeout = setTimeout(() => {
      if (!armedRef.current || window.innerWidth > 768) return;
      armedRef.current = false;
      markExitIntentSeen();
      setOpen(true);
    }, 25000);

    document.addEventListener("mouseout", onLeave);
    return () => {
      clearTimeout(armTimer);
      clearTimeout(onMobileTimeout);
      document.removeEventListener("mouseout", onLeave);
    };
  }, []);

  const claim = () => {
    saveVoucher(VOUCHER_CODE);
    toast.success(`Voucher ${VOUCHER_CODE} aktif! Diskon otomatis di checkout.`);
    setOpen(false);
  };

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(VOUCHER_CODE);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* noop */
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        data-testid="exit-intent-modal"
        className="bg-[hsl(var(--reef-mid))] border-[hsla(174,70%,55%,0.35)] text-[hsl(var(--reef-foam))] sm:max-w-md p-0 overflow-hidden"
      >
        <div className="absolute top-3 right-3 z-10">
          <button
            data-testid="exit-intent-close"
            onClick={() => setOpen(false)}
            className="w-8 h-8 grid place-items-center rounded-full bg-[hsla(198,75%,8%,0.7)] hover:bg-[hsla(198,75%,8%,0.9)]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-8">
          <div className="w-14 h-14 rounded-2xl bg-[hsla(8,89%,64%,0.15)] grid place-items-center mb-5">
            <Gift className="w-7 h-7 text-[hsl(var(--reef-coral))]" />
          </div>

          <DialogHeader>
            <DialogTitle className="font-display text-3xl leading-tight text-left">
              Eits, jangan cabut dulu!
            </DialogTitle>
            <DialogDescription className="text-[hsl(var(--reef-foam))]/75 text-left mt-2 text-base">
              Khusus buat reefer yang pertama kali mampir, ada voucher{" "}
              <b className="text-[hsl(var(--reef-glow))]">{formatRupiah(VOUCHER_VALUE)}</b> buat order pertama kamu.
            </DialogDescription>
          </DialogHeader>

          <button
            onClick={copyCode}
            data-testid="exit-intent-copy-code"
            className="mt-6 w-full group flex items-center justify-between gap-3 p-4 rounded-2xl bg-[hsla(192,55%,22%,0.6)] border border-dashed border-[hsla(174,70%,55%,0.4)] hover:border-[hsl(var(--reef-glow))] transition"
          >
            <div className="text-left">
              <div className="text-xs uppercase tracking-widest opacity-60 mb-1">Kode voucher</div>
              <div className="font-mono font-bold text-2xl text-[hsl(var(--reef-glow))] tracking-wider">
                {VOUCHER_CODE}
              </div>
            </div>
            <div className="flex items-center gap-1.5 text-xs opacity-70 group-hover:opacity-100">
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-[hsl(var(--reef-glow))]" /> Tersalin
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" /> Salin
                </>
              )}
            </div>
          </button>

          <Button
            data-testid="exit-intent-claim"
            onClick={claim}
            className="coral-pill hover:opacity-90 h-12 rounded-full font-semibold w-full mt-5"
          >
            Pakai Voucher & Belanja Sekarang
          </Button>
          <button
            data-testid="exit-intent-decline"
            onClick={() => setOpen(false)}
            className="w-full mt-2 text-xs opacity-50 hover:opacity-80 py-2"
          >
            Nggak usah, lain kali aja
          </button>

          <p className="mt-4 text-[11px] opacity-50 text-center leading-relaxed">
            Berlaku 1× per customer, min. order Rp100.000. Otomatis diskon di checkout.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
