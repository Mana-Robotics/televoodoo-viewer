import { writable } from 'svelte/store';
import type { Pose, OutputConfig } from './types';

export const bleStatus = writable<'disconnected' | 'connecting' | 'connected'>('disconnected');
export const connectionName = writable<string>('prsntr??');
export const accessCode = writable<string>('______');
export const inputPose = writable<Pose>({ pose_start: false, x: 0, y: 0, z: 0, x_rot: 0, y_rot: 0, z_rot: 0, qx: 0, qy: 0, qz: 0, qw: 1 });
export const outputJson = writable<Record<string, unknown>>({});
export const outputConfig = writable<OutputConfig | null>(null);


