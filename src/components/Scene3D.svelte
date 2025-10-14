<script lang="ts">
  import { Canvas, T } from '@threlte/core';
  import { Gizmo, OrbitControls, Grid } from '@threlte/extras';
  import * as THREE from 'three';
  import { outputJson } from '../lib/store';
  import { onMount } from 'svelte';

  export let selectedOutputMode: 'absolute_input' | 'delta_input' | 'absolute_transformed' | 'delta_transformed' = 'absolute_transformed';

  let quaternion = new THREE.Quaternion(0, 0, 0, 1);
  let position = new THREE.Vector3(0, 0, 0);
  let meshQuaternion: [number, number, number, number] = [0, 0, 0, 1];
  let meshPosition: [number, number, number] = [0, 0, 0];

  // View sizing and orthographic camera bounds
  let containerEl: HTMLDivElement | null = null;
  let width = 1;
  let height = 1;
  $: aspect = width / Math.max(1, height);
  $: orthoLeft = -0.5 * aspect;
  $: orthoRight = 0.5 * aspect;
  $: orthoTop = 0.5;
  $: orthoBottom = -0.5;

  function measure() {
    if (containerEl) {
      const rect = containerEl.getBoundingClientRect();
      width = Math.max(1, Math.floor(rect.width));
      height = Math.max(1, Math.floor(rect.height));
    }
  }

  onMount(() => {
    measure();
    const onResize = () => measure();
    window.addEventListener('resize', onResize);
    const obs = new ResizeObserver(() => measure());
    if (containerEl) obs.observe(containerEl);
    return () => {
      window.removeEventListener('resize', onResize);
      obs.disconnect();
    };
  });


  $: {
    const data = $outputJson as any;
    if (!data) {
      quaternion.set(0, 0, 0, 1);
      position.set(0, 0, 0);
    } else {
      const absT = data?.absolute_transformed;
      const absI = data?.absolute_input;
      const dT = data?.delta_transformed;
      const dI = data?.delta_input;

      // Select orientation source: prefer the selected dataset's quaternion, fallback to absT, then absI
      const oriSrc =
        (selectedOutputMode === 'absolute_transformed' && absT) ||
        (selectedOutputMode === 'absolute_input' && absI) ||
        (selectedOutputMode === 'delta_transformed' && dT) ||
        (selectedOutputMode === 'delta_input' && dI) ||
        absT ||
        absI ||
        {};
      if (
        typeof oriSrc.qx === 'number' &&
        typeof oriSrc.qy === 'number' &&
        typeof oriSrc.qz === 'number' &&
        typeof oriSrc.qw === 'number'
      ) {
        quaternion.set(oriSrc.qx, oriSrc.qy, oriSrc.qz, oriSrc.qw);
      }

      // Select position source based on selected mode
      if (selectedOutputMode === 'absolute_transformed' || selectedOutputMode === 'absolute_input') {
        const p = data[selectedOutputMode];
        if (p && typeof p.x === 'number' && typeof p.y === 'number' && typeof p.z === 'number') {
          position.set(p.x, p.y, p.z);
        }
      } else if (selectedOutputMode === 'delta_transformed' || selectedOutputMode === 'delta_input') {
        const d = data[selectedOutputMode];
        if (d && typeof d.dx === 'number' && typeof d.dy === 'number' && typeof d.dz === 'number') {
          position.set(d.dx, d.dy, d.dz);
        }
      }
    }
    // reflect updates to props consumed by <T.Mesh>
    meshQuaternion = [quaternion.x, quaternion.y, quaternion.z, quaternion.w];
    meshPosition = [position.x, position.y, position.z];
  }
</script>

<div class="h-full w-full" bind:this={containerEl}>
<Canvas dpr={Math.min(2, window.devicePixelRatio)}>
  {#key selectedOutputMode}
    <T.Color attach={'background'} args={[0x0b0f17]} />
    <T.AmbientLight intensity={0.6} />
    <T.DirectionalLight position={[1, 1, 1]} intensity={0.9} />

    <!-- Axes helper and labels -->
    <!-- Axes helper length 0.5m, colors: x=red, y=green, z=blue -->
    <T.AxesHelper args={[0.5]} />

    <!-- Cuboid 0.072 x 0.114 x 0.08 meters -->
    <T.Mesh quaternion={meshQuaternion} position={meshPosition}>
      <T.BoxGeometry attach={'geometry'} args={[0.072, 0.114, 0.08]} />
      <T.MeshStandardMaterial attach={'material'} color={0x2dd4bf} metalness={0.1} roughness={0.6} />
    </T.Mesh>

    <T.PerspectiveCamera position={[2, 2, 2]} fov={36} makeDefault target={[0, 0, 0]}>
      <OrbitControls>
        <Gizmo placement={'bottom-left'} size={86} />
      </OrbitControls>
    </T.PerspectiveCamera>

    <Grid sectionSize={0} cellColor="#3a3a3a" />
  {/key}
</Canvas>
</div>


