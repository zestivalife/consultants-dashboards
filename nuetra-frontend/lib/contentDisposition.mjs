export function contentDispositionFilename(disposition, fallback) {
  const extended = /filename\*\s*=\s*(?:UTF-8'')?([^;]+)/i.exec(disposition || '')?.[1]?.trim().replace(/^"|"$/g, '');
  if (extended) {
    try { return decodeURIComponent(extended); } catch { return extended; }
  }
  return /filename="?([^";]+)"?/i.exec(disposition || '')?.[1] || fallback;
}
