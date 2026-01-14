import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { connectionStatus, connectionType, outputJson, connectionName, accessCode, wifiIp, wifiPort, inputPose, originPose, outputConfig, serviceState, type ConnectionType, type ServiceConfig } from './store';
import { computeOutput } from './transform';
import { log } from './log';

let currentStatus: 'disconnected' | 'connecting' | 'connected' = 'disconnected';
let lastActivityMs = 0;
let inactivityTimer: number | null = null;
let unlistenStdout: (() => void) | null = null;
let unlistenStderr: (() => void) | null = null;

function setStatus(next: 'disconnected' | 'connecting' | 'connected') {
  if (currentStatus === next) return;
  currentStatus = next;
  connectionStatus.set(next);
  log('info', `Connection status -> ${next}`);
}

function processMessage(msg: any) {
  if (msg.type === 'session') {
    connectionName.set(msg.name);
    accessCode.set(msg.code);
    if (msg.transport) {
      connectionType.set(msg.transport as ConnectionType);
    }
    if (msg.ip) {
      wifiIp.set(msg.ip);
    }
    if (msg.port) {
      wifiPort.set(msg.port);
    }
    log('info', `Session: ${msg.name} / ${msg.code} (${msg.transport || 'unknown'})`);
  } else if (msg.type === 'ble_state') {
    // ignore detailed adapter state
  } else if (msg.type === 'ble_service_added' || msg.type === 'ble_advertising' || msg.type === 'ble_advertising_started') {
    log('info', `BLE: ${msg.type}`);
  // New unified UDP service events (WiFi and USB use same server)
  } else if (msg.type === 'server_starting') {
    log('info', `Server starting on ${msg.ip}:${msg.port}`);
  } else if (msg.type === 'server_listening') {
    log('info', `Server listening on ${msg.ip}:${msg.port}`);
  } else if (msg.type === 'server_stopped') {
    log('info', 'Server stopped');
  } else if (msg.type === 'mdns_registered') {
    log('info', `mDNS: ${msg.service} @ ${msg.ip}:${msg.port}`);
  } else if (msg.type === 'connected') {
    // Unified connected event from UDP server (works for both WiFi and USB)
    lastActivityMs = Date.now();
    setStatus('connected');
    log('info', `Connected: ${msg.client}`);
  } else if (msg.type === 'disconnected') {
    // Unified disconnected event from UDP server
    setStatus('disconnected');
    log('info', `Disconnected: ${msg.reason || 'unknown'}`);
  } else if (msg.type === 'session_rejected') {
    log('warn', `Connection rejected: ${msg.reason} from ${msg.client}`);
  // Legacy events for backward compatibility
  } else if (msg.type === 'wifi_starting' || msg.type === 'wifi_listening') {
    log('info', `WiFi: ${msg.type}`);
  } else if (msg.type === 'wifi_connected') {
    lastActivityMs = Date.now();
    setStatus('connected');
    log('info', `WiFi connected: ${msg.client}`);
  } else if (msg.type === 'wifi_disconnected') {
    setStatus('disconnected');
    log('info', `WiFi disconnected: ${msg.reason}`);
  } else if (msg.type === 'wifi_rejected') {
    log('warn', `WiFi rejected: ${msg.reason}`);
  } else if (msg.type === 'usb_starting' || msg.type === 'usb_listening') {
    log('info', `USB: ${msg.type}`);
  } else if (msg.type === 'usb_connected') {
    lastActivityMs = Date.now();
    setStatus('connected');
    log('info', `USB connected: ${msg.client}`);
  } else if (msg.type === 'usb_disconnected') {
    setStatus('disconnected');
    log('info', `USB disconnected: ${msg.reason}`);
  } else if (msg.type === 'usb_rejected') {
    log('warn', `USB rejected: ${msg.reason}`);
  } else if (msg.type === 'service_heartbeat') {
    // ignore - only for process liveness
  } else if (msg.type === 'usb_setup_info') {
    log('info', 'USB: Check setup requirements for iOS/Android');
  } else if (msg.type === 'resampling_enabled') {
    log('info', `Resampling: ${msg.upsample_to_hz}Hz (rate limit: ${msg.rate_limit_hz || 'none'})`);
  } else if (msg.type === 'warn') {
    log('warn', msg.message);
  } else if (msg.type === 'error') {
    log('error', msg.message);
  } else if (msg.type === 'heartbeat') {
    // BLE connectivity heartbeat - don't log (high frequency)
    lastActivityMs = Date.now();
    if (currentStatus !== 'connected') setStatus('connected');
  } else if (msg.type === 'ble_auth_ok') {
    lastActivityMs = Date.now();
    setStatus('connected');
    log('info', 'BLE auth OK');
  } else if (msg.type === 'ble_auth_failed') {
    lastActivityMs = Date.now();
    log('warn', 'BLE auth FAILED');
  } else if (msg.type === 'ble_control') {
    lastActivityMs = Date.now();
    log('info', `BLE control: ${msg.cmd}`);
  } else if (msg.type === 'pose') {
    try {
      const ai = msg.data?.absolute_input;
      if (ai) {
        const pose = {
          movement_start: !!ai.movement_start,
          x: Number(ai.x ?? 0),
          y: Number(ai.y ?? 0),
          z: Number(ai.z ?? 0),
          x_rot: Number(ai.x_rot ?? 0),
          y_rot: Number(ai.y_rot ?? 0),
          z_rot: Number(ai.z_rot ?? 0),
          qx: Number(ai.qx ?? 0),
          qy: Number(ai.qy ?? 0),
          qz: Number(ai.qz ?? 0),
          qw: Number(ai.qw ?? 1)
        };
        // INPUT pose is in reference coordinate system (equals visualization world)
        inputPose.set(pose);
        let currentOrigin: any;
        originPose.subscribe((v) => (currentOrigin = v))();
        let cfg: any;
        outputConfig.subscribe((v) => (cfg = v))();
        if (!cfg) {
          cfg = {
            includeFormats: { absolute_input: true, absolute_transformed: true, delta_input: false, delta_transformed: false },
            includeOrientation: { quaternion: true, euler_radian: false, euler_degree: false },
            scale: 1,
            outputAxes: { x: 1, y: 1, z: 1 }
          };
        }
        const { output, newOrigin } = computeOutput(pose, cfg, currentOrigin ?? null);
        outputJson.set(output);
        if (newOrigin !== currentOrigin) originPose.set(newOrigin);
      }
    } catch (err) {
      console.error('pose handling failed', err);
    }
    // pose messages do not change connection state
    lastActivityMs = Date.now();
  }
}

export interface StartConfig {
  connection: ConnectionType;
  name?: string;
  code?: string;
  upsampleHz?: number;
  rateLimitHz?: number;
}

export async function startPythonSidecar(config: StartConfig) {
  log('info', `Starting Python sidecar (${config.connection})...`);
  setStatus('disconnected');
  lastActivityMs = 0;
  connectionType.set(config.connection);
  
  // Clean up any existing listeners
  if (unlistenStdout) {
    unlistenStdout();
    unlistenStdout = null;
  }
  if (unlistenStderr) {
    unlistenStderr();
    unlistenStderr = null;
  }
  
  unlistenStdout = await listen<string>('python-line', (e) => {
    const line = e.payload;
    
    // Handle multiple JSON objects on a single line (can happen with concurrent prints)
    // Split on }{ which indicates concatenated JSON objects
    const jsonStrings = line.split(/(?<=\})(?=\{)/);
    
    for (const jsonStr of jsonStrings) {
      const trimmed = jsonStr.trim();
      if (!trimmed) continue;
      
      try {
        const msg = JSON.parse(trimmed);
        processMessage(msg);
      } catch (_) {
        // Not valid JSON, skip (e.g., QR code lines)
      }
    }
  });
  
  unlistenStderr = await listen<string>('python-error', (e) => {
    const payload = e.payload;
    // Only log and potentially disconnect on actual errors, not warnings
    const isCriticalError = /error|exception|traceback/i.test(payload);
    if (isCriticalError) {
      log('error', `python: ${payload}`);
      setStatus('disconnected');
    }
  });
  
  try {
    await invoke('start_python', {
      config: {
        connection: config.connection,
        name: config.name || null,
        code: config.code || null,
        upsample_hz: config.upsampleHz || null,
        rate_limit_hz: config.rateLimitHz || null,
      }
    });
    log('info', 'Python sidecar started');
    serviceState.set('running');
  } catch (err) {
    log('error', `Failed to start Python sidecar: ${String(err)}`);
    setStatus('disconnected');
    serviceState.set('stopped');
    throw err;
  }
  
  // Start inactivity watchdog: consider disconnected after 10s without activity
  if (inactivityTimer) clearInterval(inactivityTimer);
  inactivityTimer = setInterval(() => {
    const age = Date.now() - lastActivityMs;
    if (lastActivityMs === 0) return; // never connected yet
    if (age > 10_000) {
      if (currentStatus !== 'disconnected') setStatus('disconnected');
    }
  }, 1000) as unknown as number;
}

export async function stopPythonSidecar() {
  log('info', 'Stopping Python sidecar...');
  
  // Stop inactivity timer
  if (inactivityTimer) {
    clearInterval(inactivityTimer);
    inactivityTimer = null;
  }
  
  // Clean up listeners
  if (unlistenStdout) {
    unlistenStdout();
    unlistenStdout = null;
  }
  if (unlistenStderr) {
    unlistenStderr();
    unlistenStderr = null;
  }
  
  try {
    await invoke('stop_python');
    log('info', 'Python sidecar stopped');
  } catch (err) {
    log('error', `Failed to stop Python sidecar: ${String(err)}`);
  }
  
  // Reset state
  setStatus('disconnected');
  connectionName.set('');
  accessCode.set('');
  serviceState.set('stopped');
}
