import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import { Mail, AlertCircle, CheckCircle, Loader2, ArrowLeft } from 'lucide-react';

export default function VerifyOtpPage() {
  const router = useRouter();
  const { email } = router.query;
  const { verifyOtp, isLoading, error, clearError } = useAuth();

  const [otp, setOtp] = useState('');
  const [localError, setLocalError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setSuccess('');

    if (!email) {
      setLocalError('Email not provided. Please go back and register again.');
      return;
    }
    if (!otp || otp.length !== 6) {
      setLocalError('Please enter a valid 6-digit OTP.');
      return;
    }

    const result = await verifyOtp(email, otp);

    if (result && !result.error) {
      setSuccess('Email verified successfully! Redirecting to login...');
      setTimeout(() => router.push('/login'), 2000);
    } else if (result?.error) {
      setLocalError(result.error);
      if (clearError) clearError();
    }
  };

  const displayError = localError || error;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 flex items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-white rounded-xl shadow-2xl p-8"
      >
        <Link href="/register" className="inline-flex items-center text-sm text-gray-600 hover:text-[#64ae00] mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Register
        </Link>

        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Mail className="h-8 w-8 text-[#64ae00]" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Verify Your Email</h1>
          <p className="text-gray-600">
            We sent a 6-digit OTP to{' '}
            <span className="font-medium text-gray-900">{email || 'your email'}</span>
          </p>
        </div>

        <AnimatePresence>
          {(displayError || success) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`mb-6 p-4 rounded-lg flex items-center space-x-2 ${
                displayError ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'
              }`}
            >
              {displayError && <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />}
              {success && <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />}
              <span className={`text-sm ${displayError ? 'text-red-700' : 'text-green-700'}`}>
                {displayError || success}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-2">
              One-Time Password
            </label>
            <input
              id="otp"
              type="text"
              inputMode="numeric"
              maxLength={6}
              required
              value={otp}
              onChange={(e) => {
                setOtp(e.target.value.replace(/\D/g, '').slice(0, 6));
                if (localError) setLocalError('');
                if (error && clearError) clearError();
              }}
              className="w-full text-center text-2xl tracking-[0.5em] px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
              placeholder="------"
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isLoading}
            className="w-full bg-[#64ae00] hover:bg-[#579700] text-white font-bold py-3 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <span>Verify OTP</span>
            )}
          </motion.button>
        </form>

        <p className="text-sm text-gray-500 text-center mt-6">
          Didn&apos;t receive the code? Check your spam folder or{' '}
          <Link href="/register" className="text-[#64ae00] font-medium">register again</Link>.
        </p>
      </motion.div>
    </div>
  );
}
