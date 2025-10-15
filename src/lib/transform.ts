import * as THREE from 'three';
import type { Pose, OutputConfig } from './types';

export type OutputPayload = Record<string, unknown>;

export function quaternionToEulerRadians(q: { qx: number; qy: number; qz: number; qw: number }) {
  const quat = new THREE.Quaternion(q.qx, q.qy, q.qz, q.qw);
  const euler = new THREE.Euler().setFromQuaternion(quat, 'XYZ');
  return { x_rot: euler.x, y_rot: euler.y, z_rot: euler.z };
}

export function radiansToDegrees(e: { x_rot: number; y_rot: number; z_rot: number }) {
  const r2d = 180 / Math.PI;
  return { x_rot: e.x_rot * r2d, y_rot: e.y_rot * r2d, z_rot: e.z_rot * r2d };
}

// INPUT pose values are expressed in the reference coordinate system defined by the
// scanned/printed ArUco marker. The visualization world equals this reference system.
// This function produces OUTPUT JSON variants based on configuration; position transforms
// (scale/axis multipliers) are applied relative to the same reference system.
export function computeOutput(
  pose: Pose,
  config: OutputConfig,
  origin: Pose | null
): { output: OutputPayload; newOrigin: Pose | null } {
  // Start of a new pose stream: when pose_start is true, always reset origin
  // to this first frame, regardless of whether an origin already exists.
  let newOrigin = pose.pose_start ? { ...pose } : origin;

  const include = config.includeFormats;
  const includeOri = config.includeOrientation;

  const absolute_input: Record<string, unknown> = {
    pose_start: pose.pose_start,
    x: pose.x,
    y: pose.y,
    z: pose.z,
  };
  const er = quaternionToEulerRadians(pose);
  const ed = radiansToDegrees(er);
  if (includeOri.quaternion) Object.assign(absolute_input, { qx: pose.qx, qy: pose.qy, qz: pose.qz, qw: pose.qw });
  if (includeOri.euler_radian) Object.assign(absolute_input, { x_rot: er.x_rot, y_rot: er.y_rot, z_rot: er.z_rot });
  if (includeOri.euler_degree) Object.assign(absolute_input, { x_rot_deg: ed.x_rot, y_rot_deg: ed.y_rot, z_rot_deg: ed.z_rot });

  const scale = config.scale ?? 1;
  const ax = config.outputAxes ?? { x: 1, y: 1, z: 1 };
  const transformPos = (p: { x: number; y: number; z: number }) => ({
    x: p.x * ax.x * scale,
    y: p.y * ax.y * scale,
    z: p.z * ax.z * scale,
  });

  const absolute_transformed: Record<string, unknown> = {
    ...transformPos(pose),
  };
  if (includeOri.quaternion) Object.assign(absolute_transformed, { qx: pose.qx, qy: pose.qy, qz: pose.qz, qw: pose.qw });
  if (includeOri.euler_radian) Object.assign(absolute_transformed, { x_rot: er.x_rot, y_rot: er.y_rot, z_rot: er.z_rot });
  if (includeOri.euler_degree) Object.assign(absolute_transformed, { x_rot_deg: ed.x_rot, y_rot_deg: ed.y_rot, z_rot_deg: ed.z_rot });

  const output: OutputPayload = {};
  if (include.absolute_input) output.absolute_input = absolute_input;
  if (include.absolute_transformed) output.absolute_transformed = absolute_transformed;

  if (newOrigin) {
    const delta_input: Record<string, unknown> = {
      dx: pose.x - newOrigin.x,
      dy: pose.y - newOrigin.y,
      dz: pose.z - newOrigin.z,
    };
    // Orientation for delta_*: include current orientation (not a delta), per UI expectation
    if (includeOri.quaternion) Object.assign(delta_input, { qx: pose.qx, qy: pose.qy, qz: pose.qz, qw: pose.qw });
    if (includeOri.euler_radian) Object.assign(delta_input, { x_rot: er.x_rot, y_rot: er.y_rot, z_rot: er.z_rot });
    if (includeOri.euler_degree) Object.assign(delta_input, { x_rot_deg: ed.x_rot, y_rot_deg: ed.y_rot, z_rot_deg: ed.z_rot });

    const dtPos = transformPos({ x: (delta_input.dx as number), y: (delta_input.dy as number), z: (delta_input.dz as number) });
    const delta_transformed: Record<string, unknown> = { ...dtPos };
    if (includeOri.quaternion) Object.assign(delta_transformed, { qx: pose.qx, qy: pose.qy, qz: pose.qz, qw: pose.qw });
    if (includeOri.euler_radian) Object.assign(delta_transformed, { x_rot: er.x_rot, y_rot: er.y_rot, z_rot: er.z_rot });
    if (includeOri.euler_degree) Object.assign(delta_transformed, { x_rot_deg: ed.x_rot, y_rot_deg: ed.y_rot, z_rot_deg: ed.z_rot });
    if (include.delta_input) output.delta_input = delta_input;
    if (include.delta_transformed) output.delta_transformed = delta_transformed;
  }

  return { output, newOrigin };
}


