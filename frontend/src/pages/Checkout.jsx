import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import { useCart, formatRupiah } from "../lib/cart";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "../components/ui/radio-group";
import { ChevronLeft, ShoppingBag, CreditCard, MessageCircle } from "lucide-react";
import { toast } from "sonner";
import { saveReturningCustomer } from "../lib/customer";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Checkout() {
  const navigate = useNavigate();
  const { items, subtotal, clear } = useCart();
  const [submitting, setSubmitting] = useState(false);
  const [keyword, setKeyword] = useState("");
  const [selectedKeyword, setSelectedKeyword] = useState("");
  const [areaResults, setAreaResults] = useState([]);
  const [channel, setChannel] = useState("midtrans");
  const [shippingRates, setShippingRates] = useState([]);
  const [shippingCourier, setShippingCourier] = useState("");
  const [shippingLoading, setShippingLoading] = useState(false);

  const [form, setForm] = useState({
    name: "", phone: "", email: "pelanggan@rimpods.com", address: "", city: "", kecamatan: "", notes: "", postalCode: "", latitude: "", longitude: ""
  });

  const handlePhoneBlur = async () => {
    if (form.phone.length < 10) return;
    try {
      const { data } = await axios.get(`${API}/customer/lookup?phone=${form.phone}`);
      if (data.found && data.contact) {
        toast.success("Selamat datang kembali! Alamat kirim otomatis diterapkan.");
        saveReturningCustomer(data.contact.name, form.phone);
        setForm({
          ...form,
          name: data.contact.name || "",
          email: data.contact.email || "pelanggan@rimpods.com",
          address: data.contact.address || "",
          city: data.contact.city || "",
          kecamatan: data.contact.kecamatan || "",
          postalCode: String(data.contact.postalCode || ""),
          latitude: data.contact.latitude || "",
          longitude: data.contact.longitude || ""
        });
        const fullKeyword = `${data.contact.kecamatan}, ${data.contact.city}`;
        setKeyword(fullKeyword);
        setSelectedKeyword(fullKeyword);
      }
    } catch (err) {
      console.log("Pelanggan baru terdeteksi.");
    }
  };

  useEffect(() => {
    if (keyword.length < 3 || keyword === selectedKeyword) {
      setAreaResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const { data } = await axios.get(`${API}/shipping/search-area?query=${keyword}`);
        setAreaResults(data.areas || []);
      } catch (err) {
        console.error("Gagal menarik area logistik.", err);
      }
    }, 500);
    return () => clearTimeout(t);
  }, [keyword, selectedKeyword]);

  useEffect(() => {
    if (!form.postalCode) {
      setShippingRates([]);
      setShippingCourier("");
      return;
    }
    const fetchRates = async () => {
      setShippingLoading(true);
      try {
        const payload = {
          items: items.map(i => ({ product_id: i.product_id, quantity: i.quantity, name: i.name, price: i.price })),
          postalCode: form.postalCode,
          latitude: form.latitude,
          longitude: form.longitude
        };
        const { data } = await axios.post(`${API}/shipping/rates`, payload);
        setShippingRates(data.rates || []);
        if (data.rates?.length) {
          const cheapest = [...data.rates].sort((a, b) => a.cost - b.cost)[0];
          setShippingCourier(cheapest.id);
        }
      } catch (err) {
        console.error("Gagal sinkronisasi ongkir.", err);
        setShippingRates([]);
      } finally {
        setShippingLoading(false);
      }
    };
    fetchRates();
  }, [form.postalCode, form.latitude, items]);

  const chosenRate = shippingRates.find((r) => r.id === shippingCourier);
  const shipping = chosenRate?.cost || 0;
  const total = Math.max(0, subtotal + shipping);

  const submit = async (e) => {
    e.preventDefault();
    if (items.length === 0) return toast.error("Keranjang kosong.");
    if (!form.name || !form.phone || !form.address || !form.postalCode) {
      return toast.error("Mohon lengkapi alamat dan pilih wilayah kecamatan Anda.");
    }
    if (!shippingCourier) return toast.error("Pilih layanan kurir pengiriman.");

    setSubmitting(true);
    try {
      const payload = {
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity, name: i.name, price: i.price })),
        contact: form,
        payment_channel: channel,
        shipping_courier: shippingCourier
      };
      
      const { data } = await axios.post(`${API}/orders`, payload);
      // Ingat pelanggan ini untuk sapaan personal di kunjungan berikutnya
      saveReturningCustomer(form.name, form.phone);

      if (channel === "midtrans") {
        if (!window.snap) {
            toast.error("Sistem kasir Midtrans belum termuat sempurna. Refresh halaman.");
            setSubmitting(false);
            return;
        }
        const tokenRes = await axios.post(`${API}/payment/midtrans/snap-token`, { order_id: data.id });
        window.snap.pay(tokenRes.data.token, {
          onSuccess: () => { toast.success("Pembayaran berhasil!"); clear(); navigate("/sukses"); },
          onPending: () => { toast.info("Menunggu penyelesaian pembayaran."); clear(); navigate("/sukses"); },
          onError: () => { toast.error("Pembayaran gagal."); setSubmitting(false); }
        });
      } else {
        window.open(data.whatsapp_url, "_blank");
        clear();
        navigate("/sukses");
      }
    } catch (err) {
      toast.error("Gagal memproses pesanan.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <Header onCartClick={() => navigate("/checkout")} />
      <div className="max-w-4xl mx-auto p-4 grid md:grid-cols-2 gap-6 pt-24">
        
        <form onSubmit={submit} className="space-y-4 bg-slate-900 p-6 rounded-2xl border border-slate-800">
          <h2 className="text-xl font-bold tracking-tight">Data Pengiriman</h2>
          
          <div className="space-y-2">
            <Label>No WhatsApp</Label>
            <Input required value={form.phone} onBlur={handlePhoneBlur} onChange={(e) => setForm({...form, phone: e.target.value})} placeholder="Contoh: 08221659..." className="bg-slate-950 text-white" />
          </div>

          <div className="space-y-2">
            <Label>Nama Lengkap</Label>
            <Input required value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} placeholder="Nama Penerima" className="bg-slate-950 text-white" />
          </div>

          <div className="space-y-2 relative">
            <Label>Kecamatan / Kota</Label>
            <Input required value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Ketik nama kecamatan tempat tinggal Anda..." className="bg-slate-950 text-white" />
            
            {areaResults.length > 0 && (
              <ul className="absolute z-50 w-full bg-slate-900 border border-slate-700 max-h-48 overflow-y-auto rounded-lg shadow-xl top-full left-0 mt-1">
                {areaResults.map((area) => {
                  const nameStr = area.name || "";
                  const cityStr = area.administrative_division_level_2 || "";
                  const postStr = area.postal_code || "00000";
                  return (
                    <li 
                      key={area.id} 
                      onMouseDown={(e) => {
                        e.preventDefault();
                        const mergedText = `${nameStr}, ${cityStr}`;
                        setSelectedKeyword(mergedText);
                        setKeyword(mergedText);
                        setForm({
                          ...form,
                          kecamatan: nameStr,
                          city: cityStr,
                          postalCode: String(postStr),
                          latitude: area.latitude ? String(area.latitude) : "",
                          longitude: area.longitude ? String(area.longitude) : ""
                        });
                        setAreaResults([]);
                      }}
                      className="p-3 border-b border-slate-800 hover:bg-slate-800 cursor-pointer text-sm text-slate-200"
                    >
                      {nameStr}, {cityStr} • <span className="text-blue-400">Pos: {postStr}</span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="space-y-2">
            <Label>Alamat Lengkap</Label>
            <Textarea required value={form.address} onChange={(e) => setForm({...form, address: e.target.value})} placeholder="Nama jalan, nomor rumah, RT/RW, blok, patokan" className="bg-slate-950 text-white" />
          </div>

          <div className="space-y-2 pt-2">
            <Label className="font-bold text-base">Opsi Pengiriman</Label>
            {shippingLoading ? (
              <p className="text-sm text-slate-400 animate-pulse">Menghitung rute logistik...</p>
            ) : (
              <RadioGroup value={shippingCourier} onValueChange={setShippingCourier} className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {shippingRates.length === 0 && form.postalCode && (
                  <p className="text-xs text-amber-400">Kurir tidak ditemukan. Coba ketik ulang wilayah Anda.</p>
                )}
                {shippingRates.map((r) => (
                  <label key={r.id} className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition ${shippingCourier === r.id ? "border-blue-500 bg-slate-800" : "border-slate-800 bg-slate-950"}`}>
                    <div className="flex items-center gap-3">
                      <RadioGroupItem value={r.id} id={r.id} />
                      <div>
                        <p className="font-semibold text-sm">{r.courier} ({r.service})</p>
                        <p className="text-xs text-slate-400">Estimasi: {r.etd}</p>
                      </div>
                    </div>
                    <span className="font-bold text-sm text-blue-400">{formatRupiah(r.cost)}</span>
                  </label>
                ))}
              </RadioGroup>
            )}
          </div>

          <div className="space-y-2 pt-2">
            <Label>Metode Pembayaran</Label>
            <RadioGroup value={channel} onValueChange={setChannel} className="grid grid-cols-2 gap-2">
              <label className={`p-3 rounded-xl border cursor-pointer text-center ${channel === "midtrans" ? "border-blue-500 bg-slate-800" : "border-slate-800 bg-slate-950"}`}>
                <RadioGroupItem value="midtrans" className="sr-only" />
                <CreditCard className="mx-auto mb-1 h-5 w-5" />
                <span className="text-xs font-medium block">Automatic Gateway</span>
              </label>
              <label className={`p-3 rounded-xl border cursor-pointer text-center ${channel === "whatsapp" ? "border-blue-500 bg-slate-800" : "border-slate-800 bg-slate-950"}`}>
                <RadioGroupItem value="whatsapp" className="sr-only" />
                <MessageCircle className="mx-auto mb-1 h-5 w-5" />
                <span className="text-xs font-medium block">WhatsApp Admin</span>
              </label>
            </RadioGroup>
          </div>

          <Button type="submit" disabled={submitting || items.length === 0} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-12 rounded-xl mt-4">
            {submitting ? "Memproses..." : channel === "midtrans" ? "Bayar Sekarang (QRIS/GoPay/Bank)" : "Lanjutkan ke WhatsApp"}
          </Button>
        </form>

        <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 h-fit space-y-4">
          <h2 className="text-xl font-bold">Ringkasan Keranjang</h2>
          <div className="divide-y divide-slate-800">
            {items.map((item, idx) => (
              <div key={idx} className="py-3 flex justify-between text-sm">
                <div>
                  <p className="font-semibold text-slate-200">{item.name}</p>
                  <p className="text-xs text-slate-400">Kuantitas: {item.quantity}x</p>
                </div>
                <span className="font-medium text-slate-300">{formatRupiah(item.price * item.quantity)}</span>
              </div>
            ))}
          </div>
          <div className="border-t border-slate-800 pt-4 space-y-2 text-sm">
            <div className="flex justify-between opacity-70"><span>Subtotal Produk</span><span>{formatRupiah(subtotal)}</span></div>
            <div className="flex justify-between opacity-70"><span>Biaya Pengiriman</span><span>{formatRupiah(shipping)}</span></div>
            <div className="flex justify-between border-t border-slate-800 pt-3 text-base font-bold text-blue-400">
              <span>Total Tagihan</span><span>{formatRupiah(total)}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}