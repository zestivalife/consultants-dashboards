#!/usr/bin/env node

import { execSync } from 'node:child_process';

const frontendUrl = (process.env.FRONTEND_URL || 'https://consultant.nuetra.in').replace(/\/$/, '');
const gatewayUrl = (process.env.GATEWAY_URL || 'https://api-gateway-production-e2be.up.railway.app').replace(/\/$/, '');
const expectedCommit =
  process.env.EXPECTED_COMMIT ||
  execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
const expectedShort = expectedCommit.slice(0, 7);

async function readJson(label, url) {
  try {
    const response = await fetch(url, { headers: { accept: 'application/json' } });
    const body = await response.json().catch(() => null);
    return { label, url, ok: response.ok, status: response.status, body };
  } catch (error) {
    return { label, url, ok: false, status: 0, error: error.message };
  }
}

function commitOf(record) {
  return record?.commit_sha || record?.runtime?.commit_sha || 'unknown';
}

function statusFor(commit) {
  if (!commit || commit === 'unknown') return 'UNKNOWN';
  return commit.startsWith(expectedShort) || expectedCommit.startsWith(commit) ? 'MATCH' : 'MISMATCH';
}

const checks = [
  await readJson('frontend', `${frontendUrl}/api/version`),
  await readJson('gateway', `${gatewayUrl}/api/v1/version`),
  await readJson('gateway-service-aggregate', `${gatewayUrl}/api/v1/versions`),
  await readJson('frontend-proxied-service-aggregate', `${frontendUrl}/api/gateway/api/v1/versions`),
];

console.log(`Expected commit: ${expectedCommit}`);
console.log('');

for (const check of checks) {
  console.log(`## ${check.label}`);
  console.log(`URL: ${check.url}`);
  console.log(`HTTP: ${check.status}`);
  if (!check.ok) {
    console.log(`Result: FAILED`);
    console.log(`Error: ${check.error || JSON.stringify(check.body)}`);
    console.log('');
    continue;
  }

  if (check.body?.services) {
    for (const [service, version] of Object.entries(check.body.services)) {
      const commit = commitOf(version);
      console.log(`${service}: ${statusFor(commit)} ${commit}`);
    }
  } else {
    const commit = commitOf(check.body);
    console.log(`Result: ${statusFor(commit)} ${commit}`);
    console.log(`Branch: ${check.body?.branch || 'unknown'}`);
    console.log(`Deployment: ${check.body?.deployment_id || 'unknown'}`);
    console.log(`Build: ${check.body?.build_timestamp || 'unknown'}`);
  }
  console.log('');
}
