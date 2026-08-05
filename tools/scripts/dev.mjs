import { spawn, spawnSync } from 'node:child_process';
import process from 'node:process';

const isWindows = process.platform === 'win32';
const applicationProcesses = new Map();
let stopping = false;
let shutdownTimer;
let desiredExitCode = 0;

const applications = [
  {
    name: 'web',
    command: 'pnpm',
    args: ['--filter', '@ude/web', 'dev'],
  },
  {
    name: 'admin',
    command: 'pnpm',
    args: ['--filter', '@ude/admin', 'dev'],
  },
  {
    name: 'api',
    command: 'uv',
    args: [
      'run',
      'uvicorn',
      'ude_api.main:create_app',
      '--factory',
      '--app-dir',
      'apps/api',
      '--host',
      '127.0.0.1',
      '--port',
      '8000',
      '--reload',
    ],
  },
];

function executable(name) {
  if (!isWindows) return name;
  if (name === 'pnpm') return 'pnpm.cmd';
  if (name === 'uv') return 'uv.exe';
  return name;
}

function run(command, args) {
  const result = spawnSync(executable(command), args, {
    cwd: process.cwd(),
    env: process.env,
    shell: false,
    stdio: 'inherit',
  });
  if (result.error || result.status !== 0) {
    if (result.error) {
      console.error(`Unable to run ${command}: ${result.error.message}`);
    }
    process.exitCode = result.status ?? 1;
    return false;
  }
  return true;
}

function stopProcess(child, signal) {
  if (child.exitCode !== null) return;
  if (isWindows) {
    spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], {
      stdio: 'ignore',
    });
    return;
  }

  try {
    process.kill(-child.pid, signal);
  } catch (error) {
    if (error.code !== 'ESRCH') throw error;
  }
}

function finishIfStopped() {
  if (!stopping || applicationProcesses.size !== 0) return;
  if (shutdownTimer) clearTimeout(shutdownTimer);
  process.exit(desiredExitCode);
}

function beginShutdown(signal, exitCode) {
  desiredExitCode = Math.max(desiredExitCode, exitCode);
  if (stopping) return;
  stopping = true;
  console.log('Stopping web, admin, and API processes...');
  for (const child of applicationProcesses.values()) {
    stopProcess(child, signal);
  }
  finishIfStopped();
  shutdownTimer = setTimeout(() => {
    for (const child of applicationProcesses.values()) {
      stopProcess(child, 'SIGKILL');
    }
    process.exit(desiredExitCode);
  }, 5_000);
}

if (
  !run('docker', [
    'compose',
    'up',
    '-d',
    '--wait',
    '--wait-timeout',
    '120',
    'postgres',
    'minio',
  ])
) {
  process.exit();
}

for (const application of applications) {
  const child = spawn(executable(application.command), application.args, {
    cwd: process.cwd(),
    detached: !isWindows,
    env: process.env,
    shell: false,
    stdio: 'inherit',
  });
  applicationProcesses.set(application.name, child);

  child.once('error', (error) => {
    console.error(`Unable to start ${application.name}: ${error.message}`);
    applicationProcesses.delete(application.name);
    beginShutdown('SIGTERM', 1);
    finishIfStopped();
  });

  child.once('exit', (code, signal) => {
    applicationProcesses.delete(application.name);
    if (!stopping) {
      const reason = signal ? `signal ${signal}` : `exit code ${String(code)}`;
      console.error(`${application.name} stopped unexpectedly with ${reason}.`);
      beginShutdown('SIGTERM', code && code > 0 ? code : 1);
    }
    finishIfStopped();
  });
}

process.once('SIGINT', () => beginShutdown('SIGINT', 0));
process.once('SIGTERM', () => beginShutdown('SIGTERM', 0));
