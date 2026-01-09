export type Pose = {
  movement_start: boolean;
  x: number;
  y: number;
  z: number;
  x_rot: number;
  y_rot: number;
  z_rot: number;
  qx: number;
  qy: number;
  qz: number;
  qw: number;
};

export type OutputConfig = {
  includeFormats: {
    absolute_input: boolean;
    delta_input: boolean;
    absolute_transformed: boolean;
    delta_transformed: boolean;
  };
  includeOrientation: {
    quaternion: boolean;
    euler_radian: boolean;
    euler_degree: boolean;
  };
  scale: number;
  outputAxes: { x: number; y: number; z: number };
  // Pose of Target Coordinate System relative to reference/world (Euler radians)
  targetFrame?: { x: number; y: number; z: number; x_rot: number; y_rot: number; z_rot: number };
  // Authentication credentials (optional)
  authCredentials?: { name?: string; code?: string };
};


