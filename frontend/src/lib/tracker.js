// Pixel tracking helpers (Meta + TikTok)
const fbq = (...args) => { if (typeof window !== "undefined" && window.fbq) window.fbq(...args); };
const ttq = (...args) => { if (typeof window !== "undefined" && window.ttq) window.ttq.track(...args); };

export const trackViewContent = (product) => {
  fbq("track", "ViewContent", {
    content_ids: [product.id], content_type: "product",
    content_name: product.name, value: product.price, currency: "IDR",
  });
  ttq("ViewContent", { contents: [{ content_id: product.id, content_name: product.name, price: product.price }], value: product.price, currency: "IDR" });
};

export const trackAddToCart = (product, qty = 1) => {
  fbq("track", "AddToCart", {
    content_ids: [product.id], content_type: "product",
    content_name: product.name, value: product.price * qty, currency: "IDR",
  });
  ttq("AddToCart", { contents: [{ content_id: product.id, content_name: product.name, price: product.price, quantity: qty }], value: product.price * qty, currency: "IDR" });
};

export const trackInitiateCheckout = (items, total) => {
  const contents = items.map((i) => ({ content_id: i.product_id, content_name: i.name, price: i.price, quantity: i.quantity }));
  fbq("track", "InitiateCheckout", { content_ids: items.map((i) => i.product_id), value: total, currency: "IDR", num_items: items.reduce((s, i) => s + i.quantity, 0) });
  ttq("InitiateCheckout", { contents, value: total, currency: "IDR" });
};

export const trackLead = (order) => {
  fbq("track", "Lead", { value: order.total, currency: "IDR", content_name: order.order_number });
  ttq("SubmitForm", { value: order.total, currency: "IDR" });
};

export const trackPurchase = (order) => {
  const contents = (order.items || []).map((i) => ({ content_id: i.product_id, content_name: i.name, price: i.price, quantity: i.quantity }));
  fbq("track", "Purchase", { value: order.total, currency: "IDR", content_ids: contents.map((c) => c.content_id), num_items: contents.length });
  ttq("CompletePayment", { contents, value: order.total, currency: "IDR" });
};
