import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  const stat = fs.statSync(src);
  const base = path.basename(src);
  // Skip virtual environments and git metadata
  if (base === '.venv' || base === '.git') return;
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
const televoodooSrc = path.join(pythonSrc, 'televoodoo');
const resourcesDir = path.join(__dirname, '..', 'resources', 'python');
const televoodooResources = path.join(resourcesDir, 'televoodoo');

// Ensure a clean replacement of televoodoo contents on each run
try {
  if (fs.existsSync(televoodooResources)) {
    fs.rmSync(televoodooResources, { recursive: true, force: true });
    console.log('[prepare-tauri] Removed existing televoodoo in resources');
  }
  // Also ensure packaged venv is recreated fresh (avoid copying source .venv)
  const packagedVenv = path.join(resourcesDir, '.venv');
  if (fs.existsSync(packagedVenv)) {
    fs.rmSync(packagedVenv, { recursive: true, force: true });
    console.log('[prepare-tauri] Removed existing resources venv');
  }
} catch (e) {
  console.warn('[prepare-tauri] Failed to remove existing televoodoo:', e?.message || e);
}

// Copy the entire python directory (including televoodoo submodule)
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
  const reqFile = path.join(televoodooResources, 'requirements.txt');
  if (fs.existsSync(reqFile)) {
    execSync(`"${pipBin}" install -U -r "${reqFile}"`, { stdio: 'inherit' });
  }

  console.log('[prepare-tauri] Installing local televoodoo package...');
  if (fs.existsSync(televoodooResources)) {
    execSync(`"${pipBin}" install -U "${televoodooResources}"`, { stdio: 'inherit' });
  } else {
    console.warn('[prepare-tauri] televoodoo directory not found in resources, skipping package install');
  }
} catch (e) {
  console.warn('[prepare-tauri] Skipped venv creation or installation due to error:', e?.message || e);
}


