import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import process from 'node:process';

const excludedDirectories = new Set([
  '.git',
  '.next',
  '.nx',
  '.venv',
  'dist',
  'node_modules',
]);

const forbiddenFilePatterns = [
  /(^|\/)\.env$/,
  /(^|\/)(credentials|service-account)\.json$/i,
  /(^|\/)id_(rsa|dsa|ecdsa|ed25519)$/,
  /\.(key|p12|pfx|pem)$/i,
];

const forbiddenContentPatterns = [
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,
  /\bAKIA[0-9A-Z]{16}\b/,
  /\bgh[oprs]_[A-Za-z0-9]{30,}\b/,
];

function filesystemFiles(directory) {
  const files = [];
  for (const entry of readdirSync(directory)) {
    if (excludedDirectories.has(entry)) continue;
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) {
      files.push(...filesystemFiles(path));
    } else {
      files.push(relative(process.cwd(), path));
    }
  }
  return files;
}

function candidateFiles() {
  if (!existsSync('.git'))
    return filesystemFiles(process.cwd()).filter((path) => path !== '.env');
  try {
    const output = execFileSync('git', ['ls-files', '-z'], { encoding: 'utf8' });
    return output.split('\0').filter(Boolean);
  } catch {
    return filesystemFiles(process.cwd()).filter((path) => path !== '.env');
  }
}

const findings = [];
for (const path of candidateFiles()) {
  if (forbiddenFilePatterns.some((pattern) => pattern.test(path))) {
    findings.push(`${path}: forbidden secret-file pattern`);
    continue;
  }
  if (path.endsWith('pnpm-lock.yaml') || path.endsWith('uv.lock')) continue;
  let content;
  try {
    content = readFileSync(path, 'utf8');
  } catch {
    continue;
  }
  if (forbiddenContentPatterns.some((pattern) => pattern.test(content))) {
    findings.push(`${path}: possible embedded credential`);
  }
}

if (findings.length > 0) {
  console.error(findings.join('\n'));
  process.exitCode = 1;
} else {
  console.log('No common committed secret files or credential patterns found.');
}
