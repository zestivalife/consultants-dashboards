/**
 * @deprecated — use lib/api.js instead.
 * This file re-exports auth helpers for backward compatibility with
 * components that haven't been migrated yet.
 */
export { authAPI as default, authAPI, getToken, setToken, clearTokens } from './api';
