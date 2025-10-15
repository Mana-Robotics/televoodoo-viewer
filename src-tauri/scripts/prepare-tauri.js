import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      copyRecursive(path.join(src, entry), path.join(dest, entry));
    }
  } else {
    fs.copyFileSync(src, dest);
  }
}

const repoRoot = path.resolve(__dirname, '..', '..');
const pythonSrc = path.join(repoRoot, 'python');
const resourcesDir = path.join(__dirname, '..', 'resources', 'python');

copyRecursive(pythonSrc, resourcesDir);
console.log(`[prepare-tauri] Copied python -> ${resourcesDir}`);

// Create a venv inside resources and install dependencies and the local package
const venvDir = path.join(resourcesDir, '.venv');
try {
  console.log('[prepare-tauri] Creating virtual environment...');
  execSync(`python3 -m venv "${venvDir}"`, { stdio: 'inherit' });

  const pyBin = path.join(venvDir, 'bin', 'python');
  const pipBin = path.join(venvDir, 'bin', 'pip');

  console.log('[prepare-tauri] Upgrading pip and wheel...');
  execSync(`"${pyBin}" -m pip install -U pip wheel`, { stdio: 'inherit' });

  console.log('[prepare-tauri] Installing requirements...');
  execSync(`"${pipBin}" install -r "${path.join(pythonSrc, 'requirements.txt')}"`, { stdio: 'inherit' });

  console.log('[prepare-tauri] Installing local package...');
  execSync(`"${pipBin}" install "${pythonSrc}"`, { stdio: 'inherit' });
} catch (e) {
  console.warn('[prepare-tauri] Skipped venv creation or installation due to error:', e?.message || e);
}


