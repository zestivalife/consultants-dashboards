const STARTED_AT = new Date().toISOString();

function firstEnv(...names) {
  for (const name of names) {
    const value = process.env[name];
    if (value) return value;
  }
  return 'unknown';
}

export function getFrontendVersion() {
  return {
    service: 'zestiva-consultant-frontend',
    app_version: process.env.npm_package_version || '1.0.0',
    environment: firstEnv('VERCEL_ENV', 'APP_ENV', 'NODE_ENV'),
    commit_sha: firstEnv('VERCEL_GIT_COMMIT_SHA', 'GIT_COMMIT_SHA', 'COMMIT_SHA', 'NEXT_PUBLIC_BUILD_COMMIT_SHA', 'NEXT_PUBLIC_GIT_COMMIT_SHA'),
    branch: firstEnv('VERCEL_GIT_COMMIT_REF', 'GIT_BRANCH', 'BRANCH', 'NEXT_PUBLIC_BUILD_BRANCH', 'NEXT_PUBLIC_GIT_BRANCH'),
    build_timestamp:
      firstEnv('BUILD_TIMESTAMP', 'NEXT_PUBLIC_BUILD_TIMESTAMP', 'VERCEL_DEPLOYMENT_CREATED_AT', 'NEXT_PUBLIC_VERCEL_DEPLOYMENT_CREATED_AT') === 'unknown'
        ? STARTED_AT
        : firstEnv('BUILD_TIMESTAMP', 'NEXT_PUBLIC_BUILD_TIMESTAMP', 'VERCEL_DEPLOYMENT_CREATED_AT', 'NEXT_PUBLIC_VERCEL_DEPLOYMENT_CREATED_AT'),
    runtime_started_at: STARTED_AT,
    deployment_id: firstEnv('VERCEL_DEPLOYMENT_ID', 'DEPLOYMENT_ID', 'NEXT_PUBLIC_BUILD_DEPLOYMENT_ID', 'NEXT_PUBLIC_VERCEL_DEPLOYMENT_ID'),
    deployment_url: firstEnv('VERCEL_URL', 'NEXT_PUBLIC_VERCEL_URL'),
    runtime: 'vercel',
  };
}

export function getBrowserBundleVersion() {
  return {
    commit_sha: process.env.NEXT_PUBLIC_BUILD_COMMIT_SHA || 'unknown',
    branch: process.env.NEXT_PUBLIC_BUILD_BRANCH || 'unknown',
    build_timestamp: process.env.NEXT_PUBLIC_BUILD_TIMESTAMP || 'unknown',
    deployment_id: process.env.NEXT_PUBLIC_BUILD_DEPLOYMENT_ID || 'unknown',
  };
}
