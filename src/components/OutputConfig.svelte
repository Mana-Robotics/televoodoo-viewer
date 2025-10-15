<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { outputConfig } from '../lib/store';
  const dispatch = createEventDispatcher();

  let includeFormats = {
    absolute_input: true,
    delta_input: false,
    absolute_transformed: true,
    delta_transformed: false,
  };
  let includeOrientation = {
    quaternion: true,
    euler_radian: false,
    euler_degree: false,
  };
  let scale = 1.0;
  let outputAxes = { x: 1, y: 1, z: 1 };

  function emitChange() {
    // This component configures OUTPUT JSON only; visualization always uses INPUT in reference/world coords
    dispatch('change', { includeFormats, includeOrientation, scale, outputAxes });
    outputConfig.set({ includeFormats, includeOrientation, scale, outputAxes });
  }

  async function saveConfig() {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const { writeTextFile } = await import('@tauri-apps/plugin-fs');
    const file = await save({ filters: [{ name: 'JSON', extensions: ['json'] }] });
    if (file) {
      const payload = { includeFormats, includeOrientation, scale, outputAxes };
      await writeTextFile(file, JSON.stringify(payload, null, 2));
    }
  }

  async function loadConfig() {
    const { open } = await import('@tauri-apps/plugin-dialog');
    const { readTextFile } = await import('@tauri-apps/plugin-fs');
    const file = await open({ multiple: false, filters: [{ name: 'JSON', extensions: ['json'] }] });
    if (typeof file === 'string') {
      const text = await readTextFile(file);
      const cfg = JSON.parse(text);
      includeFormats = cfg.includeFormats ?? includeFormats;
      includeOrientation = cfg.includeOrientation ?? includeOrientation;
      scale = cfg.scale ?? scale;
      outputAxes = cfg.outputAxes ?? outputAxes;
      emitChange();
    }
  }
</script>

<div class="flex gap-2">
  <h2 class="text-xl font-semibold mb-2">Data Output Settings</h2>
  <button class="px-2 py-0 bg-gray-800 border border-gray-700 text-sm" on:click={saveConfig}>Save</button>
  <button class="px-2 py-0 bg-gray-800 border border-gray-700 text-sm" on:click={loadConfig}>Load</button>
</div>
<div class="grid grid-cols-3 gap-4">
  <div class="space-y-4 text-sm">
    <div>
      <label class="block mb-1" for="axes-x">Orientation of OUTPUT coordinate system</label>
      <div class="flex gap-2">
        <label class="flex items-center gap-1" for="axes-x"><input id="axes-x" type="number" bind:value={outputAxes.x} class="w-16 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> x</label>
        <label class="flex items-center gap-1" for="axes-y"><input id="axes-y" type="number" bind:value={outputAxes.y} class="w-16 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> y</label>
        <label class="flex items-center gap-1" for="axes-z"><input id="axes-z" type="number" bind:value={outputAxes.z} class="w-16 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> z</label>
      </div>
    </div>
    <div>
      <label class="block mb-1" for="scale">Scaling factor</label>
      <input id="scale" type="number" min="0" step="0.01" bind:value={scale} class="bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange} />
    </div>
  </div>

  <div class="space-y-4 text-sm">

    <div>
      <div class="block mb-1" role="heading" aria-level="3">Include in OUTPUT JSON</div>
      <div class="grid grid-cols-1 gap-1">
        <label class="flex items-center gap-2" for="fmt-abs-in"><input id="fmt-abs-in" type="checkbox" bind:checked={includeFormats.absolute_input} on:change={emitChange}/> absolute INPUT pose data</label>
        <label class="flex items-center gap-2" for="fmt-delta-in"><input id="fmt-delta-in" type="checkbox" bind:checked={includeFormats.delta_input} on:change={emitChange}/> delta of INPUT pose data since begin</label>
        <label class="flex items-center gap-2" for="fmt-abs-tr"><input id="fmt-abs-tr" type="checkbox" bind:checked={includeFormats.absolute_transformed} on:change={emitChange}/> absolute transformed pose data</label>
        <label class="flex items-center gap-2" for="fmt-delta-tr"><input id="fmt-delta-tr" type="checkbox" bind:checked={includeFormats.delta_transformed} on:change={emitChange}/> delta of transformed pose data since begin</label>
      </div>
    </div>
  </div>

  <div class="space-y-4 text-sm">
    <div>
      <div class="block mb-1" role="heading" aria-level="3">Pose orientation values</div>
      <div class="grid grid-cols-1 gap-1">
        <label class="flex items-center gap-2" for="ori-q"><input id="ori-q" type="checkbox" bind:checked={includeOrientation.quaternion} on:change={emitChange}/> quaternion</label>
        <label class="flex items-center gap-2" for="ori-er"><input id="ori-er" type="checkbox" bind:checked={includeOrientation.euler_radian} on:change={emitChange}/> euler radian</label>
        <label class="flex items-center gap-2" for="ori-ed"><input id="ori-ed" type="checkbox" bind:checked={includeOrientation.euler_degree} on:change={emitChange}/> euler degree</label>
      </div>
    </div>
    <!-- Visualization always uses INPUT (reference/world). No selector needed. -->


  </div>
</div>


