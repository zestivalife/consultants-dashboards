const present = (value) =>
  value !== undefined &&
  value !== null &&
  value !== '' &&
  !(Array.isArray(value) && value.length === 0);

export function buildInformationSubmission(fields = [], values = {}) {
  return Object.fromEntries(
    fields
      .filter((field) => present(values[field.field_id]))
      .map((field) => [field.field_id, values[field.field_id]]),
  );
}

export function canSubmitInformationUpdate(fields = [], values = {}) {
  const payload = buildInformationSubmission(fields, values);
  const requiredComplete = fields
    .filter((field) => field.requirement_level === 'REQUIRED')
    .every((field) => present(values[field.field_id]));
  return requiredComplete && Object.keys(payload).length > 0;
}

export function freeTextListValue(value) {
  return (Array.isArray(value) ? value : [])
    .filter((item) => !['NONE', 'UNKNOWN'].includes(String(item).toUpperCase()))
    .join('\n');
}

export function parseFreeTextList(value) {
  return String(value || '')
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}
