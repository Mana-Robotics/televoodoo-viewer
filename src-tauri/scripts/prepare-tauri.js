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

// Ensure a dev venv at python/.venv for local development runs
const repoVenvDir = path.join(pythonSrc, '.venv');
try {
  const repoPy = path.join(repoVenvDir, 'bin', 'python');
  const repoPip = path.join(repoVenvDir, 'bin', 'pip');

  const isLinux = process.platform === 'linux';
  if (!fs.existsSync(repoPy)) {
    console.log('[prepare-tauri] Creating dev virtual environment at python/.venv ...');
    const venvFlags = isLinux ? '--system-site-packages' : '';
    execSync(`python3 -m venv ${venvFlags} "${repoVenvDir}"`, { stdio: 'inherit' });
  } else {
    console.log('[prepare-tauri] Dev virtual environment already present');
  }

  console.log('[prepare-tauri] Upgrading pip in dev venv ...');
  execSync(`"${repoPy}" -m pip install -U pip wheel`, { stdio: 'inherit' });

  const repoReq = path.join(televoodooSrc, 'requirements.txt');
  if (fs.existsSync(repoReq)) {
    console.log('[prepare-tauri] Installing Python requirements into dev venv ...');
    execSync(`"${repoPip}" install -U -r "${repoReq}"`, { stdio: 'inherit' });
  }

  // On Linux, verify that dbus is importable; if not, print a helpful hint
  if (isLinux) {
    try {
      execSync(`"${repoPy}" - <<'PY'\nimport importlib, sys\nimportlib.import_module('dbus')\nprint('dbus ok')\nPY`, { stdio: 'inherit', shell: '/bin/bash' });
    } catch (e) {
      console.warn('[prepare-tauri] Python module "dbus" not available. If install fails via pip, install system packages:');
      console.warn('[prepare-tauri]   sudo apt update && sudo apt install -y python3-dbus python3-gi');
      console.warn('[prepare-tauri] Or install build deps then pip install dbus-python:');
      console.warn('[prepare-tauri]   sudo apt install -y libdbus-1-dev libglib2.0-dev && "' + repoPip + '" install dbus-python');
    }
  }
} catch (e) {
  console.warn('[prepare-tauri] Skipped dev venv setup due to error:', e?.message || e);
}

// Note: we do NOT create a venv inside Resources. The app will bootstrap
// a runtime venv under App Support on first launch to avoid dyld issues.


