import { spawnSync } from 'node:child_process';
import process from 'node:process';

const isWindows = process.platform === 'win32';
const pnpm = isWindows ? 'pnpm.cmd' : 'pnpm';
const checks = [
  ['formatting', ['format:check']],
  ['linting', ['lint']],
  ['unit tests', ['test']],
  ['builds', ['build']],
  ['OpenAPI validation', ['api:validate']],
  ['secret scan', ['check:secrets']],
  ['Docker Compose validation', ['compose:validate']],
  [
    'live infrastructure, migration, integration tests, and API smoke test',
    ['test:infra'],
  ],
];

for (const [label, args] of checks) {
  console.log(`\nFoundation verification: ${label}`);
  const result = spawnSync(pnpm, args, {
    cwd: process.cwd(),
    env: process.env,
    shell: false,
    stdio: 'inherit',
  });
  if (result.error || result.status !== 0) {
    console.error(`Foundation verification failed during ${label}.`);
    process.exit(result.status ?? 1);
  }
}

console.log('\nFoundation verification completed successfully.');
