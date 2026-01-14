#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Emitter;
use tauri::Manager; // for app.path()

#[cfg(unix)]
use std::os::unix::process::CommandExt;

// Global storage for Python child process to enable cleanup on exit
static PYTHON_CHILD: Mutex<Option<Child>> = Mutex::new(None);

// simple recursive copy helper for bootstrapping runtime python from resources
fn copy_dir_all(src: &std::path::Path, dst: &std::path::Path) -> std::io::Result<()> {
    if !src.exists() {
        return Ok(());
    }
    std::fs::create_dir_all(dst)?;
    for entry in std::fs::read_dir(src)? {
        let entry = entry?;
        let ty = entry.file_type()?;
        if ty.is_dir() {
            copy_dir_all(&entry.path(), &dst.join(entry.file_name()))?;
        } else {
            std::fs::copy(entry.path(), dst.join(entry.file_name()))?;
        }
    }
    Ok(())
}

fn find_bundled_python_dir(app: &tauri::AppHandle) -> Option<std::path::PathBuf> {
    if let Ok(res_dir) = app.path().resource_dir() {
        let candidate1 = res_dir.join("python");
        if candidate1.exists() {
            return Some(candidate1);
        }
        let candidate2 = res_dir.join("resources").join("python");
        if candidate2.exists() {
            return Some(candidate2);
        }
    }
    None
}

/// Configuration for starting the Python sidecar
#[derive(serde::Deserialize)]
struct StartConfig {
    /// Connection type: "wifi", "ble", or "usb"
    connection: String,
    /// Peripheral/server name (optional - uses random if not provided)
    name: Option<String>,
    /// Authentication code (optional - uses random if not provided)
    code: Option<String>,
    /// Upsample poses to target frequency (Hz) using linear extrapolation
    upsample_hz: Option<f64>,
    /// Rate limit pose output to maximum frequency (Hz)
    rate_limit_hz: Option<f64>,
}

#[tauri::command]
async fn start_python(app: tauri::AppHandle, config: StartConfig) -> Result<(), String> {
    // In dev builds, run directly from the repo's python dir and venv
    if cfg!(debug_assertions) {
        // Resolve repo root at compile time (this is the src-tauri dir); go up one to project root
        let repo_root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .ok_or_else(|| "Could not determine repo root".to_string())?
            .to_path_buf();

        let python_dir = repo_root.join("python");
        let dev_python = python_dir.join(".venv").join("bin").join("python");
        let python = if dev_python.exists() {
            dev_python.to_string_lossy().to_string()
        } else {
            "python3".to_string()
        };

        let televoodoo_dir = python_dir.join("televoodoo");
        if !televoodoo_dir.exists() {
            return Err(format!("televoodoo directory not found at: {}", televoodoo_dir.display()));
        }
        let televoodoo_src = televoodoo_dir.join("src");
        if !televoodoo_src.exists() {
            return Err(format!("televoodoo src directory not found at: {}", televoodoo_src.display()));
        }

        let mut cmd = Command::new(&python);
        cmd.arg("-m").arg("televoodoo")
            .arg("--connection").arg(&config.connection)
            .current_dir(&televoodoo_dir)
            .env("PYTHONPATH", televoodoo_src.to_string_lossy().to_string());
        
        // Add optional name and code
        if let Some(ref name) = config.name {
            cmd.arg("--name").arg(name);
        }
        if let Some(ref code) = config.code {
            cmd.arg("--code").arg(code);
        }
        // Add optional upsampling and rate limiting
        if let Some(hz) = config.upsample_hz {
            cmd.arg("--upsample-hz").arg(hz.to_string());
        }
        if let Some(hz) = config.rate_limit_hz {
            cmd.arg("--rate-limit-hz").arg(hz.to_string());
        }

        // Ensure pyobjc on macOS for dev
        #[cfg(target_os = "macos")]
        {
            if let Ok(status) = Command::new(&cmd.get_program())
                .args(["-c", "import objc"]) // simple import test
                .current_dir(cmd.get_current_dir().unwrap_or_else(|| std::path::Path::new(".")))
                .status()
            {
                if !status.success() {
                    let _ = Command::new(&cmd.get_program())
                        .args(["-m", "pip", "install", "pyobjc"])
                        .current_dir(cmd.get_current_dir().unwrap_or_else(|| std::path::Path::new(".")))
                        .status();
                }
            }
        }

        // AppImage and some launchers may inject Python-related env vars that break venvs.
        // For dev, we KEEP PYTHONPATH (we set it above) but sanitize the rest.
        cmd.env_remove("PYTHONHOME")
            .env_remove("PYTHONEXECUTABLE")
            .env_remove("PYTHONUSERBASE")
            .env("PYTHONUNBUFFERED", "1");

        // On Unix, create new process group for cleaner termination
        #[cfg(unix)]
        unsafe {
            cmd.pre_exec(|| {
                // Create new process group with this process as leader
                libc::setpgid(0, 0);
                Ok(())
            });
        }

        let mut child = cmd
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| e.to_string())?;

        let stdout = child.stdout.take();
        let stderr = child.stderr.take();
        
        // Store child process for cleanup on exit
        if let Ok(mut guard) = PYTHON_CHILD.lock() {
            // Kill any existing Python process first
            if let Some(mut old_child) = guard.take() {
                let _ = old_child.kill();
            }
            *guard = Some(child);
        }
        
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
        return Ok(());
    }

    // Always prefer a runtime venv under App Support and bootstrap it from bundled Resources if missing.
    let mut python = "python3".to_string();
    if let Ok(app_data_dir) = app.path().app_data_dir() {
        let runtime_py_dir = app_data_dir.join("python");
        let runtime_venv_bin = runtime_py_dir.join(".venv").join("bin");
        let runtime_python = runtime_venv_bin.join("python");
        let runtime_pip = runtime_venv_bin.join("pip");

        if !runtime_python.exists() {
            if let Some(bundled) = find_bundled_python_dir(&app) {
                let televoodoo_dir = bundled.join("televoodoo");
                let pyproject = televoodoo_dir.join("pyproject.toml");
                if pyproject.exists() {
                    let _ = std::fs::create_dir_all(&runtime_py_dir);
                    let runtime_televoodoo = runtime_py_dir.join("televoodoo");
                    let _ = copy_dir_all(&televoodoo_dir, &runtime_televoodoo);
                    let _ = Command::new("python3").arg("-m").arg("venv").arg(runtime_py_dir.join(".venv")).status();
                    if runtime_pip.exists() {
                        let _ = Command::new(&runtime_python).arg("-m").arg("pip").arg("install").arg("-U").arg("pip").status();
                        let req = televoodoo_dir.join("requirements.txt");
                        if req.exists() {
                            let _ = Command::new(&runtime_python).arg("-m").arg("pip").arg("install").arg("-r").arg(&req).status();
                        }
                        let _ = Command::new(&runtime_python).arg("-m").arg("pip").arg("install").arg(&runtime_televoodoo).status();
                    }
                }
            }
        }
        if runtime_python.exists() {
            python = runtime_python.to_string_lossy().to_string();
        }
    }

    let mut cmd = Command::new(python);
    cmd.arg("-m").arg("televoodoo")
        .arg("--connection").arg(&config.connection);
    
    // Add optional name and code
    if let Some(ref name) = config.name {
        cmd.arg("--name").arg(name);
    }
    if let Some(ref code) = config.code {
        cmd.arg("--code").arg(code);
    }
    // Add optional upsampling and rate limiting
    if let Some(hz) = config.upsample_hz {
        cmd.arg("--upsample-hz").arg(hz.to_string());
    }
    if let Some(hz) = config.rate_limit_hz {
        cmd.arg("--rate-limit-hz").arg(hz.to_string());
    }

    // Packaged: prefer bundled Resources/python/televoodoo, else runtime app_data/python/televoodoo
    if let Some(bundled_py) = find_bundled_python_dir(&app) {
        let televoodoo_bundled = bundled_py.join("televoodoo");
        if televoodoo_bundled.join("pyproject.toml").exists() {
            cmd.current_dir(&televoodoo_bundled);
        }
    } else if let Ok(app_data_dir) = app.path().app_data_dir() {
        let televoodoo_runtime = app_data_dir.join("python").join("televoodoo");
        if televoodoo_runtime.join("pyproject.toml").exists() {
            cmd.current_dir(&televoodoo_runtime);
        }
    }

    // Only ensure pyobjc on macOS; Linux must not try to install it
    #[cfg(target_os = "macos")]
    {
        if let Ok(status) = Command::new(&cmd.get_program())
            .args(["-c", "import objc"]) // simple import test
            .current_dir(cmd.get_current_dir().unwrap_or_else(|| std::path::Path::new(".")))
            .status()
        {
            if !status.success() {
                let _ = Command::new(&cmd.get_program())
                    .args(["-m", "pip", "install", "pyobjc"])
                    .current_dir(cmd.get_current_dir().unwrap_or_else(|| std::path::Path::new(".")))
                    .status();
            }
        }
    }

    // Clean up Python-related env vars that AppImage sets (PYTHONHOME, PYTHONPATH, ...)
    cmd.env_remove("PYTHONHOME")
        .env_remove("PYTHONPATH")
        .env_remove("PYTHONEXECUTABLE")
        .env_remove("PYTHONUSERBASE")
        .env("PYTHONUNBUFFERED", "1");

    // On Unix, create new process group for cleaner termination
    #[cfg(unix)]
    unsafe {
        cmd.pre_exec(|| {
            // Create new process group with this process as leader
            libc::setpgid(0, 0);
            Ok(())
        });
    }

    let mut child = cmd
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;

    // take pipes before moving child into threads
    let stdout = child.stdout.take();
    let stderr = child.stderr.take();

    // Store child process for cleanup on exit
    if let Ok(mut guard) = PYTHON_CHILD.lock() {
        // Kill any existing Python process first
        if let Some(mut old_child) = guard.take() {
            let _ = old_child.kill();
        }
        *guard = Some(child);
    }

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

#[tauri::command]
async fn stop_python() -> Result<(), String> {
    cleanup_python();
    Ok(())
}

/// Cleanup function to gracefully terminate the Python child process
fn cleanup_python() {
    if let Ok(mut guard) = PYTHON_CHILD.lock() {
        if let Some(mut child) = guard.take() {
            #[cfg(unix)]
            {
                let pid = child.id() as i32;
                // First try SIGTERM for graceful shutdown
                unsafe { libc::kill(pid, libc::SIGTERM); }
                
                // Give it a short moment to respond
                std::thread::sleep(Duration::from_millis(100));
                
                // Check if it exited
                match child.try_wait() {
                    Ok(Some(_)) => return, // Already exited gracefully
                    _ => {
                        // Process didn't exit, try killing the entire process group
                        // This ensures any child processes/threads are also killed
                        unsafe { libc::kill(-pid, libc::SIGKILL); }
                        
                        // Also send SIGKILL to the specific process
                        unsafe { libc::kill(pid, libc::SIGKILL); }
                        
                        // Wait for process to finish
                        let _ = child.wait();
                    }
                }
            }
            #[cfg(not(unix))]
            {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![start_python, stop_python])
        .on_window_event(|window, event| {
            match event {
                // Handle close request to cleanup before window is destroyed
                tauri::WindowEvent::CloseRequested { .. } => {
                    if window.label() == "main" {
                        cleanup_python();
                    }
                }
                // Also handle destroyed as backup
                tauri::WindowEvent::Destroyed => {
                    if window.label() == "main" {
                        cleanup_python();
                    }
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
    
    // Also cleanup on normal exit
    cleanup_python();
}


