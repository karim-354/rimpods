import { useEffect, useState } from "react";
import axios from "axios";
import { Button } from "../ui/button";
import { Star, Trash2, Eye, EyeOff, Plus } from "lucide-react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const EMPTY = { name: "", text: "", product: "", date_label: "Baru saja", rating: 5 };

export const TestimonialsManager = () => {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const { data } = await axios.get(`${API}/admin/testimonials`, { withCredentials: true });
      setItems(data.testimonials || []);
    } catch (e) {
      console.error(e);
    }
  };
  useEffect(() => { load(); }, []);

  const toggleVisible = async (t) => {
    await axios.put(`${API}/admin/testimonials/${t.id}`, { visible: !t.visible }, { withCredentials: true });
    toast.success(t.visible ? "Testimoni disembunyikan" : "Testimoni ditampilkan");
    load();
  };

  const remove = async (t) => {
    if (!window.confirm(`Hapus testimoni dari ${t.name}?`)) return;
    await axios.delete(`${API}/admin/testimonials/${t.id}`, { withCredentials: true });
    toast.success("Testimoni dihapus");
    load();
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.text.trim()) return toast.error("Nama dan isi ulasan wajib diisi");
    setSaving(true);
    try {
      await axios.post(`${API}/admin/testimonials`, form, { withCredentials: true });
      toast.success("Testimoni ditambahkan");
      setForm(EMPTY);
      setShowForm(false);
      load();
    } catch (err) {
      toast.error("Gagal menyimpan");
    } finally {
      setSaving(false);
    }
  };

  const inputCls = "w-full bg-[hsla(198,75%,8%,0.5)] border border-[hsla(174,70%,55%,0.25)] rounded-xl px-4 py-2.5 text-sm outline-none focus:border-[hsla(174,70%,55%,0.6)]";

  return (
    <section className="mt-10" data-testid="admin-testimonials-section">
      <div className="flex items-end justify-between mb-4">
        <div>
          <h2 className="font-display text-2xl">Wall of Reefs — Testimoni</h2>
          <p className="text-xs opacity-60 mt-1">
            {items.filter((t) => t.visible).length} tampil dari {items.length} total · halaman publik: <a href="/testimoni" target="_blank" rel="noreferrer" className="text-[hsl(var(--reef-glow))] hover:underline">/testimoni</a>
          </p>
        </div>
        <Button
          data-testid="admin-testi-add-btn"
          onClick={() => setShowForm((v) => !v)}
          size="sm"
          className="coral-pill hover:opacity-90 rounded-full"
        >
          <Plus className="w-4 h-4 mr-1" /> Tambah
        </Button>
      </div>

      {showForm && (
        <form onSubmit={submit} className="glass-card rounded-2xl p-6 mb-5 grid sm:grid-cols-2 gap-3" data-testid="admin-testi-form">
          <input className={inputCls} placeholder="Nama pembeli" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="admin-testi-name" />
          <input className={inputCls} placeholder="Produk (opsional)" value={form.product}
            onChange={(e) => setForm({ ...form, product: e.target.value })} data-testid="admin-testi-product" />
          <textarea className={`${inputCls} sm:col-span-2`} rows={3} placeholder="Isi ulasan" value={form.text}
            onChange={(e) => setForm({ ...form, text: e.target.value })} data-testid="admin-testi-text" />
          <input className={inputCls} placeholder='Label waktu (mis. "2 hari lalu")' value={form.date_label}
            onChange={(e) => setForm({ ...form, date_label: e.target.value })} data-testid="admin-testi-date" />
          <div className="flex items-center gap-3">
            <select className={inputCls} value={form.rating}
              onChange={(e) => setForm({ ...form, rating: Number(e.target.value) })} data-testid="admin-testi-rating">
              {[5, 4, 3].map((r) => <option key={r} value={r}>{r} bintang</option>)}
            </select>
            <Button type="submit" disabled={saving} className="coral-pill hover:opacity-90 rounded-full h-10 px-6" data-testid="admin-testi-submit">
              {saving ? "Menyimpan..." : "Simpan"}
            </Button>
          </div>
        </form>
      )}

      <div className="glass-card rounded-2xl divide-y divide-[hsla(174,70%,55%,0.1)] max-h-[480px] overflow-y-auto" data-testid="admin-testi-list">
        {items.map((t) => (
          <div key={t.id} className={`px-5 py-4 flex items-start gap-4 ${t.visible ? "" : "opacity-40"}`}>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-sm font-semibold">
                {t.name}
                <span className="flex">
                  {Array.from({ length: t.rating || 5 }).map((_, k) => (
                    <Star key={k} className="w-3 h-3 fill-[hsl(var(--reef-glow))] text-[hsl(var(--reef-glow))]" />
                  ))}
                </span>
                {t.photos?.length > 0 && <span className="text-[10px] opacity-60">📷 {t.photos.length}</span>}
              </div>
              <p className="text-xs opacity-75 mt-1 line-clamp-2">{t.text}</p>
              <div className="text-[10px] opacity-50 mt-1">{t.product} · {t.date_label} · {t.source}</div>
            </div>
            <div className="flex gap-1 shrink-0">
              <Button size="sm" variant="ghost" onClick={() => toggleVisible(t)}
                className="text-[hsl(var(--reef-foam))]/70 hover:text-[hsl(var(--reef-foam))] hover:bg-transparent h-8 w-8 p-0"
                data-testid={`admin-testi-toggle-${t.id}`}>
                {t.visible ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => remove(t)}
                className="text-red-400/70 hover:text-red-400 hover:bg-transparent h-8 w-8 p-0"
                data-testid={`admin-testi-delete-${t.id}`}>
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
