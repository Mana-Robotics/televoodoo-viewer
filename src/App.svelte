<script lang="ts">
  import Qr from './components/Qr.svelte';
  import OutputConfig from './components/OutputConfig.svelte';
  import PoseValues from './components/PoseValues.svelte';
  import Scene3D from './components/Scene3D.svelte';
  import { onMount } from 'svelte';
  import { startPythonSidecar } from './lib/backend';
  import { bleStatus as bleStatusStore, connectionName as connectionNameStore, accessCode as accessCodeStore } from './lib/store';
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
  let selectedOutputMode: 'absolute_input' | 'delta_input' | 'absolute_transformed' | 'delta_transformed' = 'absolute_transformed';

  function handleConfigChange(event: CustomEvent) {
    // Placeholder: wire into Tauri backend persistence later
    console.log('config changed', event.detail);
  }
</script>

<div class="h-full grid grid-cols-12 gap-4 p-4">
  <!-- Column 1 -->
  <div class="col-span-3 space-y-6">
    <section>
      <h2 class="text-xl font-semibold mb-2">Connect with BLE</h2>
      <Qr {connectionName} {accessCode} />
      <div class="mt-3 space-y-1">
        <div class="text-sm text-gray-300">Status: <span class="px-2 py-0.5 rounded bg-gray-800 text-xs align-middle">{bleStatus}</span></div>
        <div class="text-sm text-gray-300">Peripheral: <span class="font-mono">{connectionName}</span></div>
        <div class="text-sm text-gray-300">Code: <span class="font-mono">{accessCode}</span></div>
      </div>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-2">Scan Reference</h2>
      <img src={markerUrl} alt="aruco" class="w-48 border border-gray-700" />
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-2">Data Output Settings</h2>
      <OutputConfig on:change={handleConfigChange} bind:selectedOutputMode />
    </section>
  </div>

  <!-- Column 2 -->
  <div class="col-span-6">
    <section>
      <h2 class="text-xl font-semibold mb-2">3D Visualization</h2>
      <div class="h-[70vh] border border-gray-800"><Scene3D bind:selectedOutputMode /></div>
    </section>
  </div>

  <!-- Column 3 -->
  <div class="col-span-3">
    <section>
      <h2 class="text-xl font-semibold mb-2">Pose Values</h2>
      <PoseValues />
    </section>
  </div>
</div>


