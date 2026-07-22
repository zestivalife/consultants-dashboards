import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { findUserByCredentials, sampleUsers } from '../data/mockPlatformData';
import { getDashboardPathForRole } from '../lib/roleRoutes';
import { authAPI, clearTokens, getRefreshToken, isRememberedAuthSession, setRefreshToken, setToken } from '../lib/api';

const SESSION_KEY = 'nuetra_session';
const BACKEND_AUTH_ENABLED = Boolean(process.env.NEXT_PUBLIC_API_URL);

const AuthContext = createContext(null);

function getPostLoginPath(user) {
  if (user?.must_change_password) {
    return '/auth/change-temporary-password';
  }
  return getDashboardPathForRole(user?.role);
}

function readStoredSessionRecord() {
  if (typeof window === 'undefined') return null;

  const localRaw = localStorage.getItem(SESSION_KEY);
  const sessionRaw = sessionStorage.getItem(SESSION_KEY);
  const raw = localRaw || sessionRaw;
  if (!raw) return null;

  try {
    return {
      session: JSON.parse(raw),
      rememberMe: Boolean(localRaw),
    };
  } catch {
    return null;
  }
}

function readStoredSession() {
  return readStoredSessionRecord()?.session || null;
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
    const storedSession = readStoredSessionRecord();
    if (storedSession?.session?.user) {
      setUser(storedSession.session.user);
    }

    if (BACKEND_AUTH_ENABLED) {
      refreshSession({ rememberMe: storedSession?.rememberMe ?? isRememberedAuthSession() })
        .catch(() => {
          clearStoredSession();
          clearTokens();
          setUser(null);
        })
        .finally(() => setIsLoading(false));
      return;
    }

    setIsLoading(false);
  }, []);

  const clearError = () => setError(null);

  async function login({ email, password, rememberMe = true, redirect = true }) {
    setIsLoading(true);
    setError(null);

    if (BACKEND_AUTH_ENABLED) {
      try {
        const response = await authAPI.login(email, password);
        const nextUser = response?.user;
        const tokens = response?.tokens;

        if (!nextUser || !tokens?.access_token) {
          throw new Error('Login response is incomplete.');
        }

        setToken(tokens.access_token, rememberMe);
        if (tokens.refresh_token) {
          setRefreshToken(tokens.refresh_token, rememberMe);
        }

        const session = {
          user: nextUser,
          loggedInAt: new Date().toISOString(),
          mode: 'backend',
          rememberMe,
        };

        setUser(nextUser);
        persistSession(session, rememberMe);
        setIsLoading(false);

        if (redirect) {
          window.location.replace(getPostLoginPath(nextUser));
        }

        return { user: nextUser };
      } catch (nextError) {
        const message = nextError?.message || 'Unable to sign in.';
        setError(message);
        setIsLoading(false);
        return { error: message };
      }
    }

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
    if (BACKEND_AUTH_ENABLED) {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          await authAPI.logout(refreshToken);
        } catch {
          // Best effort logout; always clear client-side state.
        }
      }
      clearTokens();
    }
    clearStoredSession();
    setUser(null);
    router.replace('/login');
  }

  async function completeTemporaryPasswordChange({ currentPassword, newPassword, confirmPassword }) {
    if (!BACKEND_AUTH_ENABLED) {
      return { error: 'Temporary password changes require backend authentication.' };
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await authAPI.changeTemporaryPassword(currentPassword, newPassword, confirmPassword);
      const nextUser = response?.user;
      const tokens = response?.tokens;
      const rememberMe = isRememberedAuthSession();

      if (!nextUser || !tokens?.access_token) {
        throw new Error('Password change response is incomplete.');
      }

      setToken(tokens.access_token, rememberMe);
      if (tokens.refresh_token) {
        setRefreshToken(tokens.refresh_token, rememberMe);
      }

      const session = {
        user: nextUser,
        loggedInAt: new Date().toISOString(),
        mode: 'backend',
        rememberMe,
      };

      setUser(nextUser);
      persistSession(session, rememberMe);
      setIsLoading(false);
      router.replace(getDashboardPathForRole(nextUser.role));
      return { user: nextUser };
    } catch (nextError) {
      const message = nextError?.message || 'Unable to change temporary password.';
      setError(message);
      setIsLoading(false);
      return { error: message };
    }
  }

  async function refreshSession(options = {}) {
    if (BACKEND_AUTH_ENABLED) {
      try {
        const rememberMe = options.rememberMe ?? isRememberedAuthSession();
        const nextUser = await authAPI.me();
        if (nextUser) {
          const session = {
            user: nextUser,
            loggedInAt: new Date().toISOString(),
            mode: 'backend',
            rememberMe,
          };
          setUser(nextUser);
          persistSession(session, rememberMe);
          if (nextUser.must_change_password && router.pathname !== '/auth/change-temporary-password') {
            router.replace('/auth/change-temporary-password');
          }
          return true;
        }
      } catch {
        clearStoredSession();
        clearTokens();
        setUser(null);
      }
      return false;
    }

    const session = readStoredSession();
    if (session?.user) {
      setUser(session.user);
      return true;
    }
    return false;
  }

  const value = useMemo(
    () => ({
      user,
      isLoading,
      error,
      login,
      logout,
      completeTemporaryPasswordChange,
      refreshSession,
      clearError,
      sampleUsers,
      isBackendAuthEnabled: BACKEND_AUTH_ENABLED,
    }),
    [user, isLoading, error]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
