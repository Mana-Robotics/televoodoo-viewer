<script lang="ts">
  import { Canvas } from '@threlte/core';
  import * as THREE from 'three';
  import { outputJson } from '../lib/store';

  export let selectedOutputMode: 'absolute_input' | 'delta_input' | 'absolute_transformed' | 'delta_transformed' = 'absolute_transformed';

  let quaternion = new THREE.Quaternion(0, 0, 0, 1);
  let position = new THREE.Vector3(0, 0, 0);

  $: {
    const data = $outputJson as any;
    if (!data) {
      quaternion.set(0, 0, 0, 1);
      position.set(0, 0, 0);
    } else {
      // Prefer quaternion from selected mode; fallback to absolute_transformed, then absolute_input
      const absT = data?.absolute_transformed;
      const absI = data?.absolute_input;
      const src = (selectedOutputMode === 'absolute_transformed' ? absT : selectedOutputMode === 'absolute_input' ? absI : absT || absI) || {};
      if (typeof src.qx === 'number' && typeof src.qy === 'number' && typeof src.qz === 'number' && typeof src.qw === 'number') {
        quaternion.set(src.qx, src.qy, src.qz, src.qw);
      }

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
  }
</script>

  <Canvas background={0x0b0f17} dpr={Math.min(2, window.devicePixelRatio)}>
  {#key selectedOutputMode}
    <t-ambientLight intensity={0.5}></t-ambientLight>
    <t-directionalLight position={[3, 3, 3]} intensity={0.8}></t-directionalLight>

    <!-- Axes helper and labels are simplified -->
    <t-axesHelper args={[0.5]}></t-axesHelper>

    <!-- Cuboid 0.072 x 0.114 x 0.08 meters -->
    <t-mesh quaternion={[quaternion.x, quaternion.y, quaternion.z, quaternion.w]} position={[position.x, position.y, position.z]}>
      <t-boxGeometry args={[0.072, 0.114, 0.08]}></t-boxGeometry>
      <t-meshStandardMaterial color={0x2dd4bf}></t-meshStandardMaterial>
    </t-mesh>

    <t-perspectiveCamera position={[0.5, 0.5, 1]} fov={50}></t-perspectiveCamera>
  {/key}
</Canvas>


