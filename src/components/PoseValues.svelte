<script lang="ts">
  import { inputPose, outputJson } from '../lib/store';
  import { logs } from '../lib/log';

  function roundNumber(value: number): number {
    return Math.round(value * 1000) / 1000;
  }

  function roundForDisplay(value: any): any {
    if (typeof value === 'number') return roundNumber(value);
    if (Array.isArray(value)) return value.map(roundForDisplay);
    if (value && typeof value === 'object') {
      const out: Record<string, any> = {};
      for (const k of Object.keys(value)) out[k] = roundForDisplay(value[k]);
      return out;
    }
    return value;
  }
</script>

<div class="space-y-4 text-sm"> 
  <div>
    <h3 class="font-semibold mb-1">INPUT Pose</h3>
    <pre class="bg-gray-900 border border-gray-800 p-2 overflow-auto">{JSON.stringify(roundForDisplay($inputPose), null, 2)}</pre>
  </div>
  <div>
    <h3 class="font-semibold mb-1">OUTPUT JSON</h3>
    <pre class="bg-gray-900 border border-gray-800 p-2 overflow-auto">{JSON.stringify(roundForDisplay($outputJson), null, 2)}</pre>
  </div>
</div>


