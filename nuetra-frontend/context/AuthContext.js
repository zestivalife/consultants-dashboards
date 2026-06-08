import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { findUserByCredentials, findUserByEmail, sampleUsers } from '../data/mockPlatformData';
import { getDashboardPathForRole } from '../lib/roleRoutes';

const SESSION_KEY = 'nuetra_mock_session';
const RESET_KEY = 'nuetra_mock_reset';

const AuthContext = createContext(null);

function readStoredSession() {
  if (typeof window === 'undefined') return null;

  const raw = localStorage.getItem(SESSION_KEY) || sessionStorage.getItem(SESSION_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function persistSession(session, rememberMe) {
  if (typeof window === 'undefined') return;

  const serialized = JSON.stringify(session);
  if (rememberMe) {
    localStorage.setItem(SESSION_KEY, serialized);
    sessionStorage.removeItem(SESSION_KEY);
  } else {
    sessionStorage.setItem(SESSION_KEY, serialized);
    localStorage.removeItem(SESSION_KEY);
  }
}

function clearStoredSession() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(SESSION_KEY);
}

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const session = readStoredSession();
    if (session?.user) {
      setUser(session.user);
    }
    setIsLoading(false);
  }, []);

  const clearError = () => setError(null);

  async function login({ email, password, rememberMe = true, redirect = true }) {
    setIsLoading(true);
    setError(null);

    const matchedUser = findUserByCredentials(email, password);

    if (!matchedUser) {
      const nextError = 'Invalid sample credentials. Use one of the practitioner accounts shown below.';
      setError(nextError);
      setIsLoading(false);
      return { error: nextError };
    }

    const session = {
      user: matchedUser,
      loggedInAt: new Date().toISOString(),
      mode: 'sample-data',
    };

    setUser(matchedUser);
    persistSession(session, rememberMe);
    setIsLoading(false);

    if (redirect) {
      router.replace(getDashboardPathForRole(matchedUser.role));
    }

    return { user: matchedUser };
  }

  async function logout() {
    clearStoredSession();
    setUser(null);
    router.replace('/login');
  }

  async function register(payload) {
    setIsLoading(true);
    setError(null);

    const email = payload?.email?.trim();
    if (!email) {
      const nextError = 'Email is required.';
      setError(nextError);
      setIsLoading(false);
      return { error: nextError };
    }

    const matchedUser = findUserByEmail(email);
    if (matchedUser) {
      setIsLoading(false);
      return {
        success: true,
        data: {
          mode: 'sample-data',
          message: 'This sample frontend already includes this practitioner account. Use the login screen credentials card to sign in.',
        },
      };
    }

    setIsLoading(false);
    return {
      success: true,
      data: {
        mode: 'sample-data',
        message: 'Registration is simulated in this frontend-only environment. Use one of the preloaded mock accounts to explore complete workflows.',
      },
    };
  }

  async function verifyOtp(email, otp) {
    setIsLoading(false);
    return {
      success: true,
      data: {
        email,
        otp,
        mode: 'sample-data',
        message: 'OTP verification is simulated for the sample frontend.',
      },
    };
  }

  async function refreshSession() {
    const session = readStoredSession();
    if (session?.user) {
      setUser(session.user);
      return true;
    }
    return false;
  }

  async function requestPasswordReset(email) {
    const matchedUser = findUserByEmail(email);
    if (typeof window !== 'undefined') {
      localStorage.setItem(
        RESET_KEY,
        JSON.stringify({
          email,
          exists: Boolean(matchedUser),
          requestedAt: new Date().toISOString(),
        })
      );
    }

    return {
      success: true,
      message: matchedUser
        ? `Reset instructions simulated for ${matchedUser.name}.`
        : 'Reset request captured in sample mode.',
    };
  }

  const value = useMemo(
    () => ({
      user,
      isLoading,
      error,
      login,
      logout,
      register,
      verifyOtp,
      refreshSession,
      requestPasswordReset,
      clearError,
      sampleUsers,
    }),
    [user, isLoading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
