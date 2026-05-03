import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./ui/dialog";
import { Button } from "./ui/button";
import { Sparkles, X, Plus, Clock } from "lucide-react";
import { useCart, formatRupiah } from "../lib/cart";
import { trackAddToCart } from "../lib/tracker";
import { toast } from "sonner";
import { useEffect, useState } from "react";

const DISCOUNT = 0.10; // 10%
const COUNTDOWN_SEC = 600; // 10 menit
const TS_KEY = (id) => `rimpods_upsell_ts_${id}`;

export default function UpsellModal({ open, onOpenChange, target }) {
  const { add } = useCart();
  const [secLeft, setSecLeft] = useState(COUNTDOWN_SEC);

  useEffect(() => {
    if (!open || !target) return;
    // Persist a per-target start timestamp so closing/reopening doesn't reset urgency
    const key = TS_KEY(target.id);
    let startMs = Number(sessionStorage.getItem(key));
    if (!startMs || Number.isNaN(startMs)) {
      startMs = Date.now();
      sessionStorage.setItem(key, String(startMs));
    }
    const tick = () => {
      const elapsed = Math.floor((Date.now() - startMs) / 1000);
      setSecLeft(Math.max(0, COUNTDOWN_SEC - elapsed));
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [open, target]);

  if (!target) return null;

  const mm = String(Math.floor(secLeft / 60)).padStart(2, "0");
  const ss = String(secLeft % 60).padStart(2, "0");
  const expired = secLeft === 0;

  const discounted = Math.round(target.price * (1 - DISCOUNT));
  const saving = target.price - discounted;

  const accept = () => {
    const upsellProduct = {
      ...target,
      id: `${target.id}-bundle`,
      price: discounted,
      name: `${target.name} (Bundle -10%)`,
    };
    add(upsellProduct, 1);
    trackAddToCart(upsellProduct, 1);
    toast.success(`Bundle aktif. Kamu hemat ${formatRupiah(saving)}.`);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        data-testid="upsell-modal"
        className="bg-[hsl(var(--reef-mid))] border-[hsla(8,89%,64%,0.35)] text-[hsl(var(--reef-foam))] sm:max-w-md p-0 overflow-hidden"
      >
        <div className="absolute top-3 right-3 z-10">
          <button
            data-testid="upsell-close"
            onClick={() => onOpenChange(false)}
            className="w-8 h-8 grid place-items-center rounded-full bg-[hsla(198,75%,8%,0.7)] hover:bg-[hsla(198,75%,8%,0.9)]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="relative">
          <img src={target.image} alt={target.name} className="w-full h-44 object-cover" />
          <div className="absolute top-3 left-3 inline-flex items-center gap-1.5 coral-pill rounded-full px-3 py-1 text-xs font-bold">
            <Sparkles className="w-3 h-3" /> Rekomendasi dari Kami
          </div>
        </div>
        <div className="p-6">
          <DialogHeader>
            <DialogTitle className="font-display text-2xl leading-tight text-left">
              Izinkan kami melengkapinya.
            </DialogTitle>
            <DialogDescription className="text-[hsl(var(--reef-foam))]/75 text-left mt-2">
              Banyak reefer menambahkan <b className="text-[hsl(var(--reef-glow))]">{target.name.split("(")[0].trim()}</b> pada saat yang sama — kombinasinya memang selaras. Kami tawarkan selisih 10% khusus bila kamu menambahkannya sekarang.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-5 p-4 rounded-2xl bg-[hsla(192,55%,22%,0.5)] border border-[hsla(174,70%,55%,0.2)]">
            <div className="flex items-center justify-between mb-3 pb-3 border-b border-[hsla(174,70%,55%,0.15)]">
              <span className="text-xs uppercase tracking-widest opacity-60 inline-flex items-center gap-1.5">
                <Clock className="w-3 h-3" /> Penawaran berlaku selama
              </span>
              <span data-testid="upsell-countdown" className={`font-mono text-lg font-bold ${expired ? "text-red-400" : "text-[hsl(var(--reef-coral))]"}`}>
                {expired ? "Berakhir" : `${mm}:${ss}`}
              </span>
            </div>
            <div className="flex items-end justify-between">
              <div>
                <div className="text-xs uppercase tracking-widest opacity-60 mb-1">Harga Bundle</div>
                <div className="font-display text-3xl text-[hsl(var(--reef-glow))]">{formatRupiah(discounted)}</div>
                <div className="text-xs line-through opacity-50">{formatRupiah(target.price)}</div>
              </div>
              <div className="text-right">
                <div className="coral-pill rounded-full px-3 py-1 text-xs font-bold inline-block">Hemat {formatRupiah(saving)}</div>
              </div>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-2">
            <Button
              data-testid="upsell-accept"
              onClick={accept}
              disabled={expired}
              className="coral-pill hover:opacity-90 h-12 rounded-full font-semibold w-full disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Plus className="w-4 h-4 mr-1" /> {expired ? "Penawaran Berakhir" : "Ya, Lengkapi Paketnya"}
            </Button>
            <Button
              data-testid="upsell-decline"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              className="h-10 text-[hsl(var(--reef-foam))]/60 hover:text-[hsl(var(--reef-foam))] hover:bg-transparent w-full"
            >
              Tidak perlu, lanjut checkout
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
