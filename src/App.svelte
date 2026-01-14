<script lang="ts">
  import Qr from './components/Qr.svelte';
  import OutputConfig from './components/OutputConfig.svelte';
  import PoseValues from './components/PoseValues.svelte';
  import ConnectionConfig from './components/ConnectionConfig.svelte';
  import { logs } from './lib/log';
  import Scene3D from './components/Scene3D.svelte';
  import { startPythonSidecar, stopPythonSidecar, type StartConfig } from './lib/backend';
  import { 
    serviceState, 
    connectionStatus as connectionStatusStore, 
    connectionName as connectionNameStore, 
    accessCode as accessCodeStore,
    connectionType as connectionTypeStore,
    wifiIp as wifiIpStore,
    wifiPort as wifiPortStore,
    upsamplingConfig as upsamplingConfigStore,
    rateLimitConfig as rateLimitConfigStore
  } from './lib/store';
  import { open } from '@tauri-apps/plugin-shell';
  const markerUrl = new URL('../SPECS/aruco-marker.png', import.meta.url).href;

  let connectionName: string;
  let accessCode: string;
  let connectionStatus: 'disconnected' | 'connecting' | 'connected';
  let connectionType: 'wifi' | 'ble' | 'usb';
  let wifiIp: string;
  let wifiPort: number;
  let isRunning: boolean;
  let upsamplingConfig: { enabled: boolean; hz: number };
  let rateLimitConfig: { enabled: boolean; hz: number };

  const unsub = [
    connectionNameStore.subscribe((v) => (connectionName = v)),
    accessCodeStore.subscribe((v) => (accessCode = v)),
    connectionStatusStore.subscribe((v) => (connectionStatus = v)),
    connectionTypeStore.subscribe((v) => (connectionType = v)),
    wifiIpStore.subscribe((v) => (wifiIp = v)),
    wifiPortStore.subscribe((v) => (wifiPort = v)),
    serviceState.subscribe((v) => (isRunning = v === 'running')),
    upsamplingConfigStore.subscribe((v) => (upsamplingConfig = v)),
    rateLimitConfigStore.subscribe((v) => (rateLimitConfig = v)),
  ];

  function handleConfigChange(event: CustomEvent) {
    console.log('config changed', event.detail);
  }

  async function handleStart(event: CustomEvent<StartConfig>) {
    try {
      const config: StartConfig = {
        ...event.detail,
        upsampleHz: upsamplingConfig.enabled ? upsamplingConfig.hz : undefined,
        rateLimitHz: rateLimitConfig.enabled ? rateLimitConfig.hz : undefined,
      };
      await startPythonSidecar(config);
    } catch (err) {
      console.error('Failed to start service:', err);
    }
  }

  async function handleStop() {
    await stopPythonSidecar();
  }

  async function openPdfLink() {
    await open('https://github.com/Mana-Robotics/televoodoo-python/blob/main/assets/televoodoo-aruco-marker.pdf');
  }
</script>

<div class="h-full grid grid-cols-12 gap-4 p-4">
  <!-- Column 1 -->
  <div class="col-span-3 space-y-6">
    {#if isRunning}
      <!-- Active Service View -->
      <section>
        <h2 class="text-xl font-semibold mb-2">Scan to Connect</h2>
        <Qr {connectionName} {accessCode} transport={connectionType} ip={wifiIp} port={wifiPort} />
        <div class="mt-3 space-y-1">
          <div class="text-sm text-gray-300">
            Status: 
            <span class="px-2 py-0.5 rounded text-xs align-middle" 
                  class:bg-green-800={connectionStatus === 'connected'}
                  class:bg-yellow-800={connectionStatus === 'connecting'}
                  class:bg-gray-800={connectionStatus === 'disconnected'}>
              {connectionStatus}
            </span>
          </div>
          <div class="text-sm text-gray-300">Transport: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{connectionType.toUpperCase()}</span></div>
          <div class="text-sm text-gray-300">Name: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{connectionName}</span></div>
          <div class="text-sm text-gray-300">Code: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{accessCode}</span></div>
          {#if (connectionType === 'wifi' || connectionType === 'usb') && wifiIp}
            <div class="text-sm text-gray-300">IP: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{wifiIp}:{wifiPort}</span></div>
          {/if}
        </div>
        
        <button
          on:click={handleStop}
          class="mt-4 w-full py-2 px-4 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10h6v4H9z" />
          </svg>
          Stop Service
        </button>
      </section>
    {:else}
      <!-- Configuration View -->
      <section>
        <ConnectionConfig on:start={handleStart} />
      </section>
    {/if}

    <section>
      <h2 class="text-xl font-semibold mb-2">Connection Logs</h2>
      <div class="h-64 overflow-auto border border-gray-800 p-2 text-xs space-y-1">
        {#each $logs as entry}
          <div class="font-mono"><span class="text-gray-400">[{new Date(entry.ts).toLocaleTimeString()}]</span> [{entry.level}] {entry.message}</div>
        {/each}
      </div>
    </section>
  </div>

  <!-- Column 2 -->
  <div class="col-span-6 space-y-6">
    <section>
      <h2 class="text-xl font-semibold mb-1">3D Visualization</h2>
      <div class="text-xs text-gray-400 mb-2">World coordinate system = defined by ArUco reference; green cuboid = INPUT pose; red cuboid = OUTPUT pose</div>
      <div class="h-[70vh] border border-gray-800"><Scene3D /></div>
    </section>

    <section>
      <OutputConfig on:change={handleConfigChange} />
    </section>
  </div>

  <!-- Column 3 -->
  <div class="col-span-3 space-y-6">
    <section>
      <h2 class="text-xl font-semibold mb-2">Scan to Set Reference</h2>
      <div class="text-xs text-gray-400 mb-2">IMPORTANT: this ArUco marker is just for testing purposes. To work correctly, the ArRuco marker should be printed out in exactly 10x10cm format.</div>
      <div class="mb-2">
        <button
          on:click={openPdfLink}
          class="text-sm underline text-blue-400 hover:text-blue-300 cursor-pointer bg-transparent border-none p-0"
        >
          Open Print File (PDF)
        </button>
      </div>
      <img src={markerUrl} alt="aruco" class="w-full border border-gray-700" />
    </section>
    <section>
      <h2 class="text-xl font-semibold mb-2">Pose Values</h2>
      <PoseValues />
    </section>
  </div>
</div>
