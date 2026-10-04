import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, CheckCircle2, Mail, Phone, RefreshCw, ShieldCheck } from 'lucide-react';
import { authAPI, persistAuthSession } from '../lib/api';

const initialProfile = {
  code: '',
  name: '',
  email: '',
  account_type: 'INDEPENDENT_CONSULTANT',
  professional_title: '',
  speciality: '',
  practice_name: '',
};

export default function ExternalConsultantSignupPage() {
  const [mobileNumber, setMobileNumber] = useState('');
  const [challengeId, setChallengeId] = useState(null);
  const [profile, setProfile] = useState(initialProfile);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [resendAfter, setResendAfter] = useState(0);

  useEffect(() => {
    if (resendAfter <= 0) return undefined;
    const timer = window.setInterval(() => setResendAfter((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [resendAfter]);

  async function start(event) {
    event.preventDefault();
    setBusy(true); setError('');
    try {
      const response = await authAPI.startExternalSignup(mobileNumber);
      setChallengeId(response.challenge_id);
      setResendAfter(30);
    } catch (caught) {
      setError(caught.message || 'Verification could not be started.');
    } finally { setBusy(false); }
  }

  async function verify(event) {
    event.preventDefault();
    setBusy(true); setError('');
    try {
      const response = await authAPI.verifyExternalSignup({
        challenge_id: challengeId,
        ...profile,
        professional_title: profile.professional_title || null,
        speciality: profile.speciality || null,
        practice_name: profile.account_type === 'PRACTICE_OWNER' ? profile.practice_name || null : null,
      });
      persistAuthSession(response.auth_session, true);
      setResult(response);
    } catch (caught) {
      setError(caught.message || 'Verification or workspace provisioning could not complete. You can retry safely.');
    } finally { setBusy(false); }
  }

  async function resend() {
    setBusy(true); setError('');
    try { await authAPI.resendExternalSignup(challengeId); setResendAfter(30); }
    catch (caught) { setError(caught.message || 'A new code could not be sent yet.'); }
    finally { setBusy(false); }
  }

  const update = (key) => (event) => setProfile((current) => ({ ...current, [key]: event.target.value }));

  return (
    <main className="fluent-page min-h-screen px-4 py-8 sm:px-6">
      <section className="fluent-card mx-auto max-w-3xl rounded-[36px] p-6 sm:p-10">
        <Link href="/login" className="inline-flex items-center gap-2 text-sm text-[#0f6cbd]"><ArrowLeft className="h-4 w-4" />Back to sign in</Link>
        <p className="mt-8 text-xs uppercase tracking-[0.24em] text-[#0f6cbd]">Fiteatsy Consultant SaaS</p>
        <h1 className="mt-3 text-3xl font-semibold text-[#242424] sm:text-4xl">Continue with mobile OTP</h1>
        <p className="mt-3 text-base leading-7 text-[#616161]">Verify your mobile identity to resume your existing workspace or create a new consultant workspace.</p>

        {!challengeId ? (
          <form onSubmit={start} className="mt-8 space-y-5">
            <label className="block"><span className="mb-2 block text-sm text-[#424242]">Mobile number</span><div className="fluent-input flex items-center gap-3 rounded-[22px] px-4 py-3"><Phone className="h-4 w-4 text-[#616161]" /><input required type="tel" value={mobileNumber} onChange={(event) => setMobileNumber(event.target.value)} placeholder="+91 97620 06688" className="w-full bg-transparent text-sm text-[#242424] outline-none" autoComplete="tel" /></div></label>
            <button disabled={busy} className="fluent-primary-button flex w-full items-center justify-center gap-2 rounded-[24px] px-4 py-4 text-sm font-medium disabled:opacity-60">Send OTP<ArrowRight className="h-4 w-4" /></button>
          </form>
        ) : result ? (
          <div className="mt-8 rounded-[28px] border border-[#107c10]/20 bg-[#107c10]/10 p-6">
            <CheckCircle2 className="h-9 w-9 text-[#107c10]" />
            <h2 className="mt-4 text-2xl font-semibold text-[#242424]">{result.identity_type === 'RETURNING_CONSULTANT' ? 'Welcome back' : 'Workspace foundation created'}</h2>
            <p className="mt-2 text-sm leading-6 text-[#424242]">{result.identity_type === 'RETURNING_CONSULTANT' ? 'Your verified mobile identity was matched to your existing account and tenant.' : 'Your verified account, tenant, OWNER membership, and onboarding record are linked. Complete onboarding before workspace access is enabled.'}</p>
            <Link href={result.workspace_ready ? '/dashboard/provider' : '/onboarding'} className="fluent-primary-button mt-6 inline-flex items-center gap-2 rounded-[22px] px-5 py-3 text-sm font-medium">Continue<ArrowRight className="h-4 w-4" /></Link>
          </div>
        ) : (
          <form onSubmit={verify} className="mt-8 grid gap-5 sm:grid-cols-2">
            <div className="sm:col-span-2 rounded-[22px] border border-[#0f6cbd]/20 bg-[#0f6cbd]/5 p-4 text-sm text-[#424242]"><ShieldCheck className="mr-2 inline h-4 w-4 text-[#0f6cbd]" />OTP sent to {mobileNumber}.</div>
            <label><span className="mb-2 block text-sm text-[#424242]">6-digit code</span><input required inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={profile.code} onChange={update('code')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></label>
            <label><span className="mb-2 block text-sm text-[#424242]">Full name</span><input required minLength={2} value={profile.name} onChange={update('name')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" autoComplete="name" /></label>
            <label><span className="mb-2 block text-sm text-[#424242]">Email (optional)</span><div className="fluent-input flex items-center gap-3 rounded-[22px] px-4 py-3"><Mail className="h-4 w-4 text-[#616161]" /><input type="email" value={profile.email} onChange={update('email')} className="w-full bg-transparent text-sm outline-none" autoComplete="email" /></div></label>
            <label><span className="mb-2 block text-sm text-[#424242]">Account type</span><select value={profile.account_type} onChange={update('account_type')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm"><option value="INDEPENDENT_CONSULTANT">Independent consultant</option><option value="PRACTICE_OWNER">Practice owner</option></select></label>
            <label><span className="mb-2 block text-sm text-[#424242]">Professional title</span><input value={profile.professional_title} onChange={update('professional_title')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></label>
            <label><span className="mb-2 block text-sm text-[#424242]">Speciality</span><input value={profile.speciality} onChange={update('speciality')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></label>
            {profile.account_type === 'PRACTICE_OWNER' ? <label className="sm:col-span-2"><span className="mb-2 block text-sm text-[#424242]">Practice name</span><input required value={profile.practice_name} onChange={update('practice_name')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></label> : null}
            <div className="sm:col-span-2 flex flex-col gap-3 sm:flex-row"><button disabled={busy} className="fluent-primary-button flex flex-1 items-center justify-center gap-2 rounded-[24px] px-4 py-4 text-sm font-medium disabled:opacity-60">Verify OTP and continue<ArrowRight className="h-4 w-4" /></button><button type="button" onClick={resend} disabled={busy || resendAfter > 0} className="flex items-center justify-center gap-2 rounded-[24px] border border-black/10 px-5 py-4 text-sm text-[#424242] disabled:opacity-60"><RefreshCw className="h-4 w-4" />{resendAfter > 0 ? `Resend in ${resendAfter}s` : 'Resend OTP'}</button></div>
          </form>
        )}
        {error ? <div role="alert" className="mt-5 rounded-[20px] border border-[#d13438]/20 bg-[#d13438]/10 px-4 py-3 text-sm text-[#b10e1c]">{error}</div> : null}
      </section>
    </main>
  );
}
