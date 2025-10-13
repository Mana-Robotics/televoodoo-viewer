#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader};
use std::process::{Command, Stdio};
use tauri::Emitter;

#[tauri::command]
async fn start_python(app: tauri::AppHandle) -> Result<(), String> {
    // Prefer project venv python if present
    let venv_python = "../python/.venv/bin/python";
    let python = if std::path::Path::new(venv_python).exists() { venv_python } else { "python3" };
    let mut child = Command::new(python)
        .arg("-m")
        .arg("voodoo_core")
        // during `tauri dev`, the CWD is typically `src-tauri`, so go up one level
        .current_dir("../python")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;

    // take pipes before moving child into threads
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();

    let app_handle = app.clone();
    std::thread::spawn(move || {
        if let Some(stdout) = stdout {
            let reader = BufReader::new(stdout);
            for line in reader.lines() {
                if let Ok(line) = line {
                    let _ = app_handle.emit("python-line", line);
                }
            }
        }
    });

    // forward stderr too
    let app_handle_err = app.clone();
    std::thread::spawn(move || {
        if let Some(stderr) = stderr {
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                if let Ok(line) = line {
                    let _ = app_handle_err.emit("python-error", line);
                }
            }
        }
    });

    Ok(())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![start_python])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}


