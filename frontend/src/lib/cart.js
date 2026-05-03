import { useEffect, useState, useCallback } from "react";

const KEY = "rimpods_cart_v1";

export const formatRupiah = (n) =>
  "Rp" + Math.round(n).toLocaleString("id-ID");

const read = () => {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

const write = (items) => {
  localStorage.setItem(KEY, JSON.stringify(items));
  window.dispatchEvent(new Event("rimpods:cart"));
};

export const useCart = () => {
  const [items, setItems] = useState(read);

  useEffect(() => {
    const sync = () => setItems(read());
    window.addEventListener("rimpods:cart", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("rimpods:cart", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const add = useCallback((product, qty = 1) => {
    const current = read();
    const idx = current.findIndex((i) => i.product_id === product.id);
    if (idx >= 0) {
      current[idx].quantity = Math.min(99, current[idx].quantity + qty);
    } else {
      current.push({
        product_id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        quantity: qty,
      });
    }
    write(current);
  }, []);

  const remove = useCallback((product_id) => {
    write(read().filter((i) => i.product_id !== product_id));
  }, []);

  const setQty = useCallback((product_id, qty) => {
    const current = read();
    const idx = current.findIndex((i) => i.product_id === product_id);
    if (idx >= 0) {
      if (qty <= 0) current.splice(idx, 1);
      else current[idx].quantity = Math.min(99, qty);
      write(current);
    }
  }, []);

  const clear = useCallback(() => write([]), []);

  const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0);
  const count = items.reduce((s, i) => s + i.quantity, 0);
  const shipping = subtotal === 0 ? 0 : subtotal >= 250000 ? 0 : 18000;
  const total = subtotal + shipping;

  return { items, add, remove, setQty, clear, subtotal, shipping, total, count };
};
