import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  biomarkerSourceLabel,
  formatBiomarkerDate,
  normalizeBiomarkerForPresentation,
} from '../lib/biomarkerPresentation.mjs';

const labSource = {
  type: 'lab_report',
  label: 'Lab Report',
  reportId: 'report-2',
  reportDate: '2026-08-20',
  labName: 'Synthetic Lab',
  fileName: 'synthetic.pdf',
};

test('formats canonical observation date without substituting the render date', () => {
  assert.equal(formatBiomarkerDate('2026-08-20'), '20 Aug 2026');
  assert.equal(formatBiomarkerDate(null), 'Not available');
});

test('preserves structured Lab Report and Manual Entry provenance', () => {
  const lab = normalizeBiomarkerForPresentation({ biomarkerId: 'ldl', name: 'LDL Cholesterol', value: 135, unit: 'mg/dL', testDate: '2026-08-20', source: labSource });
  const manual = normalizeBiomarkerForPresentation({ biomarkerId: 'tsh', name: 'TSH', value: 3, unit: 'mIU/L', testDate: '2026-08-20', source: { type: 'manual_entry', label: 'Manual Entry', reportId: null } });
  assert.equal(biomarkerSourceLabel(lab.source), 'Lab Report');
  assert.equal(biomarkerSourceLabel(manual.source), 'Manual Entry');
});

test('resolves latest by observation date and orders complete history newest first', () => {
  const biomarker = normalizeBiomarkerForPresentation({
    biomarkerId: 'ldl',
    canonicalMarkerName: 'LDL Cholesterol',
    value: 120,
    unit: 'mg/dL',
    testDate: '2026-08-01',
    history: [
      { observationId: 'older', value: 120, unit: 'mg/dL', referenceRange: null, testDate: '2026-08-01', source: { type: 'manual_entry', label: 'Manual Entry', reportId: null }, createdAtISO: '2026-08-01T08:00:00.000Z' },
      { observationId: 'latest', value: 135, unit: 'mg/dL', referenceRange: '<100', testDate: '2026-08-20', source: labSource, createdAtISO: '2026-08-20T08:00:00.000Z' },
    ],
  });
  assert.equal(biomarker.name, 'LDL Cholesterol');
  assert.equal(biomarker.value, 135);
  assert.deepEqual(biomarker.history.map((item) => item.observationId), ['latest', 'older']);
});

test('does not copy a newer reference range into an older observation', () => {
  const biomarker = normalizeBiomarkerForPresentation({
    biomarkerId: 'ldl',
    name: 'LDL Cholesterol',
    history: [
      { observationId: 'latest', value: 135, unit: 'mg/dL', referenceRange: '<100', testDate: '2026-08-20', source: labSource },
      { observationId: 'older', value: 120, unit: 'mg/dL', referenceRange: null, testDate: '2026-08-01', source: labSource },
    ],
  });
  assert.equal(biomarker.history[0].referenceRange, '<100');
  assert.equal(biomarker.history[1].referenceRange, null);
});

test('single observations do not fabricate historical results', () => {
  const biomarker = normalizeBiomarkerForPresentation({ biomarkerId: 'albumin', name: 'Albumin', value: 4.55, unit: 'g/dL', referenceRange: '3.5 - 5.2', testDate: '2026-08-20', source: labSource });
  assert.deepEqual(biomarker.history, []);
  assert.equal(biomarker.value, 4.55);
});

test('Consultant profile exposes the factual biomarker navigation and fields', async () => {
  const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
  assert.match(workspace, /key: 'Biomarkers', label: 'Biomarkers'/);
  assert.match(workspace, /label="Observation date"/);
  assert.match(workspace, /label="Source"/);
  assert.match(workspace, /View history \(\{biomarker\.history\.length\}\)/);
  assert.match(workspace, />Date<\/th>/);
  assert.match(workspace, />Value<\/th>/);
  assert.match(workspace, />Unit<\/th>/);
  assert.match(workspace, />Reference<\/th>/);
  assert.match(workspace, />Source<\/th>/);
});

test('Consultant biomarker presentation contains no generic interpretation', async () => {
  const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
  assert.doesNotMatch(workspace, /This can improve with consistent routine this week\./i);
});
