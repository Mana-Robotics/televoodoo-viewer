import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { bleStatus, outputJson, connectionName, accessCode, inputPose, originPose, outputConfig } from './store';
import { computeOutput } from './transform';
import { log } from './log';

let currentStatus: 'disconnected' | 'connecting' | 'connected' = 'disconnected';
let lastBleActivityMs = 0;
let inactivityTimer: number | null = null;

function setStatus(next: 'disconnected' | 'connecting' | 'connected') {
  if (currentStatus === next) return;
  currentStatus = next;
  bleStatus.set(next);
  log('info', `BLE status -> ${next}`);
}

function processMessage(msg: any) {
  if (msg.type === 'session') {
    connectionName.set(msg.name);
    accessCode.set(msg.code);
    log('info', `Session: ${msg.name} / ${msg.code}`);
  } else if (msg.type === 'ble_state') {
    // ignore detailed adapter state
  } else if (msg.type === 'ble_service_added' || msg.type === 'ble_advertising' || msg.type === 'ble_advertising_started') {
    log('info', `BLE: ${msg.type}`);
  } else if (msg.type === 'service_heartbeat') {
    // ignore - only for process liveness
  } else if (msg.type === 'heartbeat') {
    // BLE connectivity heartbeat - don't log (high frequency)
    lastBleActivityMs = Date.now();
    if (currentStatus !== 'connected') setStatus('connected');
  } else if (msg.type === 'ble_auth_ok') {
    lastBleActivityMs = Date.now();
    setStatus('connected');
    log('info', 'BLE auth OK');
  } else if (msg.type === 'ble_auth_failed') {
    lastBleActivityMs = Date.now();
    log('warn', 'BLE auth FAILED');
  } else if (msg.type === 'ble_control') {
    lastBleActivityMs = Date.now();
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
    lastBleActivityMs = Date.now();
  }
}

export async function startPythonSidecar() {
  log('info', 'Starting Python sidecar...');
  setStatus('disconnected');
  lastBleActivityMs = 0;
  
  const unlisten = await listen<string>('python-line', (e) => {
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
  
  const unlistenErr = await listen<string>('python-error', (e) => {
    const payload = e.payload;
    // Only log and potentially disconnect on actual errors, not warnings
    const isCriticalError = /error|exception|traceback/i.test(payload);
    if (isCriticalError) {
      log('error', `python: ${payload}`);
      setStatus('disconnected');
    }
  });
  
  try {
    await invoke('start_python');
    log('info', 'Python sidecar started');
  } catch (err) {
    log('error', `Failed to start Python sidecar: ${String(err)}`);
    setStatus('disconnected');
  }
  
  // Start inactivity watchdog: consider disconnected after 10s without BLE activity
  if (inactivityTimer) clearInterval(inactivityTimer);
  inactivityTimer = setInterval(() => {
    const age = Date.now() - lastBleActivityMs;
    if (lastBleActivityMs === 0) return; // never connected yet
    if (age > 10_000) {
      if (currentStatus !== 'disconnected') setStatus('disconnected');
    }
  }, 1000) as unknown as number;

  return () => { unlisten(); unlistenErr(); if (inactivityTimer) clearInterval(inactivityTimer); };
}
