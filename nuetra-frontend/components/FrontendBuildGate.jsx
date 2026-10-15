import { useCallback, useEffect, useState } from 'react';
import { getBrowserBundleVersion } from '../lib/buildVersion';
import {
  BUILD_GATE_STATE,
  BUILD_RELOAD_ATTEMPT_KEY,
  BUILD_SYNC_CHANNEL,
  buildControlledReloadUrl,
  classifyFrontendBuild,
  shouldEnforceBuildIdentity,
} from '../lib/frontendBuildResilience';

function RecoveryScreen({ onRetry, unavailable = false }) {
  return (
    <main className="min-h-screen bg-[#f4f7fb] px-6 py-16 flex items-center justify-center">
      <section className="w-full max-w-lg rounded-3xl border border-[#dbe3ef] bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-bold text-[#071127]">
          {unavailable ? 'Secure update check unavailable' : 'Application update needs attention'}
        </h1>
        <p className="mt-4 text-sm leading-6 text-[#526078]">
          {unavailable
            ? 'We could not confirm the current application version. Your signed-in session has been preserved.'
            : 'A newer version could not be loaded automatically. Your signed-in session has been preserved.'}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-6 min-h-12 rounded-xl bg-[#1769e0] px-6 py-3 font-semibold text-white focus:outline-none focus:ring-4 focus:ring-[#1769e0]/25"
        >
          Retry secure update
        </button>
      </section>
    </main>
  );
}

export default function FrontendBuildGate({ children }) {
  const [state, setState] = useState(
    shouldEnforceBuildIdentity(process.env.NODE_ENV) ? 'CHECKING' : BUILD_GATE_STATE.CURRENT
  );
  const browserBundle = getBrowserBundleVersion();

  const checkRuntime = useCallback(async ({ allowReload = true } = {}) => {
    if (!shouldEnforceBuildIdentity(process.env.NODE_ENV)) {
      setState(BUILD_GATE_STATE.CURRENT);
      return;
    }

    try {
      const response = await fetch(`/api/version?build-check=${Date.now()}`, {
        cache: 'no-store',
        headers: { 'Cache-Control': 'no-cache' },
      });
      if (!response.ok) throw new Error('Runtime identity unavailable');
      const runtime = await response.json();
      const attemptedRuntimeSha = sessionStorage.getItem(BUILD_RELOAD_ATTEMPT_KEY);
      const nextState = classifyFrontendBuild({
        bundleSha: browserBundle.commit_sha,
        runtimeSha: runtime?.commit_sha,
        attemptedRuntimeSha,
      });

      if (nextState === BUILD_GATE_STATE.CURRENT) {
        sessionStorage.removeItem(BUILD_RELOAD_ATTEMPT_KEY);
        setState(nextState);
        return;
      }

      if (nextState === BUILD_GATE_STATE.STALE && allowReload) {
        sessionStorage.setItem(BUILD_RELOAD_ATTEMPT_KEY, runtime.commit_sha);
        try {
          const channel = new BroadcastChannel(BUILD_SYNC_CHANNEL);
          channel.postMessage({ type: 'CURRENT_RUNTIME_SHA', commitSha: runtime.commit_sha });
          channel.close();
        } catch {
          // Runtime checking on every bootstrap remains authoritative.
        }
        setState(nextState);
        window.location.replace(buildControlledReloadUrl(window.location.href, runtime.commit_sha));
        return;
      }

      setState(nextState);
    } catch {
      setState(BUILD_GATE_STATE.RUNTIME_UNAVAILABLE);
    }
  }, [browserBundle.commit_sha]);

  useEffect(() => {
    checkRuntime();
  }, [checkRuntime]);

  useEffect(() => {
    if (!shouldEnforceBuildIdentity(process.env.NODE_ENV) || typeof BroadcastChannel === 'undefined') return undefined;
    const channel = new BroadcastChannel(BUILD_SYNC_CHANNEL);
    channel.onmessage = (event) => {
      if (event?.data?.type === 'CURRENT_RUNTIME_SHA' && event.data.commitSha !== browserBundle.commit_sha) {
        checkRuntime();
      }
    };
    return () => channel.close();
  }, [browserBundle.commit_sha, checkRuntime]);

  if (state === BUILD_GATE_STATE.CURRENT) return children;
  if (state === BUILD_GATE_STATE.RECOVERY_REQUIRED) {
    return <RecoveryScreen onRetry={() => checkRuntime({ allowReload: false })} />;
  }
  if (state === BUILD_GATE_STATE.RUNTIME_UNAVAILABLE) {
    return <RecoveryScreen unavailable onRetry={() => checkRuntime()} />;
  }

  return (
    <main className="min-h-screen bg-[#f4f7fb] flex items-center justify-center px-6">
      <p className="rounded-2xl bg-white px-6 py-4 font-semibold text-[#26344d] shadow-sm" role="status">
        A newer version of the application is available. Updating securely…
      </p>
    </main>
  );
}
