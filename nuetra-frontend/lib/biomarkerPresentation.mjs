const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function finiteNumber(value) {
  const numberValue = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(numberValue) ? numberValue : null;
}

function sourceFrom(observation, fallback = null) {
  const source = observation?.source && typeof observation.source === 'object' ? observation.source : fallback;
  if (source && typeof source === 'object') {
    return {
      type: source.type || (source.reportId ? 'lab_report' : 'manual_entry'),
      label: source.label || (source.reportId ? 'Lab Report' : 'Manual Entry'),
      reportId: source.reportId ?? null,
      reportDate: source.reportDate ?? null,
      labName: source.labName ?? null,
      fileName: source.fileName ?? null,
    };
  }
  const reportId = observation?.sourceReportId ?? null;
  return {
    type: reportId ? 'lab_report' : 'manual_entry',
    label: reportId ? 'Lab Report' : 'Manual Entry',
    reportId,
    reportDate: null,
    labName: null,
    fileName: null,
  };
}

function observationTimestamp(observation) {
  const testDate = Date.parse(observation?.testDate || '');
  const createdAt = Date.parse(observation?.createdAtISO || '');
  return [Number.isFinite(testDate) ? testDate : Number.NEGATIVE_INFINITY, Number.isFinite(createdAt) ? createdAt : Number.NEGATIVE_INFINITY];
}

export function compareBiomarkerObservationsNewestFirst(left, right) {
  const [leftTestDate, leftCreatedAt] = observationTimestamp(left);
  const [rightTestDate, rightCreatedAt] = observationTimestamp(right);
  return rightTestDate - leftTestDate || rightCreatedAt - leftCreatedAt || String(left?.observationId || '').localeCompare(String(right?.observationId || ''));
}

function normalizeObservation(observation, fallbackSource = null) {
  return {
    observationId: observation?.observationId ?? null,
    value: finiteNumber(observation?.value),
    unit: observation?.unit || '',
    referenceRange: observation?.referenceRange ?? null,
    status: observation?.clinicalStatus || observation?.status || observation?.validationStatus || null,
    validationStatus: observation?.validationStatus ?? null,
    testDate: observation?.testDate ?? null,
    rawMarkerName: observation?.rawMarkerName ?? null,
    source: sourceFrom(observation, fallbackSource),
    createdAtISO: observation?.createdAtISO ?? null,
  };
}

export function normalizeBiomarkerForPresentation(record) {
  const topLevel = normalizeObservation({
    ...record,
    status: record?.clinicalStatus || record?.status,
  }, record?.source);
  const history = (Array.isArray(record?.history) ? record.history : [])
    .map((observation) => normalizeObservation(observation, record?.source))
    .filter((observation) => observation.value != null)
    .sort(compareBiomarkerObservationsNewestFirst);
  const latest = history[0] || topLevel;
  const previous = history[1] || null;

  return {
    biomarkerId: record?.biomarkerId ?? null,
    name: record?.canonicalMarkerName || record?.name || 'Biomarker',
    rawMarkerName: record?.rawMarkerName ?? null,
    value: latest.value,
    unit: latest.unit,
    status: latest.status,
    referenceRange: latest.referenceRange,
    confidence: record?.confidence ?? null,
    testDate: latest.testDate,
    createdAtISO: latest.createdAtISO,
    source: latest.source,
    trend: record?.comparisonStatus || record?.trend || null,
    previousValue: previous?.value ?? record?.previousValue ?? null,
    previousTestDate: previous?.testDate ?? record?.previousTestDate ?? null,
    history,
  };
}

export function formatBiomarkerDate(value) {
  if (!value) return 'Not available';
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return 'Not available';
  const monthIndex = Number(match[2]) - 1;
  if (monthIndex < 0 || monthIndex > 11) return 'Not available';
  return `${match[3]} ${MONTHS[monthIndex]} ${match[1]}`;
}

export function biomarkerSourceLabel(source) {
  return source?.label || 'Source unavailable';
}
