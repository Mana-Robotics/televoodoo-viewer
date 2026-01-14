import { writable } from 'svelte/store';
import type { Pose, OutputConfig } from './types';

// Service state: 'stopped' = config view, 'running' = active view
export const serviceState = writable<'stopped' | 'running'>('stopped');

// Connection configuration
export type ConnectionType = 'wifi' | 'ble' | 'usb';
export interface ServiceConfig {
  connection: ConnectionType;
  useCustomCredentials: boolean;
  customName: string;
  customCode: string;
}
export const serviceConfig = writable<ServiceConfig>({
  connection: 'wifi',
  useCustomCredentials: false,
  customName: '',
  customCode: '',
});

// Upsampling settings
export interface UpsamplingConfig {
  enabled: boolean;
  hz: number;
}
export const upsamplingConfig = writable<UpsamplingConfig>({
  enabled: false,
  hz: 200,
});

// Rate limiting settings
export interface RateLimitConfig {
  enabled: boolean;
  hz: number;
}
export const rateLimitConfig = writable<RateLimitConfig>({
  enabled: false,
  hz: 30,
});

// Active connection info (set when service starts)
export const connectionType = writable<ConnectionType>('wifi');
export const connectionStatus = writable<'disconnected' | 'connecting' | 'connected'>('disconnected');
export const connectionName = writable<string>('');
export const accessCode = writable<string>('');
export const wifiIp = writable<string>('');
export const wifiPort = writable<number>(50000);

// Legacy alias for backward compatibility
export const bleStatus = connectionStatus;

// Pose data
export const inputPose = writable<Pose>({ movement_start: false, x: 0, y: 0, z: 0, x_rot: 0, y_rot: 0, z_rot: 0, qx: 0, qy: 0, qz: 0, qw: 1 });
export const outputJson = writable<Record<string, unknown>>({});
export const outputConfig = writable<OutputConfig | null>(null);
export const originPose = writable<Pose | null>(null);
export const outputConfigDefaults: OutputConfig = {
  includeFormats: { absolute_input: true, absolute_transformed: true, delta_input: false, delta_transformed: false },
  includeOrientation: { quaternion: true, euler_radian: false, euler_degree: false },
  scale: 1,
  outputAxes: { x: 1, y: 1, z: 1 },
  targetFrame: { x: 0, y: 0, z: 0, qx: 0, qy: 0, qz: 0, qw: 1 }
};


