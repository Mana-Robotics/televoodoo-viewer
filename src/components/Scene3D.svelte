<script lang="ts">
  import { Canvas, T } from '@threlte/core';
  import { Gizmo, OrbitControls, Grid } from '@threlte/extras';
  import * as THREE from 'three';
  import { inputPose, outputJson, outputConfig as outputConfigStore } from '../lib/store';
  import { onMount } from 'svelte';

  // Visualization world coordinate system equals the reference coordinate system
  // defined by the scanned/printed ArUco marker. The cuboid pose is always taken
  // from the INPUT pose values (reference/world coordinates).

  let quaternion = new THREE.Quaternion(0, 0, 0, 1);
  let position = new THREE.Vector3(0, 0, 0);
  let meshQuaternion: [number, number, number, number] = [0, 0, 0, 1];
  let meshPosition: [number, number, number] = [0, 0, 0];
  // Red cuboid (OUTPUT in target coords)
  let outQuaternion: [number, number, number, number] = [0, 0, 0, 1];
  let outPosition: [number, number, number] = [0, 0, 0];
  // Target frame axes (pose relative to world)
  let targetAxesPos: [number, number, number] = [0, 0, 0];
  let targetAxesQuat: [number, number, number, number] = [0, 0, 0, 1];

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
    const p = $inputPose as any;
    if (!p) {
      quaternion.set(0, 0, 0, 1);
      position.set(0, 0, 0);
    } else {
      if (
        typeof p.qx === 'number' &&
        typeof p.qy === 'number' &&
        typeof p.qz === 'number' &&
        typeof p.qw === 'number'
      ) {
        quaternion.set(p.qx, p.qy, p.qz, p.qw);
      }
      if (
        typeof p.x === 'number' &&
        typeof p.y === 'number' &&
        typeof p.z === 'number'
      ) {
        position.set(p.x, p.y, p.z);
      }
    }
    // reflect updates to props consumed by <T.Mesh>
    meshQuaternion = [quaternion.x, quaternion.y, quaternion.z, quaternion.w];
    meshPosition = [position.x, position.y, position.z];
  }

  // Reflect OUTPUT pose (absolute_transformed) in target coordinate system for red cuboid
  $: {
    const out = ($outputJson as any)?.absolute_transformed;
    if (out && typeof out.x === 'number' && typeof out.y === 'number' && typeof out.z === 'number') {
      outPosition = [out.x, out.y, out.z];
    } else {
      outPosition = [0, 0, 0];
    }
    if (out && typeof out.qx === 'number' && typeof out.qy === 'number' && typeof out.qz === 'number' && typeof out.qw === 'number') {
      outQuaternion = [out.qx, out.qy, out.qz, out.qw];
    } else {
      outQuaternion = [0, 0, 0, 1];
    }
  }

  // Target frame axes visualization in world (reference) space
  $: {
    const cfg = ($outputConfigStore as any);
    const tf = cfg?.targetFrame;
    if (tf) {
      targetAxesPos = [tf.x ?? 0, tf.y ?? 0, tf.z ?? 0];
      const euler = new THREE.Euler(tf.x_rot ?? 0, tf.y_rot ?? 0, tf.z_rot ?? 0, 'XYZ');
      const q = new THREE.Quaternion().setFromEuler(euler);
      targetAxesQuat = [q.x, q.y, q.z, q.w];
    } else {
      targetAxesPos = [0, 0, 0];
      targetAxesQuat = [0, 0, 0, 1];
    }
  }
</script>

<div class="h-full w-full" bind:this={containerEl}>
<Canvas dpr={Math.min(2, window.devicePixelRatio)}>
  <T.Color attach={'background'} args={[0x0b0f17]} />
  <T.AmbientLight intensity={0.6} />
  <T.DirectionalLight position={[1, 1, 1]} intensity={0.9} />

  <!-- Axes helper and labels -->
  <!-- Axes helper length 0.5m, colors: x=red, y=green, z=blue -->
  <T.AxesHelper args={[0.5]} />

  <!-- Target coordinate system axes (greenish)
       Shown at target frame pose relative to world/reference -->
  <T.Group position={targetAxesPos} quaternion={targetAxesQuat}>
    <T.AxesHelper args={[0.4]} />
  </T.Group>

  <!-- Cuboid 0.072 x 0.114 x 0.08 meters -->
  <T.Mesh quaternion={meshQuaternion} position={meshPosition}>
    <T.BoxGeometry attach={'geometry'} args={[0.114, 0.072, 0.008]} />
    <T.MeshStandardMaterial attach={'material'} color={0x2dd4bf} metalness={0.1} roughness={0.6} />
  </T.Mesh>

  <!-- Red cuboid showing OUTPUT pose in target coordinate system -->
  <T.Mesh quaternion={outQuaternion} position={outPosition}>
    <T.BoxGeometry attach={'geometry'} args={[0.114, 0.072, 0.008]} />
    <T.MeshStandardMaterial attach={'material'} color={0xff4444} metalness={0.1} roughness={0.6} />
  </T.Mesh>

  <T.PerspectiveCamera position={[1.0, 0.9, 1.0]} fov={36} makeDefault target={[0, 0, 0]}>
    <OrbitControls>
      <Gizmo placement={'bottom-left'} size={86} />
    </OrbitControls>
  </T.PerspectiveCamera>

  <Grid sectionSize={0} cellColor="#3a3a3a" />
</Canvas>
</div>


