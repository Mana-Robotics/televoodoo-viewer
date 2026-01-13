<script lang="ts">
  import { toCanvas } from 'qrcode';
  import { onMount, onDestroy } from 'svelte';
  import type { ConnectionType } from '../lib/store';
  
  export let connectionName: string;
  export let accessCode: string;
  export let transport: ConnectionType = 'wifi';
  export let ip: string = '';
  export let port: number = 50000;

  let canvasEl: HTMLCanvasElement;
  let containerEl: HTMLDivElement;
  let currentWidth = 0;
  let ro: ResizeObserver | null = null;
  let renderTimeout: number | null = null;

  // Build QR payload based on transport type
  $: qrPayload = transport === 'wifi' 
    ? JSON.stringify({ name: connectionName, code: accessCode, transport, ip, port })
    : JSON.stringify({ name: connectionName, code: accessCode, transport });

  async function render(width?: number) {
    if (!canvasEl) return;
    try {
      const targetWidth = Math.max(64, Math.floor(width ?? containerEl?.clientWidth ?? 0));
      if (!targetWidth) return;
      if (targetWidth === currentWidth) return;
      currentWidth = targetWidth;
      await toCanvas(canvasEl, qrPayload, { width: targetWidth, errorCorrectionLevel: 'M' });
    } catch (e) {
      console.error('QR render failed', e);
    }
  }

  onMount(() => {
    render(containerEl?.clientWidth);
    ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = Math.floor(entry.contentRect.width);
        if (w && w !== currentWidth) {
          if (renderTimeout) cancelAnimationFrame(renderTimeout);
          renderTimeout = requestAnimationFrame(() => render(w));
        }
      }
    });
    if (containerEl && ro) ro.observe(containerEl);
  });
  onDestroy(() => { ro?.disconnect(); ro = null; });

  $: if (canvasEl && containerEl && qrPayload) {
    render(containerEl.clientWidth);
  }
</script>

<div class="w-full" bind:this={containerEl}>
  <canvas bind:this={canvasEl} class="border border-gray-700 bg-white w-full h-auto"></canvas>
  </div>


