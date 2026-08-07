import { copyFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import process from 'node:process';

const isWindows = process.platform === 'win32';

function executable(name) {
  return isWindows && name === 'pnpm' ? `${name}.cmd` : name;
}

function run(command, args) {
  const result = spawnSync(executable(command), args, {
    cwd: process.cwd(),
    env: process.env,
    shell: false,
    stdio: 'inherit',
  });
  if (result.error || result.status !== 0) {
    const renderedCommand = [command, ...args].join(' ');
    throw new Error(`Command failed: ${renderedCommand}`);
  }
}

function ensureAvailable(command, args = ['--version']) {
  const result = spawnSync(executable(command), args, {
    shell: false,
    stdio: 'ignore',
  });
  if (result.error || result.status !== 0) {
    throw new Error(`Required tool is unavailable: ${command}`);
  }
}

ensureAvailable('uv');
ensureAvailable('docker');
ensureAvailable('docker', ['compose', 'version']);

if (!existsSync('.env')) {
  copyFileSync('.env.example', '.env');
  console.log('Created .env from safe local development defaults.');
}

run('uv', ['sync', '--frozen']);
run('docker', ['compose', 'config', '--quiet']);
run('docker', [
  'compose',
  'up',
  '-d',
  '--wait',
  '--wait-timeout',
  '120',
  'postgres',
  'minio',
]);
run('uv', ['run', 'alembic', '-c', 'apps/api/alembic.ini', 'upgrade', 'head']);

console.log('Setup complete. Run pnpm dev to start all application shells.');
