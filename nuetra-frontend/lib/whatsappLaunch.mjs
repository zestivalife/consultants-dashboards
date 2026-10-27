export function normaliseWhatsAppPhone(value = "") {
  return String(value).replace(/\D/g, "");
}

export function buildWhatsAppUrl({ phone = "", message = "" } = {}) {
  const digits = normaliseWhatsAppPhone(phone);
  const recipient = digits ? `/${digits}` : "";
  const query = message ? `?text=${encodeURIComponent(message)}` : "";
  return `https://wa.me${recipient}${query}`;
}

export function reserveWhatsAppWindow(browserWindow = globalThis.window) {
  const popup = browserWindow?.open?.("about:blank", "_blank");
  if (popup) popup.opener = null;
  return popup || null;
}

export function navigateReservedWhatsAppWindow(
  popup,
  input,
  browserWindow = globalThis.window,
) {
  const url = buildWhatsAppUrl(input);
  if (popup && !popup.closed) {
    popup.location.replace(url);
    return url;
  }
  const fallback = browserWindow?.open?.(url, "_blank", "noopener,noreferrer");
  if (!fallback) {
    throw new Error(
      "WhatsApp could not open. Allow pop-ups for Zestiva and try again.",
    );
  }
  return url;
}

export function closeReservedWhatsAppWindow(popup) {
  if (popup && !popup.closed) popup.close();
}
