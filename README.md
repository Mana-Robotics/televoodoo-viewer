# Televoodoo Viewer

Televoodoo Viewer is a cross‑platform desktop application for visualizing and streaming 6‑DoF poses and scene data. It lets you inspect input poses (e.g., from ArUco/QR workflows) in a 3D view and output transformed poses over JSON/BLE for downstream consumers. The app is built with Tauri + Svelte + Threlte, and includes a Python core module for pose processing.

## Requirements
- Node 18+
- Rust toolchain (for Tauri)
- Python 3.10+

### Install Node and Rust (macOS & Ubuntu)

- macOS
  - Install Node.js: Use Homebrew or the official installer.
    - Homebrew:
      ```
      brew install node
      ```
    - Official Node installer: see Node.js downloads (https://nodejs.org/en/download)
  - Install Rust toolchain: Use rustup (recommended). See Rust installation guide (https://www.rust-lang.org/learn/get-started)
      ```
      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
      ```
- Ubuntu
  - Install Node.js: node, nvm and npm.
    - Download from the official site: see Node.js downloads (https://nodejs.org/en/download)
    - Install according to instructions
  - Rust toolchain: Use rustup (recommended).
    ```
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    ```

## Install
1. Clone the repository
```
git clone https://github.com/Mana-Robotics/televoodoo-viewer.git
cd televoodoo-viewer
```
2. Sync submodules (fetch Python core `televoodoo`)
```
git submodule sync --recursive
git submodule update --init --recursive
```
3. Install dependencies
```
npm install
```


## Run (Development Mode)
```
npm run tauri:dev
```

## Build
```
npm run tauri:build
```

## Notes
- QR content format: see SPECS/QR_CODE_READING_GUIDE.md
- BLE API: see SPECS/BLUETOOTH_API_DOCUMENTATION.md
- Input pose data: see SPECS/INPUT_POSE_DATA_FORMAT.md
- Coordinate systems: World coordinate system equals the reference coordinate system (defined by the scanned ArUco-Marker). The 3D cuboid uses INPUT pose values (reference/world) directly. OUTPUT transforms only affect JSON output.

## Maintainer

Developed with ❤️ for 🤖 by [Mana Robotics](https://www.mana-robotics.com).
## License

MIT License — see [LICENSE](LICENSE) for details.
