import Head from 'next/head';
import { useEffect, useMemo, useState } from 'react';
import { Eye, EyeOff, KeyRound, ShieldCheck } from 'lucide-react';

import { useAuth } from '../../context/AuthContext';

const PASSWORD_RULES = [
  { id: 'length', label: 'At least 12 characters', test: (value) => value.length >= 12 },
  { id: 'upper', label: 'One uppercase letter', test: (value) => /[A-Z]/.test(value) },
  { id: 'lower', label: 'One lowercase letter', test: (value) => /[a-z]/.test(value) },
  { id: 'number', label: 'One number', test: (value) => /\d/.test(value) },
  { id: 'special', label: 'One special character', test: (value) => /[^A-Za-z0-9]/.test(value) },
];

function PasswordField({ label, value, onChange, visible, onToggle, autoComplete }) {
  return (
    <label className="block">
      <span className="text-sm font-bold text-slate-700">{label}</span>
      <div className="mt-2 flex items-center rounded-2xl border border-slate-200 bg-white px-4 shadow-sm transition focus-within:border-[#237afc]">
        <input
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete={autoComplete}
          className="min-h-[52px] flex-1 bg-transparent text-base font-semibold text-slate-900 outline-none"
        />
        <button
          type="button"
          onClick={onToggle}
          className="rounded-xl p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
          aria-label={visible ? `Hide ${label}` : `Show ${label}`}
        >
          {visible ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
        </button>
      </div>
    </label>
  );
}

export default function ChangeTemporaryPasswordPage() {
  const { user, isLoading, completeTemporaryPasswordChange, logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [visible, setVisible] = useState({ current: false, next: false, confirm: false });
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const ruleState = useMemo(
    () => PASSWORD_RULES.map((rule) => ({ ...rule, passed: rule.test(newPassword) })),
    [newPassword]
  );
  const passedRules = ruleState.filter((rule) => rule.passed).length;
  const strengthLabel = passedRules >= 5 ? 'Strong' : passedRules >= 3 ? 'Getting there' : 'Weak';
  const canSubmit = currentPassword && newPassword && confirmPassword && passedRules === PASSWORD_RULES.length && newPassword === confirmPassword;

  useEffect(() => {
    if (!isLoading && user && !user.must_change_password) {
      window.location.replace('/dashboard');
    }
  }, [isLoading, user]);

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage('');

    if (newPassword !== confirmPassword) {
      setMessage('New password and confirmation must match.');
      return;
    }

    setSubmitting(true);
    const result = await completeTemporaryPasswordChange({
      currentPassword,
      newPassword,
      confirmPassword,
    });
    if (result?.error) {
      setMessage(result.error);
      setSubmitting(false);
    }
  }

  if (isLoading || !user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <p className="text-sm font-bold text-slate-500">Preparing secure password setup...</p>
      </main>
    );
  }

  return (
    <>
      <Head>
        <title>Change Temporary Password | Zestiva</title>
      </Head>
      <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,#eaf3ff,transparent_34%),linear-gradient(135deg,#f8fafc,#ffffff)] px-6 py-10">
        <section className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <aside className="rounded-[32px] border border-white bg-white/80 p-8 shadow-2xl shadow-slate-200/60">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#237afc] text-white">
              <ShieldCheck className="h-7 w-7" />
            </div>
            <p className="mt-8 text-xs font-black uppercase tracking-[0.24em] text-[#237afc]">Mandatory security step</p>
            <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-950">Create your permanent password</h1>
            <p className="mt-4 text-base leading-7 text-slate-600">
              Your administrator created this account with a temporary password. Replace it now before entering the workspace.
            </p>
            <div className="mt-8 rounded-3xl bg-slate-950 p-5 text-white">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Signed in as</p>
              <p className="mt-2 text-lg font-black">{user.email}</p>
              <p className="mt-1 text-sm text-slate-300">{user.role?.replace(/_/g, ' ') || 'User'}</p>
            </div>
          </aside>

          <form onSubmit={handleSubmit} className="rounded-[32px] border border-slate-100 bg-white p-8 shadow-2xl shadow-slate-200/70">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                <KeyRound className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-2xl font-black text-slate-950">Password setup</h2>
                <p className="text-sm font-semibold text-slate-500">This screen is required once for temporary credentials.</p>
              </div>
            </div>

            <div className="mt-8 space-y-5">
              <PasswordField
                label="Current temporary password"
                value={currentPassword}
                onChange={setCurrentPassword}
                visible={visible.current}
                onToggle={() => setVisible((current) => ({ ...current, current: !current.current }))}
                autoComplete="current-password"
              />
              <PasswordField
                label="New password"
                value={newPassword}
                onChange={setNewPassword}
                visible={visible.next}
                onToggle={() => setVisible((current) => ({ ...current, next: !current.next }))}
                autoComplete="new-password"
              />
              <PasswordField
                label="Confirm new password"
                value={confirmPassword}
                onChange={setConfirmPassword}
                visible={visible.confirm}
                onToggle={() => setVisible((current) => ({ ...current, confirm: !current.confirm }))}
                autoComplete="new-password"
              />
            </div>

            <div className="mt-6 rounded-3xl bg-slate-50 p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-black text-slate-900">Password strength</p>
                <span className="rounded-full bg-white px-3 py-1 text-xs font-black text-slate-700 shadow-sm">{strengthLabel}</span>
              </div>
              <div className="mt-4 grid grid-cols-5 gap-2">
                {PASSWORD_RULES.map((rule, index) => (
                  <span
                    key={rule.id}
                    className={`h-2 rounded-full ${index < passedRules ? 'bg-[#237afc]' : 'bg-slate-200'}`}
                  />
                ))}
              </div>
              <ul className="mt-4 grid gap-2 sm:grid-cols-2">
                {ruleState.map((rule) => (
                  <li key={rule.id} className={`text-sm font-semibold ${rule.passed ? 'text-emerald-700' : 'text-slate-500'}`}>
                    {rule.passed ? '✓' : '○'} {rule.label}
                  </li>
                ))}
                <li className={`text-sm font-semibold ${confirmPassword && newPassword === confirmPassword ? 'text-emerald-700' : 'text-slate-500'}`}>
                  {confirmPassword && newPassword === confirmPassword ? '✓' : '○'} Passwords match
                </li>
              </ul>
            </div>

            {message ? (
              <div className="mt-5 rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">
                {message}
              </div>
            ) : null}

            <div className="mt-8 flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={!canSubmit || submitting}
                className="rounded-2xl bg-[#237afc] px-6 py-3 text-sm font-black text-white shadow-lg shadow-blue-200 transition hover:bg-[#0f6cbd] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
              >
                {submitting ? 'Updating password...' : 'Create permanent password'}
              </button>
              <button
                type="button"
                onClick={logout}
                className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-black text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
              >
                Sign out
              </button>
            </div>
          </form>
        </section>
      </main>
    </>
  );
}
