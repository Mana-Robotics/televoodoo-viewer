<script lang="ts">
  import Qr from './components/Qr.svelte';
  import OutputConfig from './components/OutputConfig.svelte';
  import PoseValues from './components/PoseValues.svelte';
  import { logs } from './lib/log';
  import Scene3D from './components/Scene3D.svelte';
  import { onMount } from 'svelte';
  import { startPythonSidecar } from './lib/backend';
  import { bleStatus as bleStatusStore, connectionName as connectionNameStore, accessCode as accessCodeStore } from './lib/store';
  import { open } from '@tauri-apps/plugin-shell';
  const markerUrl = new URL('../SPECS/aruco-marker.png', import.meta.url).href;

  let connectionName: string;
  let accessCode: string;
  let bleStatus: 'disconnected' | 'connecting' | 'connected';
  const unsub = [
    connectionNameStore.subscribe((v) => (connectionName = v)),
    accessCodeStore.subscribe((v) => (accessCode = v)),
    bleStatusStore.subscribe((v) => (bleStatus = v)),
  ];

  onMount(() => {
    startPythonSidecar();
    return () => unsub.forEach((u) => u());
  });
  // Visualization uses INPUT pose in reference/world coords; OUTPUT mode only affects JSON

  function handleConfigChange(event: CustomEvent) {
    // Placeholder: wire into Tauri backend persistence later
    console.log('config changed', event.detail);
  }

  async function openPdfLink() {
    await open('https://github.com/Mana-Robotics/televoodoo-python/blob/main/assets/televoodoo-aruco-marker.pdf');
  }
</script>

<div class="h-full grid grid-cols-12 gap-4 p-4">
  <!-- Column 1 -->
  <div class="col-span-3 space-y-6">
    <section>
      <h2 class="text-xl font-semibold mb-2">Scan to Connect</h2>
      <Qr {connectionName} {accessCode} />
      <div class="mt-3 space-y-1">
        <div class="text-sm text-gray-300">Connection Status: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{bleStatus}</span></div>
        <div class="text-sm text-gray-300">Name: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{connectionName}</span></div>
        <div class="text-sm text-gray-300">Code: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{accessCode}</span></div>
      </div>
    </section>

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


