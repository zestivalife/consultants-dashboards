const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [],
  outputFileTracingRoot: path.join(__dirname),
  env: {
    NEXT_PUBLIC_BUILD_COMMIT_SHA:
      process.env.VERCEL_GIT_COMMIT_SHA ||
      process.env.GIT_COMMIT_SHA ||
      process.env.COMMIT_SHA ||
      process.env.NEXT_PUBLIC_GIT_COMMIT_SHA ||
      'unknown',
    NEXT_PUBLIC_BUILD_BRANCH:
      process.env.VERCEL_GIT_COMMIT_REF ||
      process.env.GIT_BRANCH ||
      process.env.BRANCH ||
      process.env.NEXT_PUBLIC_GIT_BRANCH ||
      'unknown',
    NEXT_PUBLIC_BUILD_TIMESTAMP:
      process.env.BUILD_TIMESTAMP ||
      process.env.NEXT_PUBLIC_BUILD_TIMESTAMP ||
      new Date().toISOString(),
    NEXT_PUBLIC_BUILD_DEPLOYMENT_ID:
      process.env.VERCEL_DEPLOYMENT_ID ||
      process.env.DEPLOYMENT_ID ||
      process.env.NEXT_PUBLIC_VERCEL_DEPLOYMENT_ID ||
      'unknown',
  },
};

module.exports = nextConfig;
