import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import { useCart, formatRupiah } from "../lib/cart";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "../components/ui/radio-group";
import { ChevronLeft, MessageCircle, ShoppingBag, Gift, X, CreditCard } from "lucide-react";
import { toast } from "sonner";
import { trackInitiateCheckout, trackLead } from "../lib/tracker";
import { getVoucher, clearVoucher, VOUCHER_VALUE } from "../lib/voucher";
import { paySnap } from "../lib/midtrans";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MIN_VOUCHER_SUBTOTAL = 100000;

export default function Checkout() {
  const navigate = useNavigate();
  const { items, subtotal, clear } = useCart();
  const [submitting, setSubmitting] = useState(false);
  const [voucher, setVoucher] = useState(getVoucher());
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    address: "",
    city: "",
    kecamatan: "",
    notes: "",
  });
  const [channel, setChannel] = useState("midtrans");
  const [shippingRates, setShippingRates] = useState([]);
  const [shippingCourier, setShippingCourier] = useState("");
  const [shippingLoading, setShippingLoading] = useState(false);

  useEffect(() => {
    const sync = () => setVoucher(getVoucher());
    window.addEventListener("rimpods:voucher", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("rimpods:voucher", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  // Fetch shipping rates whenever city changes (debounced)
  useEffect(() => {
    const c = (form.city || "").trim();
    if (c.length < 3) {
      setShippingRates([]);
      setShippingCourier("");
      return;
    }
    const t = setTimeout(async () => {
      setShippingLoading(true);
      try {
        const params = new URLSearchParams({ city: c, kecamatan: form.kecamatan || "", address: form.address || "" });
        const { data } = await axios.get(`${API}/shipping/rates?${params.toString()}`);
        setShippingRates(data.rates || []);
        if (data.rates?.length && !shippingCourier) {
          // Default to cheapest courier (sorted asc by cost)
          const cheapest = [...data.rates].sort((a, b) => a.cost - b.cost)[0];
          setShippingCourier(cheapest.courier);
        }
      } catch (err) {
        console.error("shipping rates error", err);
        setShippingRates([]);
      } finally {
        setShippingLoading(false);
      }
    }, 400);
    return () => clearTimeout(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.city, form.kecamatan]);

  const chosenRate = shippingRates.find((r) => r.courier === shippingCourier);
  const shipping = chosenRate?.cost || 0;
  const voucherEligible = !!voucher && subtotal >= MIN_VOUCHER_SUBTOTAL;
  const discount = voucherEligible ? Math.min(VOUCHER_VALUE, subtotal) : 0;
  const total = Math.max(0, subtotal - discount + shipping);

  useEffect(() => {
    if (items.length > 0) trackInitiateCheckout(items, total);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setF = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (items.length === 0) {
      toast.error("Keranjang kamu masih kosong.");
      return;
    }
    if (!form.name || !form.phone || !form.address || !form.city || !form.kecamatan) {
      toast.error("Mohon lengkapi nama, nomor, alamat, kota, dan kecamatan.");
      return;
    }
    if (!shippingCourier) {
      toast.error("Silakan pilih kurir pengiriman terlebih dahulu.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        contact: form,
        payment_channel: channel,
        voucher_code: voucherEligible ? voucher : null,
        shipping_courier: shippingCourier,
      };
      const { data } = await axios.post(`${API}/orders`, payload);
      const orderInfo = {
        order_number: data.order_number,
        whatsapp_url: data.whatsapp_url,
        tokopedia_url: data.tokopedia_url,
        items: data.items,
        total: data.total,
        channel,
      };
      sessionStorage.setItem("rimpods_last_order", JSON.stringify(orderInfo));
      trackLead(data);

      // Midtrans path: fetch snap token then open popup
      if (channel === "midtrans") {
        try {
          const { data: snap } = await axios.post(`${API}/payment/midtrans/snap-token`, {
            order_id: data.id,
          });
          const res = await paySnap(snap.token, {
            onSuccess: () => toast.success("Pembayaran berhasil!"),
            onPending: () => toast.info("Menunggu pembayaran — cek email atau aplikasi bank kamu."),
            onError: () => toast.error("Pembayaran gagal — silakan coba lagi."),
          });
          if (res.outcome === "closed") {
            toast.info("Kamu bisa melanjutkan pembayaran dari halaman order.");
          }
          orderInfo.midtrans_token = snap.token;
          orderInfo.midtrans_redirect_url = snap.redirect_url;
          sessionStorage.setItem("rimpods_last_order", JSON.stringify(orderInfo));
          clear();
          if (voucherEligible) clearVoucher();
          navigate("/sukses");
          return;
        } catch (err) {
          console.error("Midtrans error:", err);
          toast.error("Gagal membuka pembayaran Midtrans. Silakan pilih metode lain.");
          setSubmitting(false);
          return;
        }
      }

      clear();
      if (voucherEligible) clearVoucher();
      navigate("/sukses");
    } catch (err) {
      toast.error("Pesanan belum berhasil diproses. Mohon dicoba kembali.");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="reef-grad min-h-screen text-[hsl(var(--reef-foam))]">
      <Header onCartClick={() => navigate("/checkout")} />
      <main className="max-w-6xl mx-auto px-5 lg:px-10 py-10">
        <Link to="/" className="inline-flex items-center text-sm opacity-70 hover:opacity-100 mb-6" data-testid="back-home-link">
          <ChevronLeft className="w-4 h-4 mr-1" /> Lanjutkan belanja
        </Link>

        <h1 className="font-display text-4xl lg:text-5xl tracking-tight">Checkout</h1>
        <p className="mt-2 opacity-70">Mohon lengkapi data pengiriman — kami akan meneruskan detail pesanan kamu ke WhatsApp atau Tokopedia.</p>

        {items.length === 0 ? (
          <div className="mt-12 glass-card rounded-2xl p-10 text-center">
            <ShoppingBag className="w-10 h-10 mx-auto opacity-50" />
            <p className="font-display text-2xl mt-4">Keranjang kamu masih kosong.</p>
            <Link to="/" className="mt-4 inline-block">
              <Button data-testid="goto-shop-btn" className="coral-pill mt-4 rounded-full h-12 px-6">Mulai Belanja</Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-10 grid lg:grid-cols-3 gap-8" data-testid="checkout-form">
            <div className="lg:col-span-2 space-y-6">
              <section className="glass-card rounded-2xl p-6">
                <h2 className="font-display text-2xl mb-4">Data Pengiriman</h2>
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="Nama Lengkap" testid="input-name">
                    <Input data-testid="input-name" required value={form.name} onChange={setF("name")} placeholder="Nama lengkap kamu" className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <Field label="No WhatsApp" testid="input-phone">
                    <Input data-testid="input-phone" required value={form.phone} onChange={setF("phone")} placeholder="0812..." className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <Field label="Email (opsional)" testid="input-email">
                    <Input data-testid="input-email" type="email" value={form.email} onChange={setF("email")} placeholder="email@domain.com" className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <Field label="Kota" testid="input-city">
                    <Input data-testid="input-city" required value={form.city} onChange={setF("city")} placeholder="Jakarta / Surabaya / ..." className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <Field label="Kecamatan" testid="input-kecamatan">
                    <Input data-testid="input-kecamatan" required value={form.kecamatan} onChange={setF("kecamatan")} placeholder="Setiabudi / Tegalsari / ..." className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                  </Field>
                  <div className="sm:col-span-2">
                    <Field label="Alamat Lengkap" testid="input-address">
                      <Textarea data-testid="input-address" required value={form.address} onChange={setF("address")} placeholder="Jl. ..., RT/RW, Kelurahan, Kode Pos" rows={3} className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                    </Field>
                  </div>
                  <div className="sm:col-span-2">
                    <Field label="Catatan untuk Admin (opsional)" testid="input-notes">
                      <Textarea data-testid="input-notes" value={form.notes} onChange={setF("notes")} placeholder="Volume tank, jenis coral, permintaan packing khusus, dan catatan lain." rows={2} className="bg-[hsla(192,55%,22%,0.4)] border-[hsla(174,70%,55%,0.25)]" />
                    </Field>
                  </div>
                </div>
              </section>

              <section className="glass-card rounded-2xl p-6" data-testid="shipping-section">
                <h2 className="font-display text-2xl mb-2">Pilih Kurir Pengiriman</h2>
                <p className="text-sm opacity-70 mb-4">
                  Tarif ongkir disesuaikan dengan kota & kecamatan kamu. Pilih salah satu kurir di bawah.
                </p>
                {(!form.city || form.city.trim().length < 3) ? (
                  <div className="text-sm opacity-60 p-3 bg-[hsla(192,55%,22%,0.4)] rounded-lg border border-[hsla(174,70%,55%,0.15)]" data-testid="shipping-empty">
                    Mohon isi <b>Kota</b> dulu untuk melihat opsi kurir.
                  </div>
                ) : shippingLoading ? (
                  <div className="text-sm opacity-60 p-3" data-testid="shipping-loading">Menghitung ongkir…</div>
                ) : shippingRates.length === 0 ? (
                  <div className="text-sm text-[hsl(var(--reef-coral))] p-3">Tidak ada kurir tersedia untuk kota ini. Mohon hubungi admin via WhatsApp.</div>
                ) : (
                  <RadioGroup value={shippingCourier} onValueChange={setShippingCourier} className="space-y-3" data-testid="shipping-courier-group">
                    {shippingRates.map((r) => (
                      <label
                        key={r.courier}
                        htmlFor={`courier-${r.courier}`}
                        data-testid={`shipping-courier-${r.courier.toLowerCase()}`}
                        className={`flex items-center gap-4 cursor-pointer border rounded-xl p-4 transition ${
                          shippingCourier === r.courier
                            ? "border-[hsl(var(--reef-glow))] bg-[hsla(49,212,196,0.06)]"
                            : "border-[hsla(174,70%,55%,0.2)] hover:border-[hsla(174,70%,55%,0.4)]"
                        }`}
                      >
                        <RadioGroupItem id={`courier-${r.courier}`} value={r.courier} className="border-[hsla(174,70%,55%,0.5)]" />
                        <div className="flex-1 flex items-center justify-between gap-3">
                          <div>
                            <div className="font-display text-lg">{r.courier} <span className="text-xs opacity-60 font-sans font-normal">· {r.service}</span></div>
                            <div className="text-xs opacity-70 mt-0.5">Estimasi: {r.etd}</div>
                          </div>
                          <div className="text-right font-semibold text-[hsl(var(--reef-glow))]">
                            {formatRupiah(r.cost)}
                          </div>
                        </div>
                      </label>
                    ))}
                  </RadioGroup>
                )}
              </section>

              <section className="glass-card rounded-2xl p-6">
                <h2 className="font-display text-2xl mb-4">Metode Pembayaran</h2>
                <RadioGroup value={channel} onValueChange={setChannel} className="space-y-3" data-testid="payment-channel">
                  <ChannelOption value="midtrans" label="Bayar Sekarang (Midtrans)" desc="Pembayaran instan via BCA, Mandiri, BNI, BRI, CIMB, BSI (Virtual Account), QRIS, GoPay, OVO, DANA, ShopeePay, atau kartu kredit dengan cicilan 0%." current={channel} />
                  <ChannelOption value="whatsapp" label="Konfirmasi via WhatsApp" desc="Detail pesanan akan kami teruskan langsung ke admin Rimpods — pembayaran dilakukan melalui transfer manual." current={channel} />
                  <ChannelOption value="tokopedia" label="Lanjutkan di Tokopedia" desc="Kamu akan diarahkan ke listing Tokopedia untuk menyelesaikan pembayaran dengan metode resmi (cicilan 0%, COD, dan lainnya)." current={channel} />
                </RadioGroup>
              </section>
            </div>

            <aside className="space-y-4 lg:sticky lg:top-24 self-start">
              <section className="glass-card rounded-2xl p-6">
                <h2 className="font-display text-2xl mb-4">Ringkasan Pesanan</h2>
                <ul className="space-y-3" data-testid="order-summary">
                  {items.map((i) => (
                    <li key={i.product_id} className="flex gap-3 text-sm">
                      <img src={i.image} alt={i.name} className="w-14 h-14 rounded-lg object-cover" />
                      <div className="flex-1">
                        <div className="line-clamp-2">{i.name}</div>
                        <div className="opacity-60 text-xs">{i.quantity} × {formatRupiah(i.price)}</div>
                      </div>
                      <div className="font-medium">{formatRupiah(i.price * i.quantity)}</div>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 pt-4 border-t border-[hsla(174,70%,55%,0.15)] space-y-2 text-sm">
                  <Row k="Subtotal" v={formatRupiah(subtotal)} />
                  <Row
                    k={chosenRate ? `Pengiriman (${chosenRate.courier} ${chosenRate.service})` : "Pengiriman"}
                    v={chosenRate ? formatRupiah(shipping) : "Pilih kurir dulu"}
                  />
                  {voucher && (
                    <div className={`flex items-start gap-2 text-xs p-2.5 rounded-lg ${voucherEligible ? "bg-[hsla(174,70%,55%,0.1)] border border-[hsla(174,70%,55%,0.25)]" : "bg-[hsla(8,89%,64%,0.1)] border border-[hsla(8,89%,64%,0.25)]"}`} data-testid="voucher-banner">
                      <Gift className={`w-4 h-4 mt-0.5 flex-shrink-0 ${voucherEligible ? "text-[hsl(var(--reef-glow))]" : "text-[hsl(var(--reef-coral))]"}`} />
                      <div className="flex-1">
                        <div className="font-semibold">
                          Voucher <span className="font-mono">{voucher}</span>
                        </div>
                        <div className="opacity-70 text-[11px] mt-0.5">
                          {voucherEligible
                            ? `Selamat, kamu hemat ${formatRupiah(discount)} pada pesanan ini.`
                            : `Minimum belanja ${formatRupiah(MIN_VOUCHER_SUBTOTAL)} agar voucher aktif.`}
                        </div>
                      </div>
                      <button
                        type="button"
                        data-testid="voucher-remove"
                        onClick={() => { clearVoucher(); setVoucher(null); }}
                        className="opacity-50 hover:opacity-100 p-0.5"
                        aria-label="Hapus voucher"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                  {voucherEligible && (
                    <Row k={`Diskon Voucher`} v={`-${formatRupiah(discount)}`} />
                  )}
                  <Row k="Total" v={formatRupiah(total)} bold testId="summary-total" />
                </div>
                <Button
                  type="submit"
                  data-testid="place-order-btn"
                  disabled={submitting}
                  className="w-full mt-5 coral-pill hover:opacity-90 h-12 rounded-full font-semibold"
                >
                  {submitting
                    ? "Memproses..."
                    : channel === "whatsapp"
                      ? "Konfirmasi via WhatsApp"
                      : channel === "midtrans"
                        ? "Bayar Sekarang"
                        : "Lanjutkan ke Tokopedia"}
                  {channel === "whatsapp" && <MessageCircle className="w-4 h-4 ml-2" />}
                  {channel === "midtrans" && <CreditCard className="w-4 h-4 ml-2" />}
                </Button>
                <p className="text-[11px] mt-3 opacity-60 text-center">
                  Dengan menekan tombol ini, kamu menyetujui detail pesanan dikirim ke admin Rimpods.
                </p>
              </section>
            </aside>
          </form>
        )}
      </main>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <Label className="text-xs uppercase tracking-wider opacity-70 mb-2 block">{label}</Label>
      {children}
    </div>
  );
}

function Row({ k, v, bold, testId }) {
  return (
    <div className={`flex justify-between ${bold ? "text-base pt-2" : ""}`}>
      <span className={bold ? "font-semibold" : "opacity-70"}>{k}</span>
      <span data-testid={testId} className={bold ? "font-display text-xl text-[hsl(var(--reef-glow))]" : ""}>{v}</span>
    </div>
  );
}

function ChannelOption({ value, label, desc, current }) {
  const active = value === current;
  return (
    <label
      data-testid={`channel-${value}`}
      className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition ${active ? "border-[hsl(var(--reef-glow))] bg-[hsla(174,70%,55%,0.08)]" : "border-[hsla(174,70%,55%,0.2)] hover:border-[hsla(174,70%,55%,0.4)]"}`}
    >
      <RadioGroupItem value={value} className="mt-1 border-[hsla(174,70%,55%,0.5)]" />
      <div>
        <div className="font-medium">{label}</div>
        <div className="text-sm opacity-70">{desc}</div>
      </div>
    </label>
  );
}
