const finitePositive = (value) => Number.isFinite(Number(value)) && Number(value) > 0;
const timestamp = (value) => {
  const time = value ? Date.parse(value) : NaN;
  return Number.isFinite(time) ? time : null;
};

export const MEASUREMENT_LABELS = {
  HEIGHT_CM: 'Height', WEIGHT_KG: 'Weight', WAIST_CM: 'Waist', HIP_CM: 'Hip',
  NECK_CM: 'Neck', CHEST_CM: 'Chest', MID_UPPER_ARM_CM: 'Upper arm',
  THIGH_CM: 'Thigh', CALF_CM: 'Calf',
};

export function currentMeasurementRows(history = []) {
  const latestVersion = new Map();
  for (const row of history) {
    if (!row?.series_id || !MEASUREMENT_LABELS[row.measurement_type] || !finitePositive(row.value) || timestamp(row.measured_at) === null) continue;
    const current = latestVersion.get(row.series_id);
    if (!current || Number(row.version) > Number(current.version)) latestVersion.set(row.series_id, row);
  }
  return [...latestVersion.values()].sort((a, b) => timestamp(a.measured_at) - timestamp(b.measured_at) || timestamp(a.created_at) - timestamp(b.created_at));
}

export function measurementSeries(history = []) {
  const grouped = Object.fromEntries(Object.keys(MEASUREMENT_LABELS).map((kind) => [kind, []]));
  for (const row of currentMeasurementRows(history)) grouped[row.measurement_type].push(row);
  return grouped;
}

export function measurementTrend(rows = []) {
  const valid = rows.filter((row) => finitePositive(row.value) && timestamp(row.measured_at) !== null);
  const latest = valid.at(-1) || null;
  const previous = valid.length > 1 ? valid.at(-2) : null;
  if (!latest) return { latest: null, previous: null, absoluteChange: null, percentageChange: null };
  const absoluteChange = previous ? Math.round((Number(latest.value) - Number(previous.value)) * 100) / 100 : null;
  const percentageChange = previous ? Math.round((absoluteChange / Number(previous.value)) * 10000) / 100 : null;
  return { latest, previous, absoluteChange, percentageChange };
}

export function buildHealthTimeline({ enrichment = {}, measurements = {}, biomarkers = [], documents = [], practiceEvents = [] } = {}) {
  const events = [];
  const add = (event) => { if (timestamp(event.occurredAt) !== null) events.push(event); };
  if (enrichment?.provenance?.updated_at) add({ id: `profile-${enrichment.version || 0}`, type: 'PROFILE_UPDATE', title: 'Health profile updated', occurredAt: enrichment.provenance.updated_at, source: enrichment.provenance.source || 'EXTERNAL_CLIENT360_ENRICHMENT', status: 'Historical' });
  for (const row of currentMeasurementRows(measurements.history || [])) add({ id: `measurement-${row.id}`, type: 'MEASUREMENT', title: `${MEASUREMENT_LABELS[row.measurement_type]} recorded`, detail: `${row.value} ${row.unit}`, occurredAt: row.measured_at, source: row.source, status: 'Historical' });
  for (const item of biomarkers) {
    if (item.status && item.status !== 'CONFIRMED') continue;
    add({ id: `biomarker-${item.id || item.canonicalBiomarkerId}`, type: 'BIOMARKER', title: `${item.name || 'Biomarker'} confirmed`, detail: item.value == null ? null : `${item.value} ${item.unit || ''}`.trim(), occurredAt: item.observationDate, source: item.sourceLabel || item.provenance?.source || 'Confirmed clinical evidence', status: 'Confirmed' });
  }
  for (const document of documents) add({ id: `document-${document.id}`, type: 'REPORT', title: document.name || 'Health report added', detail: document.category?.replaceAll('_', ' '), occurredAt: document.uploadedAt || document.documentDate, source: document.sourceLabel || 'Health record', status: document.processingStatus === 'COMPLETED' ? 'Confirmed' : 'Awaiting review' });
  for (const event of practiceEvents) add({ id: `practice-${event.id}`, type: event.event_type || 'PRACTICE_EVENT', title: event.summary || 'Practice activity', occurredAt: event.occurred_at, source: event.source_type || 'Practice activity', status: 'Historical' });
  return events.sort((a, b) => timestamp(b.occurredAt) - timestamp(a.occurredAt));
}

export function buildReviewPriorities({ missingChecklist = [], measurements = {}, pendingReports = 0, now = Date.now() } = {}) {
  const items = missingChecklist.map((item) => ({ code: `MISSING_${String(item.label).toUpperCase().replaceAll(' ', '_')}`, title: `${item.label} not recorded`, detail: `Complete ${String(item.category).replace(/([A-Z])/g, ' $1').toLowerCase()}.`, source: 'Profile completeness' }));
  const current = currentMeasurementRows(measurements.history || []);
  if (!current.length) items.push({ code: 'MISSING_MEASUREMENTS', title: 'No body measurements recorded', detail: 'Add a dated measurement when available.', source: 'Measurement history' });
  else {
    const latest = Math.max(...current.map((row) => timestamp(row.measured_at)));
    if (Number.isFinite(latest) && now - latest > 90 * 86400000) items.push({ code: 'STALE_MEASUREMENTS', title: 'Measurements may be stale', detail: 'The latest dated measurement is more than 90 days old.', source: 'Measurement history' });
  }
  if (pendingReports > 0) items.push({ code: 'UNREVIEWED_REPORTS', title: `${pendingReports} report${pendingReports === 1 ? '' : 's'} awaiting review`, detail: 'Review persisted report evidence before using it clinically.', source: 'Health records' });
  return items;
}
