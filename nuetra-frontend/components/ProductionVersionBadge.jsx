import { useEffect, useState } from 'react';
import { getBrowserBundleVersion } from '../lib/buildVersion';

function shortSha(sha) {
  if (!sha || sha === 'unknown') return 'unknown';
  return sha.slice(0, 7);
}

export default function ProductionVersionBadge() {
  const [version, setVersion] = useState(null);
  const browserBundle = getBrowserBundleVersion();

  useEffect(() => {
    let active = true;

    fetch('/api/version')
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (active) setVersion(data);
      })
      .catch(() => {
        if (active) setVersion(null);
      });

    return () => {
      active = false;
    };
  }, []);

  const displayVersion = version || browserBundle;

  return (
    <div
      className="fixed bottom-3 right-3 z-[9999] rounded-full border border-gray-200/80 bg-white/90 px-3 py-1.5 text-[11px] font-bold text-gray-600 shadow-lg backdrop-blur"
      title={`Browser bundle commit: ${browserBundle.commit_sha}\nBrowser bundle branch: ${browserBundle.branch}\nBrowser bundle build: ${browserBundle.build_timestamp}\nFrontend runtime commit: ${displayVersion.commit_sha}\nFrontend runtime deployment: ${displayVersion.deployment_id}`}
      data-testid="production-version-badge"
    >
      Build {shortSha(browserBundle.commit_sha)} · {browserBundle.branch || 'unknown'}
    </div>
  );
}
