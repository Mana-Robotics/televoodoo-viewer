# Televoodoo Viewer

Cross-platform desktop app built with Tauri + Svelte + Threlte and a Python core module.

## Requirements
- Node 18+
- Rust toolchain (for Tauri)
- Python 3.10+

### Install Node and Rust (macOS & Ubuntu)

- macOS
  - Node.js: Use Homebrew or official installer.
    - Homebrew: `brew install node`
    - Or download from the official site: see Node.js downloads (`https://nodejs.org/en/download`)
  - Rust toolchain: Use rustup (recommended).
    - `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
    - Official docs: Rust installation guide (`https://www.rust-lang.org/learn/get-started`)

- Ubuntu
  - Node.js: node, nvm and npm.
    - Download from the official site: see Node.js downloads (`https://nodejs.org/en/download`)
  - Rust toolchain: Use rustup (recommended).
    - `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
    - Official docs: Rust installation guide (`https://www.rust-lang.org/learn/get-started`)

## Install
1. cd /Users/daniel/Code/mana/voodoo-control/VoodooControlDesktop
2. npm install

## Run (frontend only)
- npm run dev

## Run (Tauri app)
- npm run tauri:dev

## Build
- npm run tauri:build

## Notes
- QR content format: see SPECS/QR_CODE_READING_GUIDE.md
- BLE API: see SPECS/BLUETOOTH_API_DOCUMENTATION.md
- Input pose data: see SPECS/INPUT_POSE_DATA_FORMAT.md
 - Coordinate systems: World coordinate system equals the reference coordinate system (ArUco). The 3D cuboid uses INPUT pose values (reference/world) directly. OUTPUT transforms only affect JSON output.
