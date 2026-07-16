import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';

import { onboardingAPI } from '../../lib/api';

const STATE_COPY = {
  loading: {
    title: 'Checking your invitation',
    description: 'We are validating this secure invitation before opening the workspace setup.',
  },
  ready: {
    title: 'You are invited to join Zestiva',
    description: 'Accept this invitation to begin secure account setup.',
  },
  accepted: {
    title: 'Invitation accepted',
    description: 'Your invitation is accepted. Password setup is the next onboarding step.',
  },
  expired: {
    title: 'Invitation expired',
    description: 'This secure invitation has expired. Please ask your organization or platform admin for a new invitation.',
  },
  revoked: {
    title: 'Invitation revoked',
    description: 'This invitation was revoked by an administrator and can no longer be used.',
  },
  invalid: {
    title: 'Invitation invalid',
    description: 'This invitation link is invalid or cannot be verified. Please check the link or request a new invitation.',
  },
  error: {
    title: 'Invitation unavailable',
    description: 'This invitation may be expired, cancelled, already used, or invalid.',
  },
};

function classifyInvitationError(err) {
  const message = String(err?.message || '').toLowerCase();
  if (message.includes('expired')) return 'expired';
  if (message.includes('revoked') || message.includes('cancelled')) return 'revoked';
  if (message.includes('accepted')) return 'accepted';
  if (message.includes('invalid') || message.includes('not found')) return 'invalid';
  return 'error';
}

export default function InvitationAcceptPage() {
  const router = useRouter();
  const token = useMemo(() => {
    const value = router.query.token;
    return Array.isArray(value) ? value[0] : value;
  }, [router.query.token]);

  const [status, setStatus] = useState('loading');
  const [invitation, setInvitation] = useState(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!router.isReady || !token) return;
    let cancelled = false;

    async function validateInvitation() {
      setStatus('loading');
      setError('');
      try {
        const result = await onboardingAPI.validateInvitation(token);
        if (cancelled) return;
        setInvitation(result);
        setStatus('ready');
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Unable to validate invitation.');
        setStatus(classifyInvitationError(err));
      }
    }

    validateInvitation();
    return () => {
      cancelled = true;
    };
  }, [router.isReady, token]);

  async function handleAccept() {
    if (!token || isSubmitting) return;
    setIsSubmitting(true);
    setError('');
    try {
      const accepted = await onboardingAPI.acceptInvitation(token);
      setInvitation(accepted);
      setStatus('accepted');
    } catch (err) {
      setError(err.message || 'Unable to accept invitation.');
      setStatus(classifyInvitationError(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  const copy = STATE_COPY[status] || STATE_COPY.loading;

  return (
    <main className="min-h-screen bg-[#f7f8f5] px-6 py-10 text-[#1f2722]">
      <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-4xl items-center justify-center">
        <div className="w-full rounded-[32px] border border-black/10 bg-white p-8 shadow-[0_24px_80px_rgba(15,23,42,0.10)] md:p-12">
          <div className="mb-10 flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[#4f7f32]">Zestiva Identity</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-[-0.04em] md:text-5xl">{copy.title}</h1>
            </div>
            <div className="rounded-full border border-black/10 px-4 py-2 text-sm font-semibold text-[#4f7f32]">
              Invitation
            </div>
          </div>

          <p className="max-w-2xl text-lg leading-8 text-[#5b625d]">{copy.description}</p>

          {invitation ? (
            <dl className="mt-8 grid gap-4 rounded-3xl bg-[#f3f5ef] p-5 text-sm md:grid-cols-2">
              <div>
                <dt className="font-semibold text-[#6b716c]">Email</dt>
                <dd className="mt-1 text-base font-semibold">{invitation.email}</dd>
              </div>
              <div>
                <dt className="font-semibold text-[#6b716c]">Role</dt>
                <dd className="mt-1 text-base font-semibold">{invitation.role || 'Assigned role'}</dd>
              </div>
              <div>
                <dt className="font-semibold text-[#6b716c]">Organization</dt>
                <dd className="mt-1 text-base font-semibold">{invitation.organization || 'Zestiva workspace'}</dd>
              </div>
              <div>
                <dt className="font-semibold text-[#6b716c]">Next step</dt>
                <dd className="mt-1 text-base font-semibold">{invitation.next_step}</dd>
              </div>
            </dl>
          ) : null}

          {error ? (
            <div className="mt-8 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
              {error}
            </div>
          ) : null}

          <div className="mt-10 flex flex-wrap items-center gap-3">
            {status === 'ready' ? (
              <button
                type="button"
                onClick={handleAccept}
                disabled={isSubmitting}
                className="rounded-full bg-[#3268a8] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[#3268a8]/20 transition hover:bg-[#27558b] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? 'Accepting invitation...' : 'Accept invitation'}
              </button>
            ) : null}
            {status === 'accepted' ? (
              <button
                type="button"
                disabled
                className="rounded-full bg-[#3268a8] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[#3268a8]/20 transition hover:bg-[#27558b]"
              >
                Password setup is next
              </button>
            ) : null}
            {['error', 'expired', 'revoked', 'invalid'].includes(status) ? (
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="rounded-full border border-black/10 bg-white px-6 py-3 text-sm font-semibold text-[#1f2722] transition hover:bg-black/5"
              >
                Return to sign in
              </button>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}
