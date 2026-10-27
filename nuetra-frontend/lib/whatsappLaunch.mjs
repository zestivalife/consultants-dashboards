import { parsePhoneNumberFromString } from "libphonenumber-js";

function resolveCountryIso2(input = {}) {
  const value = input.countryIso2 || input.country_iso2 || "";
  return String(value).trim().toUpperCase() || undefined;
}

export function canonicaliseWhatsAppPhone(value = "", countryIso2 = "") {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const region = String(countryIso2 || "").trim().toUpperCase() || undefined;
  const parsed = parsePhoneNumberFromString(raw, region);
  if (parsed?.isPossible()) return parsed.number;
  if (raw.startsWith("+")) {
    const digits = raw.replace(/\D/g, "");
    return digits ? `+${digits}` : "";
  }
  return "";
}

export function normaliseWhatsAppPhone(value = "", countryIso2 = "") {
  return canonicaliseWhatsAppPhone(value, countryIso2).replace(/\D/g, "");
}

export function buildWhatsAppUrl(input = {}) {
  const { phone = "", message = "" } = input;
  const digits = normaliseWhatsAppPhone(phone, resolveCountryIso2(input));
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
