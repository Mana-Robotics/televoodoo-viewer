import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { bleStatus, outputJson, connectionName, accessCode } from './store';
import { log } from './log';

let currentStatus: 'disconnected' | 'connecting' | 'connected' = 'disconnected';
function setStatus(next: 'disconnected' | 'connecting' | 'connected') {
  if (currentStatus === next) return;
  currentStatus = next;
  bleStatus.set(next);
  console.log(`[BLE] status -> ${next}`);
  log('info', `BLE status -> ${next}`);
}

export async function startPythonSidecar() {
  setStatus('disconnected');
  lastBleActivityMs = 0;
  const unlisten = await listen<string>('python-line', (e) => {
    const line = e.payload;
    try {
      const msg = JSON.parse(line);
      if (msg.type === 'session') {
        connectionName.set(msg.name);
        accessCode.set(msg.code);
        // session emitted, but not considered connected until heartbeat arrives
        log('info', `Session: name=${msg.name} code=${msg.code}`);
      } else if (msg.type === 'service_heartbeat') {
        // ignore for connection state; only for process liveness
      } else if (msg.type === 'heartbeat') {
        // BLE connectivity heartbeat
        lastBleActivityMs = Date.now();
        if (currentStatus !== 'connected') setStatus('connected');
        log('info', `Heartbeat ${new Date(lastBleActivityMs).toLocaleTimeString()}`);
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
        outputJson.set(msg.data);
        // pose messages do not change connection state
        lastBleActivityMs = Date.now();
      }
    } catch (_) {
      // ignore non-json lines
    }
  });
  const unlistenErr = await listen<string>('python-error', (e) => {
    console.error('python stderr:', e.payload);
    setStatus('disconnected');
  });
  await invoke('start_python');
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

let lastBleActivityMs = 0;
let inactivityTimer: number | null = null;


