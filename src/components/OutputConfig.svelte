<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { outputConfig, upsamplingConfig, rateLimitConfig } from '../lib/store';
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
  // Pose of Target Coordinate System relative to reference/world (UI: meters, degrees)
  let targetPos = { x: 0, y: 0, z: 0 };
  let targetEulerDeg = { x_rot_deg: 0, y_rot_deg: 0, z_rot_deg: 0 };

  // Upsampling settings
  let upsamplingEnabled = false;
  let upsamplingHz = 200;

  // Rate limit settings
  let rateLimitEnabled = false;
  let rateLimitHz = 30;

  function toRadians(deg: number) { return (deg * Math.PI) / 180; }
  function toDegrees(rad: number) { return (rad * 180) / Math.PI; }

  function emitResamplingChange() {
    upsamplingConfig.set({ enabled: upsamplingEnabled, hz: upsamplingHz });
    rateLimitConfig.set({ enabled: rateLimitEnabled, hz: rateLimitHz });
  }

  function emitChange() {
    // This component configures OUTPUT JSON only; visualization always uses INPUT in reference/world coords
    // Convert UI degrees to radians for backend/runtime config
    const targetFrame = {
      x: Number(targetPos.x) || 0,
      y: Number(targetPos.y) || 0,
      z: Number(targetPos.z) || 0,
      x_rot: toRadians(Number(targetEulerDeg.x_rot_deg) || 0),
      y_rot: toRadians(Number(targetEulerDeg.y_rot_deg) || 0),
      z_rot: toRadians(Number(targetEulerDeg.z_rot_deg) || 0),
    };
    dispatch('change', { includeFormats, includeOrientation, scale, outputAxes, targetFrame });
    outputConfig.set({ includeFormats, includeOrientation, scale, outputAxes, targetFrame });
  }

  async function saveConfig() {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const { writeTextFile } = await import('@tauri-apps/plugin-fs');
    try {
      const file = await save({ defaultPath: 'voodoo_settings.json', filters: [{ name: 'JSON', extensions: ['json'] }] });
      if (file) {
        // Ensure .json extension
        let path = String(file);
        if (!path.toLowerCase().endsWith('.json')) path = path + '.json';
        // Save UI-friendly payload (degrees)
        const payload = { includeFormats, includeOrientation, scale, outputAxes, targetFrameDegrees: { ...targetPos, ...targetEulerDeg } };
        await writeTextFile(path, JSON.stringify(payload, null, 2));
      }
    } catch (e) {
      console.error('Failed to save settings:', e);
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
      // Support loading UI degrees or runtime radians or legacy quaternion
      if (cfg.targetFrameDegrees) {
        targetPos = { x: cfg.targetFrameDegrees.x ?? 0, y: cfg.targetFrameDegrees.y ?? 0, z: cfg.targetFrameDegrees.z ?? 0 };
        targetEulerDeg = {
          x_rot_deg: cfg.targetFrameDegrees.x_rot_deg ?? 0,
          y_rot_deg: cfg.targetFrameDegrees.y_rot_deg ?? 0,
          z_rot_deg: cfg.targetFrameDegrees.z_rot_deg ?? 0,
        };
      } else if (cfg.targetFrame && typeof cfg.targetFrame.x_rot === 'number') {
        targetPos = { x: cfg.targetFrame.x ?? 0, y: cfg.targetFrame.y ?? 0, z: cfg.targetFrame.z ?? 0 };
        targetEulerDeg = {
          x_rot_deg: toDegrees(cfg.targetFrame.x_rot ?? 0),
          y_rot_deg: toDegrees(cfg.targetFrame.y_rot ?? 0),
          z_rot_deg: toDegrees(cfg.targetFrame.z_rot ?? 0),
        };
      } else if (cfg.targetFrame && typeof cfg.targetFrame.qx === 'number') {
        // Legacy quaternion format: cannot directly derive degrees without math; reset to zeros
        targetPos = { x: cfg.targetFrame.x ?? 0, y: cfg.targetFrame.y ?? 0, z: cfg.targetFrame.z ?? 0 };
        targetEulerDeg = { x_rot_deg: 0, y_rot_deg: 0, z_rot_deg: 0 };
      }
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
      <div class="block mb-1" role="heading" aria-level="3">Pose of Target Coordinate System (relative to reference/world)</div>
      <div class="grid grid-cols-6 gap-2 items-center">
        <label class="flex items-center gap-1" for="t-x"><input id="t-x" type="number" bind:value={targetPos.x} class="w-24 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> x <span class="text-gray-400">m</span></label>
        <label class="flex items-center gap-1" for="t-y"><input id="t-y" type="number" bind:value={targetPos.y} class="w-24 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> y <span class="text-gray-400">m</span></label>
        <label class="flex items-center gap-1" for="t-z"><input id="t-z" type="number" bind:value={targetPos.z} class="w-24 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> z <span class="text-gray-400">m</span></label>
      </div>
      <div class="grid grid-cols-6 gap-2 items-center mt-2">
        <label class="flex items-center gap-1" for="t-xdeg"><input id="t-xdeg" type="number" bind:value={targetEulerDeg.x_rot_deg} class="w-24 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> x°</label>
        <label class="flex items-center gap-1" for="t-ydeg"><input id="t-ydeg" type="number" bind:value={targetEulerDeg.y_rot_deg} class="w-24 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> y°</label>
        <label class="flex items-center gap-1" for="t-zdeg"><input id="t-zdeg" type="number" bind:value={targetEulerDeg.z_rot_deg} class="w-24 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitChange}/> z°</label>
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

    <div>
      <div class="block mb-1" role="heading" aria-level="3">Upsampling</div>
      <div class="space-y-2">
        <label class="flex items-center gap-2" for="upsample-on">
          <input id="upsample-on" type="checkbox" bind:checked={upsamplingEnabled} on:change={emitResamplingChange}/>
          Enable upsampling
        </label>
        {#if upsamplingEnabled}
          <label class="flex items-center gap-2" for="upsample-hz">
            <input id="upsample-hz" type="number" min="1" max="1000" step="1" bind:value={upsamplingHz} class="w-20 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitResamplingChange}/>
            <span class="text-gray-400">Hz</span>
          </label>
          <p class="text-xs text-gray-500">Upsamples poses using linear extrapolation for high-frequency control loops.</p>
        {/if}
      </div>
    </div>

    <div>
      <div class="block mb-1" role="heading" aria-level="3">Rate Limit</div>
      <div class="space-y-2">
        <label class="flex items-center gap-2" for="rate-limit-on">
          <input id="rate-limit-on" type="checkbox" bind:checked={rateLimitEnabled} on:change={emitResamplingChange}/>
          Enable rate limit
        </label>
        {#if rateLimitEnabled}
          <label class="flex items-center gap-2" for="rate-limit-hz">
            <input id="rate-limit-hz" type="number" min="1" max="100" step="1" bind:value={rateLimitHz} class="w-20 bg-gray-900 border border-gray-700 px-2 py-1" on:change={emitResamplingChange}/>
            <span class="text-gray-400">Hz</span>
          </label>
          <p class="text-xs text-gray-500">Caps output frequency by dropping excess poses.</p>
        {/if}
      </div>
    </div>
  </div>
</div>


