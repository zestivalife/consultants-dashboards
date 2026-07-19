import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { ArrowRight, KeyRound, Mail, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getDashboardPathForRole } from '../lib/roleRoutes';
import { SAMPLE_PASSWORD, getRoleDisplayName } from '../data/mockPlatformData';

export default function LoginPage() {
  const { login, user, isLoading, error, clearError, sampleUsers, isBackendAuthEnabled } = useAuth();
  const [form, setForm] = useState({ email: isBackendAuthEnabled ? '' : sampleUsers?.[0]?.email || '', password: isBackendAuthEnabled ? '' : SAMPLE_PASSWORD, rememberMe: true });
  const groupedUsers = useMemo(() => sampleUsers || [], [sampleUsers]);

  useEffect(() => {
    if (!isLoading && user?.role) {
      window.location.replace(getDashboardPathForRole(user.role));
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
    <div className="fluent-page min-h-screen">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-[-10%] top-[-8%] h-[420px] w-[420px] rounded-full bg-[#dbeafe] blur-3xl" />
        <div className="absolute right-[-10%] top-[8%] h-[380px] w-[380px] rounded-full bg-[#dcfce7] blur-3xl" />
        <div className="absolute bottom-[-12%] left-[24%] h-[320px] w-[320px] rounded-full bg-[#fef3c7] blur-3xl" />
      </div>

      <div className="relative mx-auto grid min-h-screen max-w-[1480px] gap-8 px-4 py-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.28, ease: 'easeOut' }}
          className="fluent-card flex flex-col justify-between rounded-[36px] p-7 backdrop-blur"
        >
          <div>
            <Image
              src="/zestiva-logo.png"
              alt="Zestiva"
              width={313}
              height={114}
              className="h-auto w-[180px] object-contain"
              priority
            />
            <p className="mt-5 text-xs uppercase tracking-[0.28em] text-[#0f6cbd]">Zestiva Consultant Dashboard</p>
            <h1 className="mt-5 max-w-3xl text-4xl font-semibold leading-tight text-[#242424] sm:text-5xl">
              Adaptive wellness operations for Indian nutrition and recovery intelligence.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-[#424242]">
              {isBackendAuthEnabled
                ? 'The dashboard is connected to the live platform API so provisioned consultants and organization admins can sign in with real accounts.'
                : 'This frontend is fully operational on production-quality sample data. Every workflow is complete: priority queue, inbox, longitudinal employee workspace, editable AI plan builder, session operations, reports, finance, quality review, and organization intelligence.'}
            </p>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {[
              ['Operational prioritization', 'Critical cases, approvals, follow-ups, and escalations stay visible without turning into analytics clutter.'],
              ['Indian-native plan logic', 'Meal frameworks reflect Maharashtrian, Gujarati, Punjabi, South Indian, and Bengali food behavior.'],
              ['Role-aware maturity', 'Consultant, senior consultant, mentor, and organization admin each get a tuned home view and action path.'],
            ].map(([title, body]) => (
              <motion.div key={title} whileHover={{ y: -2 }} transition={{ duration: 0.16 }} className="fluent-card-subtle fluent-card-hover rounded-[24px] p-5">
                <p className="font-medium text-[#242424]">{title}</p>
                <p className="mt-3 text-sm leading-6 text-[#424242]">{body}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.05 }}
          className="fluent-card rounded-[36px] p-6 backdrop-blur sm:p-8"
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
              <span className="mb-2 block text-sm text-[#424242]">Email</span>
              <div className="fluent-input flex items-center gap-3 rounded-[22px] px-4 py-3 focus-within:border-[#0f6cbd]">
                <Mail className="h-4 w-4 text-[#616161]" />
                <input
                  type="email"
                  value={form.email}
                  onChange={(event) => {
                    clearError();
                    setForm((current) => ({ ...current, email: event.target.value }));
                  }}
                  className="w-full bg-transparent text-sm text-[#242424] outline-none placeholder:text-[#616161]"
                  placeholder={isBackendAuthEnabled ? 'admin@company.com' : 'name@nuetra.in'}
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
              <Link href="/forgot-password" className="text-[#0f6cbd] transition hover:text-[#0f548c]">
                Forgot password
              </Link>
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
