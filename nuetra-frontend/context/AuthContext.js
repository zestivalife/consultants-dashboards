import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { findUserByCredentials, sampleUsers } from '../data/mockPlatformData';
import {
  canAccessDashboardLocation,
  getAccountActionRoute,
  getDashboardPathForUser,
  getPostAuthPathForUser,
} from '../lib/roleRoutes';
import { authAPI, clearTokens, getRefreshToken, getToken, isRememberedAuthSession, setRefreshToken, setToken } from '../lib/api';
import {
  getExternalTemporaryPasswordIdentifier,
  isExternalTemporaryPasswordUser,
  isSameTemporaryPasswordUser,
} from '../lib/temporaryPasswordBootstrap';
import { needsFiteatsyProfessionalClaimRefresh } from '../lib/fiteatsyProfessionalClaim';

const SESSION_KEY = 'nuetra_session';
const LOGOUT_EVENT_KEY = 'nuetra_logout_event';
const EXTERNAL_WORKSPACE_CACHE_PREFIXES = ['external-consultant:', 'external-client:', 'nuetra-external:'];
const BACKEND_AUTH_ENABLED = Boolean(process.env.NEXT_PUBLIC_API_URL);

const AuthContext = createContext(null);

function getPostLoginPath(user) {
  return getPostAuthPathForUser(user);
}

async function getGovernedPostLoginPath(user) {
  // Account-security actions are authoritative and must never depend on
  // workspace/onboarding availability. In particular, a temporary-password
  // session must remain usable while the password is being replaced.
  const accountActionRoute = getAccountActionRoute(user);
  if (accountActionRoute) return accountActionRoute;

  return getPostLoginPath(user);
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

function clearExternalWorkspaceCaches() {
  if (typeof window === 'undefined') return;
  for (const storage of [localStorage, sessionStorage]) {
    for (let index = storage.length - 1; index >= 0; index -= 1) {
      const key = storage.key(index);
      if (key && EXTERNAL_WORKSPACE_CACHE_PREFIXES.some((prefix) => key.startsWith(prefix))) {
        storage.removeItem(key);
      }
    }
  }
}

function clearBrowserSessionState() {
  clearTokens();
  clearStoredSession();
  clearExternalWorkspaceCaches();
}

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const storedSession = readStoredSessionRecord();
    if (!BACKEND_AUTH_ENABLED && storedSession?.session?.user) {
      setUser(storedSession.session.user);
    }

    const hasStoredTokens = Boolean(getToken() || getRefreshToken());

    if (BACKEND_AUTH_ENABLED && hasStoredTokens) {
      const rememberMe = storedSession?.rememberMe ?? isRememberedAuthSession();
      const refreshProfessionalClaim = async () => {
        const refreshToken = getRefreshToken();
        if (
          refreshToken
          && needsFiteatsyProfessionalClaimRefresh({ token: getToken(), user: storedSession?.session?.user })
        ) {
          try {
            const freshTokens = await authAPI.refresh(refreshToken);
            if (freshTokens?.access_token) setToken(freshTokens.access_token, rememberMe);
            if (freshTokens?.refresh_token) setRefreshToken(freshTokens.refresh_token, rememberMe);
          } catch {
            // Preserve the existing access token. The normal authenticated
            // request path remains responsible for session-expiry handling.
          }
        }
        return refreshSession({ rememberMe });
      };

      refreshProfessionalClaim()
        .catch(() => {
          clearStoredSession();
          clearTokens();
          setUser(null);
        })
        .finally(() => setIsLoading(false));
      return;
    }

    if (!BACKEND_AUTH_ENABLED) {
      setIsLoading(false);
      return;
    }

    fetch('/api/qa/session', { credentials: 'same-origin', cache: 'no-store' })
      .then(async response => response.ok ? response.json() : null)
      .then(payload => {
        if (!payload?.user || payload.user.accountPurpose !== 'QA_TEST') {
          clearStoredSession();
          setUser(null);
          return;
        }
        const session = { user: payload.user, loggedInAt: new Date().toISOString(), mode: 'qa-server-session', rememberMe: false };
        setUser(payload.user); persistSession(session, false);
      })
      .catch(() => {
        clearStoredSession();
        setUser(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    const handleRemoteLogout = (event) => {
      if (event.key !== LOGOUT_EVENT_KEY || !event.newValue) return;
      clearBrowserSessionState();
      setUser(null);
      if (window.location.pathname !== '/login') window.location.replace('/login');
    };
    window.addEventListener('storage', handleRemoteLogout);
    return () => window.removeEventListener('storage', handleRemoteLogout);
  }, []);

  const clearError = () => setError(null);

  async function login({ email, password, mfaCode = '', rememberMe = true, redirect = true }) {
    setIsLoading(true);
    setError(null);

    if (BACKEND_AUTH_ENABLED) {
      try {
        const response = await authAPI.login(email, password, mfaCode);
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

        if (redirect) window.location.replace(await getGovernedPostLoginPath(nextUser));

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
      router.replace(getDashboardPathForUser(matchedUser));
    }

    return { user: matchedUser };
  }

  async function logout() {
    if (readStoredSession()?.mode === 'qa-server-session') {
      await fetch('/api/qa/session', { method: 'DELETE', credentials: 'same-origin' }).catch(() => null);
    }
    if (BACKEND_AUTH_ENABLED) {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          await authAPI.logout(refreshToken);
        } catch {
          // Best effort logout; always clear client-side state.
        }
      }
    }
    clearBrowserSessionState();
    setUser(null);
    localStorage.setItem(LOGOUT_EVENT_KEY, `${Date.now()}:${globalThis.crypto?.randomUUID?.() || Math.random()}`);
    window.location.replace('/login');
  }

  async function completeTemporaryPasswordChange({ currentPassword, newPassword, confirmPassword }) {
    if (!BACKEND_AUTH_ENABLED) {
      return { error: 'Temporary password changes require backend authentication.' };
    }

    setIsLoading(true);
    setError(null);
    try {
      // External temporary-password setup can be resumed after a frontend
      // release or stale-tab recovery has preserved the account metadata but
      // lost its short-lived access token. Re-authenticate the submitted
      // temporary credential for the exact same External user before changing
      // it. Internal and privileged account flows remain untouched.
      if (isExternalTemporaryPasswordUser(user)) {
        const identifier = getExternalTemporaryPasswordIdentifier(user);
        if (!identifier) {
          throw new Error('External account identifier is unavailable. Return to sign in and try again.');
        }

        const freshLogin = await authAPI.login(identifier, currentPassword);
        const authenticatedUser = freshLogin?.user;
        const freshTokens = freshLogin?.tokens;
        if (
          !isSameTemporaryPasswordUser(user, authenticatedUser)
          || getAccountActionRoute(authenticatedUser) !== '/auth/change-temporary-password'
          || !freshTokens?.access_token
        ) {
          throw new Error('Temporary password authority could not be verified. Return to sign in and try again.');
        }

        const rememberExternalSession = isRememberedAuthSession();
        setToken(freshTokens.access_token, rememberExternalSession);
        if (freshTokens.refresh_token) {
          setRefreshToken(freshTokens.refresh_token, rememberExternalSession);
        }
      }

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
      router.replace(getPostAuthPathForUser(nextUser));
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
          const postAuthPath = await getGovernedPostLoginPath(nextUser);
          if (
            postAuthPath
            && router.pathname !== postAuthPath
            && router.pathname.startsWith('/dashboard')
            && !canAccessDashboardLocation(nextUser, router.pathname, router.query)
          ) {
            router.replace(postAuthPath);
          }
          return true;
        }
      } catch {
        // Only /auth/me failure invalidates authentication. Governed routing
        // resolves fail-closed and does not throw from getGovernedPostLoginPath.
        clearBrowserSessionState();
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
