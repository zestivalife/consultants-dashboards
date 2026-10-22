import { useEffect, useState } from 'react';
import { Save } from 'lucide-react';
import { INTERNAL_HEALTH_GOALS } from '../../lib/internalClientProfile.mjs';
import { saveInternalClientProfileEnrichment } from '../../lib/practiceOperationsApi';

const emptyMeasurements = { height_cm: '', weight_kg: '', waist_cm: '', hip_cm: '', neck_cm: '', goal_weight_kg: '', body_fat_percent: '', recorded_at: '' };

export default function InternalClientProfileEnrichmentPanel({ clientId, profile, onSaved }) {
  const enrichment = profile?.internalEnrichment || {};
  const [goals, setGoals] = useState([]);
  const [measurements, setMeasurements] = useState(emptyMeasurements);
  const [medicalHistory, setMedicalHistory] = useState('');
  const [sleepStress, setSleepStress] = useState('');
  const [recordDates, setRecordDates] = useState({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => {
    setGoals(enrichment.goals || []);
    setMeasurements({ ...emptyMeasurements, ...(enrichment.measurements || {}) });
    setMedicalHistory(enrichment.medical_history_narrative ?? '');
    setSleepStress(enrichment.sleep_stress_narrative ?? '');
    setRecordDates(enrichment.health_record_dates || {});
  }, [clientId, enrichment.version]);

  const toggleGoal = (goal) => setGoals((current) => current.includes(goal) ? current.filter((item) => item !== goal) : current.length < 3 ? [...current, goal] : current);
  const save = async () => {
    setSaving(true); setMessage('');
    try {
      await saveInternalClientProfileEnrichment(clientId, {
        expected_version: enrichment.version || 0,
        values: {
          goals,
          dob_display_format: 'DD/MM/YYYY',
          measurements: Object.fromEntries(Object.entries(measurements).map(([key, value]) => [key, value === '' ? null : value])),
          medical_history_narrative: medicalHistory,
          sleep_stress_narrative: sleepStress,
          health_record_dates: recordDates,
        },
      });
      await onSaved(clientId); setMessage('Internal profile enrichment saved.');
    } catch (error) { setMessage(error.message || 'Profile enrichment could not be saved.'); }
    finally { setSaving(false); }
  };
  return <section className="rounded-[20px] border border-[var(--fluent-color-neutral-stroke-1)] bg-[var(--fluent-color-neutral-background-1)] p-5">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="text-[17px] font-semibold">Internal profile enrichment</h3><p className="mt-1 text-sm text-[var(--fluent-color-neutral-foreground-2)]">Governed Internal-only details. Fiteatsy base data remains read-only.</p></div><span className="rounded-full bg-[var(--fluent-color-neutral-background-2)] px-3 py-1 text-xs">Version {enrichment.version || 0}</span></div>
    <fieldset className="mt-5"><legend className="text-sm font-semibold">Health & wellness goals (maximum 3)</legend><div className="mt-2 flex flex-wrap gap-2">{INTERNAL_HEALTH_GOALS.map((goal) => <button type="button" key={goal} aria-pressed={goals.includes(goal)} onClick={() => toggleGoal(goal)} className={`min-h-11 rounded-full border px-3 text-sm ${goals.includes(goal) ? 'border-[var(--fluent-color-brand-stroke-1)] bg-[var(--fluent-color-brand-background-2)] font-semibold' : 'border-[var(--fluent-color-neutral-stroke-1)]'}`}>{goal}</button>)}</div><p className="mt-2 text-xs text-[var(--fluent-color-neutral-foreground-3)]">{goals.length}/3 selected</p></fieldset>
    <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['height_cm','Height (cm)'],['weight_kg','Weight (kg)'],['waist_cm','Waist (cm)'],['hip_cm','Hip (cm)'],['neck_cm','Neck (cm)'],['goal_weight_kg','Goal weight (kg)'],['body_fat_percent','Body fat (%)']].map(([key,label]) => <label key={key} className="text-sm font-medium">{label}<input type="number" min="0" step="0.1" value={measurements[key] ?? ''} onChange={(event) => setMeasurements((current) => ({...current,[key]:event.target.value}))} className="mt-1 min-h-11 w-full rounded-xl border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3" /></label>)}<label className="text-sm font-medium">Measured at<input type="datetime-local" value={measurements.recorded_at ? String(measurements.recorded_at).slice(0,16) : ''} onChange={(event) => setMeasurements((current) => ({...current,recorded_at:event.target.value}))} className="mt-1 min-h-11 w-full rounded-xl border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3" /></label></div>
    <div className="mt-5 grid gap-4 lg:grid-cols-2"><label className="text-sm font-medium">Medical History<textarea rows={4} value={medicalHistory} onChange={(event) => setMedicalHistory(event.target.value)} className="mt-1 w-full rounded-xl border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent p-3" /></label><label className="text-sm font-medium">Sleep & Stress<textarea rows={4} value={sleepStress} onChange={(event) => setSleepStress(event.target.value)} className="mt-1 w-full rounded-xl border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent p-3" /></label></div>
    {profile?.reports?.length ? <fieldset className="mt-5"><legend className="text-sm font-semibold">Health-record dates</legend><div className="mt-2 space-y-3">{profile.reports.map((report) => { const id=String(report.id || report.reportId || ''); const dates=recordDates[id] || {}; return <div key={id} className="grid gap-3 rounded-xl bg-[var(--fluent-color-neutral-background-2)] p-3 sm:grid-cols-[1fr_180px_180px]"><p className="self-center text-sm">{report.title || report.originalFilename || 'Health record'}</p>{[['report_date','Report date'],['confirmation_date','Confirmation date']].map(([key,label]) => <label key={key} className="text-xs font-medium">{label}<input type="date" value={dates[key] || ''} onChange={(event) => setRecordDates((current) => ({...current,[id]:{...(current[id] || {}),[key]:event.target.value || null}}))} className="mt-1 min-h-11 w-full rounded-xl border border-[var(--fluent-color-neutral-stroke-1)] bg-transparent px-3" /></label>)}</div>; })}</div></fieldset> : null}
    <div className="mt-5 flex flex-wrap items-center gap-3"><button type="button" disabled={saving} onClick={save} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-[var(--fluent-color-brand-background)] px-4 font-semibold text-[var(--fluent-color-brand-foreground)] disabled:opacity-50"><Save size={16}/>{saving ? 'Saving…' : 'Save Internal profile'}</button>{message ? <p role="status" className="text-sm text-[var(--fluent-color-neutral-foreground-2)]">{message}</p> : null}</div>
  </section>;
}
