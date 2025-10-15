# Voodoo Control Receiver

Cross-platform desktop app built with Tauri + Svelte + Threlte and a Python core module.

## Requirements
- Node 18+
- Rust toolchain (for Tauri)
- Python 3.10+

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
