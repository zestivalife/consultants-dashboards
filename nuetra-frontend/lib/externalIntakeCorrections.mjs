import { parsePhoneNumberFromString } from 'libphonenumber-js';

export const WATER_INTAKE_OPTIONS = Array.from({ length: 11 }, (_, index) => {
  const millilitres = 1000 + (index * 500);
  return [String(millilitres), `${millilitres / 1000} ltr`];
});

export function canonicalPhoneDisplay(value, defaultCountry = 'IN') {
  const raw = String(value || '').trim();
  if (!raw) return 'Not provided';
  const indianTrunk = defaultCountry === 'IN' && /^0\d{10}$/.test(raw) ? `+91${raw.slice(1)}` : raw;
  const parsed = parsePhoneNumberFromString(indianTrunk, defaultCountry);
  return parsed?.isValid() ? parsed.number : raw;
}

export function validDateOfBirth(value, today = new Date()) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ''))) return false;
  const [year, month, day] = value.split('-').map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) return false;
  const ceiling = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  return parsed.getTime() <= ceiling;
}

export async function validatePdfFile(file, maximumBytes = 12 * 1024 * 1024) {
  if (!file || file.size <= 0 || file.size > maximumBytes) return 'Choose a PDF no larger than 12 MB.';
  if (file.type !== 'application/pdf' || !file.name.toLowerCase().endsWith('.pdf')) return 'Only PDF blood reports are supported.';
  const signature = new TextDecoder('ascii').decode(await file.slice(0, 5).arrayBuffer());
  return signature === '%PDF-' ? '' : 'This file is not a valid PDF.';
}

export function normaliseWaterIntake(section = {}) {
  if (section.waterIntakeMl != null) return String(section.waterIntakeMl);
  return '';
}
