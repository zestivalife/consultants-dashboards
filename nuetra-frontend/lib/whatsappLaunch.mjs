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

export function shouldUseWhatsAppApp(browserWindow = globalThis.window) {
  const navigator = browserWindow?.navigator;
  if (navigator?.userAgentData?.mobile === true) return true;

  const userAgent = String(navigator?.userAgent || "");
  if (/Android|iPhone|iPad|iPod|IEMobile|Opera Mini/i.test(userAgent)) {
    return true;
  }

  // iPadOS can identify itself as macOS. Touch capability distinguishes it
  // from a desktop Mac without relying on viewport width alone.
  if (navigator?.platform === "MacIntel" && Number(navigator?.maxTouchPoints) > 1) {
    return true;
  }

  // Last-resort responsive signal for browsers that suppress device metadata.
  return browserWindow?.matchMedia?.("(max-width: 767px)")?.matches === true;
}

export function buildWhatsAppUrl(input = {}, browserWindow = globalThis.window) {
  const { phone = "", message = "" } = input;
  const digits = normaliseWhatsAppPhone(phone, resolveCountryIso2(input));
  const parameters = new URLSearchParams();
  if (digits) parameters.set("phone", digits);
  if (message) parameters.set("text", message);
  const query = parameters.toString();
  const base = shouldUseWhatsAppApp(browserWindow)
    ? "https://api.whatsapp.com/send"
    : "https://web.whatsapp.com/send";
  return query ? `${base}?${query}` : base;
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
  const url = buildWhatsAppUrl(input, browserWindow);
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
