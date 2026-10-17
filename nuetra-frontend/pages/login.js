import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, KeyRound, Mail, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getPostAuthPathForUser } from '../lib/roleRoutes';
import { SAMPLE_PASSWORD, getRoleDisplayName } from '../data/mockPlatformData';
import PublicHeader from '../components/public-consultant/PublicHeader';
import AuthStoryPanel from '../components/public-consultant/AuthStoryPanel';

export default function LoginPage() {
  const { login, user, isLoading, error, clearError, sampleUsers, isBackendAuthEnabled } = useAuth();
  const [form, setForm] = useState({ email: isBackendAuthEnabled ? '' : sampleUsers?.[0]?.email || '', password: isBackendAuthEnabled ? '' : SAMPLE_PASSWORD, rememberMe: true });
  const groupedUsers = useMemo(() => sampleUsers || [], [sampleUsers]);

  useEffect(() => {
    if (!isLoading && user?.role) {
      window.location.replace(getPostAuthPathForUser(user));
    }
  }, [isLoading, user]);

  if (!isLoading && user?.role) {
    return (
      <div className="fluent-page min-h-screen flex items-center justify-center">
        <div className="fluent-card rounded-[28px] px-8 py-7 text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-[#0f6cbd] border-t-transparent" />
          <p className="mt-4 text-sm text-[#616161]">Returning to your workspace…</p>
        </div>
      </div>
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await login(form);
  }

  return (
    <div className="min-h-screen bg-[#f3f2ed]">
      <PublicHeader action="signup" />
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-[-10%] top-[-8%] h-[420px] w-[420px] rounded-full bg-[#dbeafe] blur-3xl" />
        <div className="absolute right-[-10%] top-[8%] h-[380px] w-[380px] rounded-full bg-[#dcfce7] blur-3xl" />
        <div className="absolute bottom-[-12%] left-[24%] h-[320px] w-[320px] rounded-full bg-[#fef3c7] blur-3xl" />
      </div>

      <div className="relative mx-auto grid min-h-screen max-w-[1480px] items-start gap-6 px-4 pb-8 pt-28 sm:px-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(420px,0.9fr)] lg:px-8">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.28, ease: 'easeOut' }}
          className="order-2 min-w-0 lg:order-1"
        >
          <AuthStoryPanel mode="login" />
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.05 }}
          className="fluent-card order-1 w-full min-w-0 max-w-[560px] self-start justify-self-end rounded-[36px] p-6 backdrop-blur sm:p-8 lg:order-2"
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-[#0f6cbd]">{isBackendAuthEnabled ? 'Secure access' : 'Sample access'}</p>
              <h2 className="mt-2 text-3xl font-semibold text-[#242424]">{isBackendAuthEnabled ? 'Sign in to your workspace' : 'Sign in instantly'}</h2>
            </div>
            <div className="rounded-full border border-[#107c10]/20 bg-[#107c10]/10 px-3 py-1.5 text-xs text-[#0f6a0f]">
              {isBackendAuthEnabled ? 'Connected to backend' : 'Frontend-only mode'}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <label className="block">
              <span className="mb-2 block text-sm text-[#424242]">Email or mobile number</span>
              <div className="fluent-input flex items-center gap-3 rounded-[22px] px-4 py-3 focus-within:border-[#0f6cbd]">
                <Mail className="h-4 w-4 text-[#616161]" />
                <input
                  type="text"
                  value={form.email}
                  onChange={(event) => {
                    clearError();
                    setForm((current) => ({ ...current, email: event.target.value }));
                  }}
                  className="w-full bg-transparent text-sm text-[#242424] outline-none placeholder:text-[#616161]"
                  placeholder={isBackendAuthEnabled ? 'name@company.com or +91 mobile' : 'name@nuetra.in'}
                />
              </div>
            </label>

            <label className="block">
              <span className="mb-2 block text-sm text-[#424242]">Password</span>
              <div className="fluent-input flex items-center gap-3 rounded-[22px] px-4 py-3 focus-within:border-[#0f6cbd]">
                <KeyRound className="h-4 w-4 text-[#616161]" />
                <input
                  type="password"
                  value={form.password}
                  onChange={(event) => {
                    clearError();
                    setForm((current) => ({ ...current, password: event.target.value }));
                  }}
                  className="w-full bg-transparent text-sm text-[#242424] outline-none placeholder:text-[#616161]"
                  placeholder={isBackendAuthEnabled ? 'Enter your password' : 'Enter sample password'}
                />
              </div>
            </label>

            <div className="flex items-center justify-between text-sm text-[#616161]">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.rememberMe}
                  onChange={(event) => setForm((current) => ({ ...current, rememberMe: event.target.checked }))}
                  className="h-4 w-4 rounded border border-[rgba(0,0,0,0.16)] bg-transparent"
                />
                {isBackendAuthEnabled ? 'Keep me signed in' : 'Keep sample session active'}
              </label>
              <span className="text-[#616161]">Contact your administrator to reset access.</span>
            </div>

            {error ? <div className="rounded-[20px] border border-[#d13438]/20 bg-[#d13438]/10 px-4 py-3 text-sm text-[#b10e1c]">{error}</div> : null}

            <motion.button
              whileTap={{ scale: 0.99 }}
              disabled={isLoading}
              type="submit"
              className="fluent-primary-button flex w-full items-center justify-center gap-2 rounded-[24px] px-4 py-4 text-sm font-medium transition disabled:opacity-70"
            >
              Enter workspace
              <ArrowRight className="h-4 w-4" />
            </motion.button>
          </form>

          {isBackendAuthEnabled ? (
            <div className="mt-5 rounded-[24px] border border-[#0f6cbd]/20 bg-[#0f6cbd]/5 p-4 text-center">
              <p className="text-sm text-[#424242]">External consultant or practice owner?</p>
              <Link href="/signup" className="mt-3 inline-flex items-center gap-2 font-medium text-[#0f6cbd] hover:underline">
                Create consultant workspace
                <ArrowRight className="h-4 w-4" />
              </Link>
              <p className="mt-2 text-xs text-[#616161]">New consultants create a password; returning consultants sign in with email or mobile and password.</p>
            </div>
          ) : null}

          {!isBackendAuthEnabled ? (
            <div className="fluent-card-subtle mt-8 rounded-[26px] p-5">
              <div className="flex items-center gap-2 text-sm text-[#0f6a0f]">
                <ShieldCheck className="h-4 w-4" />
                Shared sample password: <span className="font-medium text-[#242424]">{SAMPLE_PASSWORD}</span>
              </div>
              <div className="mt-4 space-y-3">
                {groupedUsers.map((account) => (
                  <motion.button
                    key={account.id}
                    type="button"
                    onClick={() => setForm({ email: account.email, password: SAMPLE_PASSWORD, rememberMe: true })}
                    whileHover={{ y: -2, borderColor: 'rgba(255,255,255,0.18)' }}
                    whileTap={{ scale: 0.995 }}
                    className="fluent-card-subtle fluent-card-hover flex w-full items-start justify-between gap-3 rounded-[22px] px-4 py-4 text-left"
                  >
                    <div>
                      <p className="font-medium text-[#242424]">{account.name}</p>
                      <p className="mt-1 text-sm text-[#616161]">{account.email}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-[#0f6cbd]">{getRoleDisplayName(account.role)}</p>
                      <p className="mt-1 text-xs text-[#616161]">{account.focus}</p>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          ) : null}
        </motion.section>
      </div>
    </div>
  );
}
