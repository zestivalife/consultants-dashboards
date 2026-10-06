import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  completeFiteatsyConsultantOnboarding,
  getFiteatsyConsultantOnboarding,
  updateFiteatsyConsultantOnboarding,
} from '../../lib/fiteatsyConsultantsApi';

const empty = { consultantName: '', professionalTitle: '', speciality: '', practiceName: '', country: 'IN', timezone: 'Asia/Kolkata', acceptTerms: false };

export default function ConsultantOnboardingPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [onboarding, setOnboarding] = useState(null);
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isLoading) return;
    if (!user) { router.replace('/login'); return; }
    getFiteatsyConsultantOnboarding().then((payload) => {
      const value = payload?.onboarding || payload;
      if (value?.workspaceReady) { router.replace('/dashboard/consultant'); return; }
      setOnboarding(value);
      setForm({
        consultantName: value?.consultantName || '', professionalTitle: value?.professionalTitle || '',
        speciality: value?.speciality || '', practiceName: value?.practiceName || '',
        country: value?.country || 'IN', timezone: value?.timezone || 'Asia/Kolkata', acceptTerms: Boolean(value?.termsAccepted)
      });
    }).catch((caught) => setError(caught.message || 'Onboarding could not be loaded.')).finally(() => setBusy(false));
  }, [isLoading, router, user]);

  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.type === 'checkbox' ? event.target.checked : event.target.value }));

  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const savedPayload = await updateFiteatsyConsultantOnboarding({ ...form, version: onboarding.version });
      const saved = savedPayload?.onboarding || savedPayload;
      const completedPayload = await completeFiteatsyConsultantOnboarding(saved.version);
      const completed = completedPayload?.onboarding || completedPayload;
      if (!completed?.workspaceReady) throw new Error('Workspace readiness was not confirmed.');
      router.replace('/dashboard/consultant?view=command-center');
    } catch (caught) { setError(caught.message || 'Onboarding could not be completed.'); setBusy(false); }
  }

  if (busy && !onboarding) return <main className="fluent-page min-h-screen p-8"><p>Loading consultant onboarding…</p></main>;

  return <main className="fluent-page min-h-screen px-4 py-8 sm:px-6"><section className="fluent-card mx-auto max-w-3xl rounded-[36px] p-6 sm:p-10">
    <p className="text-xs uppercase tracking-[0.24em] text-[#0f6cbd]">Fiteatsy Consultant SaaS</p>
    <h1 className="mt-3 text-3xl font-semibold text-[#242424]">Complete your consultant workspace</h1>
    <p className="mt-3 text-base leading-7 text-[#616161]">Set up your professional practice. Client health intake is separate and is not part of this onboarding.</p>
    <form onSubmit={submit} className="mt-8 grid gap-5 sm:grid-cols-2">
      <Field label="Consultant name"><input required minLength={2} value={form.consultantName} onChange={update('consultantName')} className="fluent-input w-full rounded-[22px] px-4 py-3" /></Field>
      <Field label="Professional title"><input required value={form.professionalTitle} onChange={update('professionalTitle')} className="fluent-input w-full rounded-[22px] px-4 py-3" /></Field>
      <Field label="Speciality"><input required value={form.speciality} onChange={update('speciality')} className="fluent-input w-full rounded-[22px] px-4 py-3" /></Field>
      {onboarding?.accountType === 'PRACTICE_OWNER' ? <Field label="Practice name"><input required value={form.practiceName} onChange={update('practiceName')} className="fluent-input w-full rounded-[22px] px-4 py-3" /></Field> : null}
      <Field label="Country"><input required maxLength={2} value={form.country} onChange={update('country')} className="fluent-input w-full rounded-[22px] px-4 py-3 uppercase" /></Field>
      <Field label="Timezone"><input required value={form.timezone} onChange={update('timezone')} className="fluent-input w-full rounded-[22px] px-4 py-3" /></Field>
      <label className="sm:col-span-2 flex items-start gap-3 rounded-[22px] border border-black/10 p-4"><input required type="checkbox" checked={form.acceptTerms} onChange={update('acceptTerms')} className="mt-1" /><span className="text-sm leading-6 text-[#424242]">I confirm these professional details and accept the Consultant SaaS terms.</span></label>
      {error ? <div role="alert" className="sm:col-span-2 rounded-[20px] border border-[#d13438]/20 bg-[#d13438]/10 px-4 py-3 text-sm text-[#b10e1c]">{error}</div> : null}
      <button disabled={busy} className="fluent-primary-button sm:col-span-2 flex items-center justify-center gap-2 rounded-[24px] px-4 py-4 text-sm font-medium disabled:opacity-60"><CheckCircle2 className="h-4 w-4" />Complete onboarding and enter workspace</button>
    </form>
  </section></main>;
}

function Field({ label, children }) { return <label><span className="mb-2 block text-sm text-[#424242]">{label}</span>{children}</label>; }
