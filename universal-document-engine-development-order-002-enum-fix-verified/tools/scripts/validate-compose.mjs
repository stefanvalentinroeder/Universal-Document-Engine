import { spawnSync } from 'node:child_process';
import process from 'node:process';

const validationEnvironment = {
  ...process.env,
  POSTGRES_DB: process.env.POSTGRES_DB ?? 'ude_validation',
  POSTGRES_USER: process.env.POSTGRES_USER ?? 'ude_validation',
  POSTGRES_PASSWORD: process.env.POSTGRES_PASSWORD ?? 'ude_validation_local_only',
  MINIO_ROOT_USER: process.env.MINIO_ROOT_USER ?? 'ude_validation',
  MINIO_ROOT_PASSWORD: process.env.MINIO_ROOT_PASSWORD ?? 'ude_validation_local_only',
};

const result = spawnSync('docker', ['compose', 'config', '--quiet'], {
  cwd: process.cwd(),
  env: validationEnvironment,
  shell: false,
  stdio: 'inherit',
});

if (result.error) {
  console.error(`Docker Compose is unavailable: ${result.error.message}`);
  process.exitCode = 1;
} else if (result.status !== 0) {
  process.exitCode = result.status ?? 1;
} else {
  console.log('Docker Compose configuration is valid.');
}
