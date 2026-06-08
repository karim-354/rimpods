import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "./ui/sheet";
import { Button } from "./ui/button";
import { useCart, formatRupiah } from "../lib/cart";
import { Minus, Plus, Trash2, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function CartDrawer({ open, onOpenChange }) {
  const { items, setQty, remove, subtotal, shipping, total } = useCart();
  const navigate = useNavigate();

  const goCheckout = () => {
    onOpenChange(false);
    navigate("/checkout");
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        data-testid="cart-drawer"
        className="bg-[hsl(var(--reef-mid))] border-l border-[hsla(174,70%,55%,0.2)] text-[hsl(var(--reef-foam))] w-full sm:max-w-md overflow-y-auto"
      >
        <SheetHeader>
          <SheetTitle className="font-display text-2xl text-[hsl(var(--reef-foam))]">
            Keranjang Kamu
          </SheetTitle>
          <SheetDescription className="text-[hsl(var(--reef-foam))]/60">
            Pastikan pilihan kamu sudah tepat sebelum lanjut ke checkout.
          </SheetDescription>
        </SheetHeader>

        {items.length === 0 ? (
          <div data-testid="cart-empty" className="mt-12 text-center text-[hsl(var(--reef-foam))]/70">
            <p className="font-display text-xl">Keranjang kamu masih kosong.</p>
            <p className="text-sm mt-2">Silakan pilih pakan coral yang paling selaras dengan tank kamu.</p>
          </div>
        ) : (
          <div className="mt-6 space-y-4">
            {items.map((it) => (
              <div
                key={it.product_id}
                data-testid={`cart-item-${it.product_id}`}
                className="flex gap-3 p-3 rounded-2xl bg-[hsla(192,55%,22%,0.5)] border border-[hsla(174,70%,55%,0.15)]"
              >
                <img src={it.image} alt={it.name} loading="lazy" className="w-20 h-20 rounded-xl object-cover" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-snug line-clamp-2">{it.name}</p>
                  <p className="text-[hsl(var(--reef-glow))] font-semibold text-sm mt-1">
                    {formatRupiah(it.price)}
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <button
                      data-testid={`qty-minus-${it.product_id}`}
                      onClick={() => setQty(it.product_id, it.quantity - 1)}
                      className="w-7 h-7 grid place-items-center rounded-md border border-[hsla(174,70%,55%,0.3)] hover:bg-[hsla(174,70%,55%,0.1)]"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="w-8 text-center text-sm">{it.quantity}</span>
                    <button
                      data-testid={`qty-plus-${it.product_id}`}
                      onClick={() => setQty(it.product_id, it.quantity + 1)}
                      className="w-7 h-7 grid place-items-center rounded-md border border-[hsla(174,70%,55%,0.3)] hover:bg-[hsla(174,70%,55%,0.1)]"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                    <button
                      data-testid={`cart-remove-${it.product_id}`}
                      onClick={() => remove(it.product_id)}
                      className="ml-auto text-[hsl(var(--reef-coral))] hover:text-[hsl(var(--reef-coral-soft))]"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}

            <div className="pt-4 border-t border-[hsla(174,70%,55%,0.15)] space-y-2 text-sm">
              <div className="flex justify-between"><span className="opacity-70">Subtotal</span><span data-testid="cart-subtotal">{formatRupiah(subtotal)}</span></div>
              <div className="flex justify-between"><span className="opacity-70">Pengiriman</span><span className="opacity-60 italic">Pilih kurir di checkout</span></div>
              <div className="flex justify-between text-base pt-1">
                <span className="font-semibold">Total</span>
                <span data-testid="cart-total" className="font-display text-xl text-[hsl(var(--reef-glow))]">{formatRupiah(total)}</span>
              </div>
            </div>

            <Button
              data-testid="cart-checkout-btn"
              onClick={goCheckout}
              className="w-full coral-pill hover:opacity-90 h-12 rounded-full font-semibold text-base"
            >
              Lanjutkan ke Checkout <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <p className="text-[11px] text-center opacity-60">
              Pilih kurir & cek ongkir di halaman checkout.
            </p>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
