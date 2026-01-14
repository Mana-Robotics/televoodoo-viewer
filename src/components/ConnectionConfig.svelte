<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ConnectionType } from '../lib/store';

  const dispatch = createEventDispatcher<{
    start: { connection: ConnectionType; name?: string; code?: string };
  }>();

  let connectionType: ConnectionType = 'wifi';
  let useCustomCredentials = false;
  let customName = '';
  let customCode = '';

  function handleStart() {
    dispatch('start', {
      connection: connectionType,
      name: useCustomCredentials && customName ? customName : undefined,
      code: useCustomCredentials && customCode ? customCode : undefined,
    });
  }

  function generateRandomCode(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  function generateRandomName(): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    const suffix = chars.charAt(Math.floor(Math.random() * chars.length)) + 
                   chars.charAt(Math.floor(Math.random() * chars.length));
    return `voodoo${suffix}`;
  }

  function fillWithRandom() {
    customName = generateRandomName();
    customCode = generateRandomCode();
  }
</script>

<div class="space-y-6">
  <h2 class="text-xl font-semibold">Connection Configuration</h2>
  
  <!-- Connection Type -->
  <div class="space-y-2">
    <label class="block text-sm font-medium text-gray-300">Connection Type</label>
    <div class="flex gap-4 flex-wrap">
      <label class="flex items-center gap-2 cursor-pointer">
        <input 
          type="radio" 
          bind:group={connectionType} 
          value="wifi" 
          class="w-4 h-4 text-blue-500 bg-gray-800 border-gray-600 focus:ring-blue-500"
        />
        <span class="text-sm">WiFi</span>
      </label>
      <label class="flex items-center gap-2 cursor-pointer">
        <input 
          type="radio" 
          bind:group={connectionType} 
          value="usb" 
          class="w-4 h-4 text-blue-500 bg-gray-800 border-gray-600 focus:ring-blue-500"
        />
        <span class="text-sm">USB</span>
      </label>
      <label class="flex items-center gap-2 cursor-pointer">
        <input 
          type="radio" 
          bind:group={connectionType} 
          value="ble" 
          class="w-4 h-4 text-blue-500 bg-gray-800 border-gray-600 focus:ring-blue-500"
        />
        <span class="text-sm">Bluetooth (BLE)</span>
      </label>
    </div>
    <p class="text-xs text-gray-500">
      {#if connectionType === 'wifi'}
        WiFi offers low latency (~16ms) and works on all platforms.
      {:else if connectionType === 'usb'}
        USB offers lowest latency (~5-10ms). Requires USB tethering or macOS Internet Sharing.
      {:else}
        BLE works on macOS and Ubuntu. Subject to connection interval batching.
      {/if}
    </p>
  </div>

  <!-- Credentials -->
  <div class="space-y-2">
    <label class="block text-sm font-medium text-gray-300">Credentials</label>
    <label class="flex items-center gap-2 cursor-pointer">
      <input 
        type="checkbox" 
        bind:checked={useCustomCredentials}
        class="w-4 h-4 text-blue-500 bg-gray-800 border-gray-600 rounded focus:ring-blue-500"
      />
      <span class="text-sm">Use custom name and code</span>
    </label>
    
    {#if useCustomCredentials}
      <div class="mt-3 space-y-3 pl-6">
        <div>
          <label class="block text-xs text-gray-400 mb-1">Name</label>
          <input 
            type="text" 
            bind:value={customName}
            placeholder="e.g., voodooAB"
            maxlength="20"
            class="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Code (6 characters)</label>
          <input 
            type="text" 
            bind:value={customCode}
            placeholder="e.g., ABC123"
            maxlength="6"
            class="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded focus:border-blue-500 focus:outline-none uppercase"
          />
        </div>
        <button 
          type="button"
          on:click={fillWithRandom}
          class="text-xs text-blue-400 hover:text-blue-300 underline"
        >
          Generate random values
        </button>
      </div>
    {:else}
      <p class="text-xs text-gray-500 pl-6">
        Random credentials will be generated each time the service starts.
      </p>
    {/if}
  </div>

  <!-- Start Button -->
  <div class="pt-4">
    <button
      on:click={handleStart}
      class="w-full py-3 px-4 bg-green-600 hover:bg-green-500 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      Start Service
    </button>
  </div>
</div>
