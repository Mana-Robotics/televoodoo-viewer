<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let selectedOutputMode: 'absolute_input' | 'delta_input' | 'absolute_transformed' | 'delta_transformed' = 'absolute_transformed';
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
    dispatch('change', { includeFormats, includeOrientation, scale, outputAxes, selectedOutputMode });
  }

  async function saveConfig() {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const { writeTextFile } = await import('@tauri-apps/plugin-fs');
    const file = await save({ filters: [{ name: 'JSON', extensions: ['json'] }] });
    if (file) {
      const payload = { includeFormats, includeOrientation, scale, outputAxes, selectedOutputMode };
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
      selectedOutputMode = cfg.selectedOutputMode ?? selectedOutputMode;
      emitChange();
    }
  }
</script>

<div class="space-y-4 text-sm">
  <div>
    <label class="block mb-1">Orientation of OUTPUT coordinate system</label>
    <div class="flex gap-2">
      <label class="flex items-center gap-1"><input type="number" bind:value={outputAxes.x} class="w-16 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> x</label>
      <label class="flex items-center gap-1"><input type="number" bind:value={outputAxes.y} class="w-16 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> y</label>
      <label class="flex items-center gap-1"><input type="number" bind:value={outputAxes.z} class="w-16 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> z</label>
    </div>
  </div>
  <div>
    <label class="block mb-1">Scaling factor</label>
    <input type="number" min="0" step="0.01" bind:value={scale} class="bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange} />
  </div>

  <div>
    <label class="block mb-1">Include in OUTPUT JSON</label>
    <div class="grid grid-cols-1 gap-1">
      <label class="flex items-center gap-2"><input type="checkbox" bind:checked={includeFormats.absolute_input} on:change={emitChange}/> absolute INPUT pose data</label>
      <label class="flex items-center gap-2"><input type="checkbox" bind:checked={includeFormats.delta_input} on:change={emitChange}/> delta of INPUT pose data since begin</label>
      <label class="flex items-center gap-2"><input type="checkbox" bind:checked={includeFormats.absolute_transformed} on:change={emitChange}/> absolute transformed pose data</label>
      <label class="flex items-center gap-2"><input type="checkbox" bind:checked={includeFormats.delta_transformed} on:change={emitChange}/> delta of transformed pose data since begin</label>
    </div>
  </div>

  <div>
    <label class="block mb-1">Pose orientation values</label>
    <div class="grid grid-cols-1 gap-1">
      <label class="flex items-center gap-2"><input type="checkbox" bind:checked={includeOrientation.quaternion} on:change={emitChange}/> quaternion</label>
      <label class="flex items-center gap-2"><input type="checkbox" bind:checked={includeOrientation.euler_radian} on:change={emitChange}/> euler radian</label>
      <label class="flex items-center gap-2"><input type="checkbox" bind:checked={includeOrientation.euler_degree} on:change={emitChange}/> euler degree</label>
    </div>
  </div>

  <div>
    <label class="block mb-1">Visualization source</label>
    <select bind:value={selectedOutputMode} class="bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}>
      <option value="absolute_input">Absolute INPUT</option>
      <option value="delta_input">Delta INPUT</option>
      <option value="absolute_transformed">Absolute Transformed</option>
      <option value="delta_transformed">Delta Transformed</option>
    </select>
  </div>

  <div class="flex gap-2">
    <button class="px-3 py-1 bg-gray-800 border border-gray-700" on:click={saveConfig}>Save</button>
    <button class="px-3 py-1 bg-gray-800 border border-gray-700" on:click={loadConfig}>Load</button>
  </div>
</div>


