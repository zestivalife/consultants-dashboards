import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';

import { onboardingAPI } from '../../../lib/api';

const COMMON_PASSWORDS = new Set([
  'password',
  'password1',
  'password123',
  'password123!',
  'qwerty123',
  'qwerty123!',
  'admin123',
  'admin123!',
  'welcome123',
  'welcome123!',
  'zestiva123',
  'zestiva123!',
]);

const ERROR_COPY = {
  expired: {
    title: 'Invitation expired',
    description: 'This invitation has expired. Ask your administrator to send a fresh invite.',
  },
  revoked: {
    title: 'Invitation revoked',
    description: 'This invitation was revoked and can no longer be used.',
  },
  invalid: {
    title: 'Invitation invalid',
    description: 'This invitation link could not be verified.',
  },
  already_used: {
    title: 'Credentials already created',
    description: 'This invitation has already been used. Return to sign in with your account.',
  },
  error: {
    title: 'Credential setup unavailable',
    description: 'We could not open credential setup for this invitation.',
  },
};

function classifyCredentialError(err) {
  const message = String(err?.message || '').toLowerCase();
  if (message.includes('expired')) return 'expired';
  if (message.includes('revoked') || message.includes('cancelled')) return 'revoked';
  if (message.includes('password_created') || message.includes('credentials') || message.includes('already')) {
    return 'already_used';
  }
  if (message.includes('invalid') || message.includes('not found')) return 'invalid';
  return 'error';
}

function buildPasswordChecks(password, confirmPassword) {
  return [
    { key: 'length', label: 'At least 12 characters', passed: password.length >= 12 },
    { key: 'uppercase', label: 'One uppercase letter', passed: /[A-Z]/.test(password) },
    { key: 'lowercase', label: 'One lowercase letter', passed: /[a-z]/.test(password) },
    { key: 'number', label: 'One number', passed: /\d/.test(password) },
    { key: 'special', label: 'One special character', passed: /[^A-Za-z0-9]/.test(password) },
    {
      key: 'common',
      label: 'Not a common password',
      passed: password.length === 0 ? false : !COMMON_PASSWORDS.has(password.trim().toLowerCase()),
    },
    {
      key: 'match',
      label: 'Passwords match',
      passed: password.length > 0 && password === confirmPassword,
    },
  ];
}

function strengthLabel(score) {
  if (score >= 6) return 'Strong';
  if (score >= 4) return 'Good';
  if (score >= 2) return 'Needs work';
  return 'Weak';
}

export default function CredentialCreationPage() {
  const router = useRouter();
  const token = useMemo(() => {
    const value = router.query.token;
    return Array.isArray(value) ? value[0] : value;
  }, [router.query.token]);

  const [status, setStatus] = useState('loading');
  const [invitation, setInvitation] = useState(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const checks = useMemo(() => buildPasswordChecks(password, confirmPassword), [password, confirmPassword]);
  const score = checks.filter((check) => check.passed).length;
  const canSubmit = status === 'ready' && checks.every((check) => check.passed) && !isSubmitting;

  useEffect(() => {
    if (!router.isReady) return;
    if (!token) {
      setStatus('invalid');
      return;
    }

    let cancelled = false;
    async function prepareCredentialSetup() {
      setStatus('loading');
      setError('');
      try {
        const result = await onboardingAPI.initiatePasswordSetup(token);
        if (cancelled) return;
        setInvitation(result);
        setStatus('ready');
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Unable to start credential setup.');
        setStatus(classifyCredentialError(err));
      }
    }

    prepareCredentialSetup();
    return () => {
      cancelled = true;
    };
  }, [router.isReady, token]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canSubmit || !token) return;

    setIsSubmitting(true);
    setError('');
    try {
      const result = await onboardingAPI.createCredentials(token, password, confirmPassword);
      setInvitation(result);
      setStatus('success');
      setPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err.message || 'Unable to create credentials.');
      if (String(err?.message || '').toLowerCase().includes('invitation')) {
        setStatus(classifyCredentialError(err));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const terminalCopy = ERROR_COPY[status];

  return (
    <>
      <Head>
        <title>Create credentials | Zestiva Identity</title>
      </Head>
      <main className="min-h-screen bg-[#f7f8f5] px-5 py-8 text-[#1f2722] sm:px-8">
        <section className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl items-center gap-8 lg:grid-cols-[0.95fr_1.05fr]">
          <aside className="rounded-[32px] border border-black/10 bg-white p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-[#4f7f32]">Zestiva Identity</p>
            <h1 className="mt-4 text-4xl font-semibold tracking-[-0.045em] md:text-5xl">
              Create secure workspace credentials.
            </h1>
            <p className="mt-5 text-base leading-7 text-[#5b625d]">
              Your invitation has been accepted. Set a strong password to protect your account before returning to sign in.
            </p>

            {invitation ? (
              <dl className="mt-8 grid gap-4 rounded-3xl bg-[#f3f5ef] p-5 text-sm">
                <div>
                  <dt className="font-semibold text-[#6b716c]">Email</dt>
                  <dd className="mt-1 text-base font-semibold">{invitation.email}</dd>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <dt className="font-semibold text-[#6b716c]">Status</dt>
                    <dd className="mt-1 text-base font-semibold">{invitation.status}</dd>
                  </div>
                  <div>
                    <dt className="font-semibold text-[#6b716c]">Next step</dt>
                    <dd className="mt-1 text-base font-semibold">{invitation.next_step}</dd>
                  </div>
                </div>
              </dl>
            ) : null}
          </aside>

          <section className="rounded-[32px] border border-black/10 bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.10)] sm:p-8">
            {status === 'loading' ? (
              <div className="space-y-5" role="status" aria-live="polite">
                <div className="h-4 w-40 animate-pulse rounded-full bg-black/10" />
                <div className="h-10 w-3/4 animate-pulse rounded-2xl bg-black/10" />
                <div className="h-48 animate-pulse rounded-3xl bg-black/5" />
              </div>
            ) : null}

            {terminalCopy ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#a4523d]">Action needed</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">{terminalCopy.title}</h2>
                <p className="mt-4 text-base leading-7 text-[#5b625d]">{terminalCopy.description}</p>
                {error ? (
                  <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
                    {error}
                  </div>
                ) : null}
                <button
                  type="button"
                  onClick={() => router.push('/login')}
                  className="mt-8 rounded-full bg-[#3268a8] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#27558b]"
                >
                  Return to sign in
                </button>
              </div>
            ) : null}

            {status === 'success' ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#4f7f32]">Credentials created</p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">Your account is secured.</h2>
                <p className="mt-4 text-base leading-7 text-[#5b625d]">
                  Your credentials were created successfully. Continue to sign in and complete the next onboarding step.
                </p>
                <button
                  type="button"
                  onClick={() => router.push('/login')}
                  className="mt-8 rounded-full bg-[#3268a8] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#27558b]"
                >
                  Return to sign in
                </button>
              </div>
            ) : null}

            {status === 'ready' ? (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#4f7f32]">Credential creation</p>
                  <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">Set your password</h2>
                </div>

                <div>
                  <label htmlFor="password" className="text-sm font-semibold text-[#3e4640]">
                    Password
                  </label>
                  <div className="mt-2 flex rounded-2xl border border-black/10 bg-[#f8faf7] px-4 py-3 focus-within:border-[#3268a8]">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      autoComplete="new-password"
                      className="min-w-0 flex-1 bg-transparent text-base font-semibold outline-none"
                      aria-describedby="password-policy"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      className="ml-3 text-sm font-semibold text-[#3268a8]"
                    >
                      {showPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirm-password" className="text-sm font-semibold text-[#3e4640]">
                    Confirm password
                  </label>
                  <div className="mt-2 flex rounded-2xl border border-black/10 bg-[#f8faf7] px-4 py-3 focus-within:border-[#3268a8]">
                    <input
                      id="confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(event) => setConfirmPassword(event.target.value)}
                      autoComplete="new-password"
                      className="min-w-0 flex-1 bg-transparent text-base font-semibold outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword((value) => !value)}
                      className="ml-3 text-sm font-semibold text-[#3268a8]"
                    >
                      {showConfirmPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>

                <div aria-label={`Password strength ${strengthLabel(score)}`}>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span className="font-semibold">Password strength</span>
                    <span className="font-semibold text-[#4f7f32]">{strengthLabel(score)}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-black/10">
                    <div
                      className="h-full rounded-full bg-[#58b000] transition-all"
                      style={{ width: `${Math.max(8, Math.round((score / checks.length) * 100))}%` }}
                    />
                  </div>
                </div>

                <ul id="password-policy" className="grid gap-3 rounded-3xl bg-[#f3f5ef] p-5 text-sm sm:grid-cols-2">
                  {checks.map((check) => (
                    <li key={check.key} className="flex items-center gap-3">
                      <span
                        aria-hidden="true"
                        className={`flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold ${
                          check.passed ? 'bg-[#58b000] text-white' : 'bg-white text-[#8c928d]'
                        }`}
                      >
                        {check.passed ? '✓' : '•'}
                      </span>
                      <span className={check.passed ? 'font-semibold text-[#1f2722]' : 'text-[#5b625d]'}>
                        {check.label}
                      </span>
                    </li>
                  ))}
                </ul>

                {error ? (
                  <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
                    {error}
                  </div>
                ) : null}

                <div className="flex flex-wrap gap-3">
                  <button
                    type="submit"
                    disabled={!canSubmit}
                    className="rounded-full bg-[#3268a8] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[#3268a8]/20 transition hover:bg-[#27558b] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isSubmitting ? 'Creating credentials...' : 'Create credentials'}
                  </button>
                  <button
                    type="button"
                    onClick={() => router.push('/login')}
                    className="rounded-full border border-black/10 bg-white px-6 py-3 text-sm font-semibold text-[#1f2722] transition hover:bg-black/5"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : null}
          </section>
        </section>
      </main>
    </>
  );
}
