import { existsSync, readdirSync, rmSync } from 'node:fs';
import { resolve } from 'node:path';

const targets = [
  '.mypy_cache',
  '.nx',
  '.pytest_cache',
  '.ruff_cache',
  'apps/admin/.next',
  'apps/web/.next',
  'coverage',
  'dist',
];

for (const target of targets) {
  const absoluteTarget = resolve(target);
  if (existsSync(absoluteTarget)) {
    rmSync(absoluteTarget, { force: true, recursive: true });
    console.log(`Removed ${target}`);
  }
}

function removePythonCaches(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    if (entry.name === 'node_modules' || entry.name === '.venv') continue;

    const path = resolve(directory, entry.name);
    if (entry.name === '__pycache__') {
      rmSync(path, { force: true, recursive: true });
      console.log(`Removed ${path}`);
    } else {
      removePythonCaches(path);
    }
  }
}

removePythonCaches(process.cwd());
