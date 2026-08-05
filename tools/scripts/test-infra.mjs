import { spawn, spawnSync } from 'node:child_process';
import { closeSync, mkdtempSync, openSync, readFileSync, rmSync } from 'node:fs';
import net from 'node:net';
import { join } from 'node:path';
import process from 'node:process';
import { tmpdir } from 'node:os';

const isWindows = process.platform === 'win32';
const projectName = `ude-foundation-${process.pid}-${Date.now()}`.toLowerCase();
const temporaryDirectory = mkdtempSync(join(tmpdir(), 'ude-foundation-'));
const apiLogPath = join(temporaryDirectory, 'api.log');
let apiLogDescriptor;
let apiProcess;
let infrastructureEnvironment;
let composeStarted = false;
let cleaningUp = false;

function executable(name) {
  if (isWindows && (name === 'pnpm' || name === 'uv')) return `${name}.exe`;
  return name;
}

function run(command, args, options = {}) {
  const result = spawnSync(executable(command), args, {
    cwd: process.cwd(),
    env: options.env ?? infrastructureEnvironment ?? process.env,
    shell: false,
    stdio: options.quiet ? 'ignore' : 'inherit',
  });
  if (!options.allowFailure && (result.error || result.status !== 0)) {
    const renderedCommand = [command, ...args].join(' ');
    const reason = result.error
      ? `: ${result.error.message}`
      : ` with exit code ${String(result.status)}`;
    throw new Error(`Command failed: ${renderedCommand}${reason}`);
  }
  return result;
}

function compose(args, options = {}) {
  return run('docker', ['compose', '--project-name', projectName, ...args], options);
}

async function freePort() {
  return await new Promise((resolve, reject) => {
    const server = net.createServer();
    server.unref();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      if (!address || typeof address === 'string') {
        server.close();
        reject(new Error('Unable to allocate an isolated TCP port'));
        return;
      }
      const { port } = address;
      server.close((error) => (error ? reject(error) : resolve(port)));
    });
  });
}

async function waitForResponse(url, timeoutMilliseconds = 30_000) {
  const deadline = Date.now() + timeoutMilliseconds;
  while (Date.now() < deadline) {
    if (apiProcess?.exitCode !== null) {
      throw new Error('API process stopped before the smoke test completed');
    }
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2_000) });
      if (response.status === 200) return response;
    } catch {
      // Startup connection errors are expected until Uvicorn is accepting work.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function smokeApi(apiPort) {
  const baseUrl = `http://127.0.0.1:${apiPort}`;
  const healthResponse = await waitForResponse(`${baseUrl}/health`);
  const health = await healthResponse.json();
  if (health.status !== 'healthy') throw new Error('/health payload is invalid');

  const readyResponse = await fetch(`${baseUrl}/ready`);
  const ready = await readyResponse.json();
  if (
    readyResponse.status !== 200 ||
    ready.status !== 'ready' ||
    ready.checks?.database?.status !== 'up' ||
    ready.checks?.object_storage?.status !== 'up'
  ) {
    throw new Error('/ready did not report both dependencies as available');
  }

  const openapiResponse = await fetch(`${baseUrl}/openapi.json`);
  const openapi = await openapiResponse.json();
  if (
    openapiResponse.status !== 200 ||
    openapi.info?.title !== 'Universal Document Engine API'
  ) {
    throw new Error('/openapi.json payload is invalid');
  }

  console.log('API smoke test passed for /health, /ready, and /openapi.json.');
}

function stopApi() {
  if (!apiProcess || apiProcess.exitCode !== null) return;
  if (isWindows) {
    spawnSync('taskkill', ['/PID', String(apiProcess.pid), '/T', '/F'], {
      stdio: 'ignore',
    });
  } else {
    try {
      process.kill(-apiProcess.pid, 'SIGTERM');
    } catch (error) {
      if (error.code !== 'ESRCH') throw error;
    }
  }
}

function diagnostics() {
  if (composeStarted) {
    console.error('\nContainer status:');
    compose(['ps', '--all'], { allowFailure: true });
    console.error('\nContainer logs:');
    compose(['logs', '--no-color', 'postgres', 'minio'], {
      allowFailure: true,
    });
  }
  try {
    const apiLog = readFileSync(apiLogPath, 'utf8');
    if (apiLog) console.error(`\nAPI log:\n${apiLog}`);
  } catch {
    // The API log does not exist when failure occurs before API startup.
  }
}

function cleanup() {
  if (cleaningUp) return;
  cleaningUp = true;
  stopApi();
  if (apiLogDescriptor !== undefined) {
    closeSync(apiLogDescriptor);
    apiLogDescriptor = undefined;
  }
  if (composeStarted) {
    compose(['down', '--volumes', '--remove-orphans'], { allowFailure: true });
  }
  rmSync(temporaryDirectory, { force: true, recursive: true });
}

function handleSignal(signal) {
  console.error(`Received ${signal}; cleaning isolated infrastructure.`);
  diagnostics();
  cleanup();
  process.exit(signal === 'SIGINT' ? 130 : 143);
}

process.once('SIGINT', () => handleSignal('SIGINT'));
process.once('SIGTERM', () => handleSignal('SIGTERM'));

try {
  run('docker', ['compose', 'version'], { env: process.env, quiet: true });
  run('uv', ['--version'], { env: process.env, quiet: true });

  const [postgresPort, minioApiPort, minioConsolePort, apiPort] = await Promise.all([
    freePort(),
    freePort(),
    freePort(),
    freePort(),
  ]);
  infrastructureEnvironment = {
    ...process.env,
    APP_ENV: 'test',
    API_HOST: '127.0.0.1',
    API_PORT: String(apiPort),
    CORS_ORIGINS: 'http://localhost:3000,http://localhost:3001',
    POSTGRES_DB: 'ude_foundation',
    POSTGRES_USER: 'ude_foundation',
    POSTGRES_PASSWORD: 'ude_foundation_local_only',
    POSTGRES_PORT: String(postgresPort),
    DATABASE_URL:
      `postgresql+asyncpg://ude_foundation:ude_foundation_local_only` +
      `@127.0.0.1:${postgresPort}/ude_foundation`,
    MINIO_ROOT_USER: 'ude_foundation',
    MINIO_ROOT_PASSWORD: 'ude_foundation_local_only',
    MINIO_API_PORT: String(minioApiPort),
    MINIO_CONSOLE_PORT: String(minioConsolePort),
    MINIO_ENDPOINT: `http://127.0.0.1:${minioApiPort}`,
    NEXT_PUBLIC_API_BASE_URL: `http://127.0.0.1:${apiPort}`,
    RUN_INFRA_TESTS: '1',
  };

  console.log(`Using isolated Compose project ${projectName}.`);
  compose(['config', '--quiet']);
  composeStarted = true;
  compose(['up', '-d', '--wait', '--wait-timeout', '120', 'postgres', 'minio']);
  run('uv', ['run', 'alembic', '-c', 'apps/api/alembic.ini', 'upgrade', 'head']);
  run('uv', ['run', 'pytest', '-m', 'integration', 'tests/integration']);

  apiLogDescriptor = openSync(apiLogPath, 'a');
  apiProcess = spawn(
    executable('uv'),
    [
      'run',
      'uvicorn',
      'ude_api.main:create_app',
      '--factory',
      '--app-dir',
      'apps/api',
      '--host',
      '127.0.0.1',
      '--port',
      String(apiPort),
    ],
    {
      cwd: process.cwd(),
      detached: !isWindows,
      env: infrastructureEnvironment,
      shell: false,
      stdio: ['ignore', apiLogDescriptor, apiLogDescriptor],
    },
  );
  await smokeApi(apiPort);
  console.log('Isolated infrastructure verification completed successfully.');
} catch (error) {
  console.error(`Infrastructure verification failed: ${error.message}`);
  diagnostics();
  process.exitCode = 1;
} finally {
  cleanup();
}
