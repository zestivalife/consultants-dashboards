import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, MailCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function ForgotPasswordPage() {
  const { requestPasswordReset } = useAuth();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    const result = await requestPasswordReset(email);
    setMessage(result.message || 'Reset flow simulated.');
    setIsSubmitting(false);
  }

  return (
    <div className="fluent-page flex min-h-screen items-center justify-center px-4 py-6">
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.26, ease: 'easeOut' }}
        className="fluent-card w-full max-w-lg rounded-[32px] p-8"
      >
        <Link href="/login" className="inline-flex items-center gap-2 text-sm text-[#0f6cbd] transition hover:text-[#0f548c]">
          <ArrowLeft className="h-4 w-4" />
          Back to login
        </Link>
        <h1 className="mt-6 text-3xl font-semibold text-[#242424]">Forgot password</h1>
        <p className="mt-3 text-sm leading-6 text-[#424242]">
          This is a frontend-only sample flow. Enter any preloaded practitioner email and the screen will simulate a reset request while keeping the platform free of backend dependencies.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm text-[#424242]">Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm outline-none focus:border-[#0f6cbd]"
              placeholder="aditi.kulkarni@nuetra.in"
              required
            />
          </label>
          <motion.button whileTap={{ scale: 0.99 }} disabled={isSubmitting} className="fluent-primary-button w-full rounded-[24px] px-4 py-4 text-sm font-medium transition disabled:opacity-70">
            {isSubmitting ? 'Simulating reset...' : 'Send reset instructions'}
          </motion.button>
        </form>

        <AnimatePresence>
          {message ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mt-6 flex items-start gap-3 rounded-[22px] border border-[#107c10]/20 bg-[#107c10]/10 p-4 text-sm text-[#0f6a0f]"
            >
              <MailCheck className="mt-0.5 h-4 w-4" />
              <span>{message}</span>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
