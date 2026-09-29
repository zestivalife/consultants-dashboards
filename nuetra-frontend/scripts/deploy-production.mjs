import { execFileSync, spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const appDirectory = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repositoryDirectory = resolve(appDirectory, '..');

const git = (...args) =>
  execFileSync('git', args, {
    cwd: repositoryDirectory,
    encoding: 'utf8',
  }).trim();

const commitSha = git('rev-parse', 'HEAD');
const branch = git('branch', '--show-current');
const status = git('status', '--short');

if (!/^[0-9a-f]{40}$/.test(commitSha)) {
  throw new Error('Production deployment requires a full 40-character Git commit SHA.');
}

if (!branch) {
  throw new Error('Production deployment requires a named Git branch.');
}

if (status) {
  throw new Error('Production deployment requires a clean Git worktree.');
}

const result = spawnSync(
  process.platform === 'win32' ? 'npx.cmd' : 'npx',
  [
    'vercel',
    '--prod',
    '--yes',
    '--build-env',
    `NEXT_PUBLIC_BUILD_COMMIT_SHA=${commitSha}`,
    '--build-env',
    `NEXT_PUBLIC_BUILD_BRANCH=${branch}`,
    '--build-env',
    `NEXT_PUBLIC_BUILD_TIMESTAMP=${new Date().toISOString()}`,
  ],
  {
    cwd: repositoryDirectory,
    env: process.env,
    stdio: 'inherit',
  },
);

if (result.error) throw result.error;
process.exit(result.status ?? 1);
