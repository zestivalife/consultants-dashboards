import Head from 'next/head';
import { useEffect, useState } from 'react';
import { ShieldCheck } from 'lucide-react';

import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../lib/api';

export default function InternalMfaEnrollmentPage() {
  const { user, isLoading, logout } = useAuth();
  const [activationToken, setActivationToken] = useState('');
  const [uri, setUri] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isLoading) return;
    if (!user || String(user.role || '').toLowerCase() !== 'internal_super_admin' || user.must_change_password) {
      window.location.replace('/login');
      return;
    }
    authAPI.beginInternalMfaEnrollment()
      .then((result) => { setActivationToken(result.activation_token); setUri(result.otp_auth_uri); })
      .catch((nextError) => setError(nextError?.message || 'MFA enrolment could not be started.'));
  }, [isLoading, user]);

  async function confirm(event) {
    event.preventDefault();
    setError(''); setSubmitting(true);
    try {
      await authAPI.confirmInternalMfaEnrollment(activationToken, code);
      await logout();
    } catch (nextError) {
      setError(nextError?.message || 'Authenticator code could not be confirmed.');
      setSubmitting(false);
    }
  }

  return <>
    <Head><title>Enrol MFA | Zestiva Internal</title></Head>
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-12">
      <section className="w-full max-w-xl rounded-[32px] border border-slate-200 bg-white p-8 shadow-2xl shadow-slate-200/70">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-700 text-white"><ShieldCheck className="h-7 w-7"/></div>
        <p className="mt-6 text-xs font-black uppercase tracking-[0.24em] text-blue-700">Mandatory security step</p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">Enrol your authenticator</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">Add the setup URI to your trusted authenticator, then enter its current six-digit code. Privileged access remains blocked until confirmation.</p>
        {error ? <p role="alert" className="mt-5 rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-800">{error}</p> : null}
        {!uri && !error ? <p role="status" className="mt-5 text-sm font-semibold text-slate-500">Preparing encrypted MFA enrolment…</p> : null}
        {uri ? <form onSubmit={confirm} className="mt-6 space-y-5">
          <label className="block"><span className="text-sm font-bold text-slate-700">Authenticator setup URI</span><textarea readOnly value={uri} aria-label="Authenticator setup URI" className="mt-2 min-h-28 w-full break-all rounded-2xl border bg-slate-50 p-4 font-mono text-xs"/></label>
          <label className="block"><span className="text-sm font-bold text-slate-700">Six-digit code</span><input required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={(event)=>setCode(event.target.value.replace(/\D/g,''))} className="mt-2 min-h-[52px] w-full rounded-2xl border px-4 text-lg font-bold tracking-[0.3em]"/></label>
          <button disabled={submitting || code.length !== 6} className="min-h-[52px] w-full rounded-2xl bg-blue-700 font-bold text-white disabled:opacity-50">{submitting ? 'Confirming…' : 'Confirm MFA and sign in again'}</button>
        </form> : null}
      </section>
    </main>
  </>;
}
