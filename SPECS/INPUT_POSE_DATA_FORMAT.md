# Voodoo Control - Pose Data Format

## Overview
Voodoo Control receives pose tracking data via Bluetooth Low Energy (BLE). All INPUT pose values are expressed in the reference coordinate system defined by the scanned/printed ArUco marker. The 3D visualization world coordinate system equals this reference coordinate system.

## JSON Payload Format

The app expects the following JSON structure to be sent via the BLE characteristic:

```json
{
  "pose_start": true|false,
  "x": 0.0,
  "y": 0.0,
  "z": 0.0,
  "x_rot": 0.0,
  "y_rot": 0.0,
  "z_rot": 0.0,
  "qx": 0.0,
  "qy": 0.0,
  "qz": 0.0,
  "qw": 1.0
}
```

### Field Descriptions (reference/world coordinates)

- **pose_start** (boolean): Indicates whether pose tracking is active
- **x** (double): Position along X-axis (in meters)
- **y** (double): Position along Y-axis (in meters)
- **z** (double): Position along Z-axis (in meters)
- **x_rot** (double): Rotation around X-axis (in degrees)
- **y_rot** (double): Rotation around Y-axis (in degrees)
- **z_rot** (double): Rotation around Z-axis (in degrees)
- **qx** (double): Quaternion X component
- **qy** (double): Quaternion Y component
- **qz** (double): Quaternion Z component
- **qw** (double): Quaternion W component

## Example Payloads

### Active Pose Tracking
```json
{
  "pose_start": true,
  "x": 0.1,
  "y": 0.2,
  "z": 0.05,
  "x_rot": 45.0,
  "y_rot": -30.0,
  "z_rot": 15.0,
  "qx": 0.01234,
  "qy": -0.56789,
  "qz": 0.12345,
  "qw": 0.81234
}
```

### Inactive Pose Tracking
```json
{
  "pose_start": false,
  "x": 0.0,
  "y": 0.0,
  "z": 0.0,
  "x_rot": 0.0,
  "y_rot": 0.0,
  "z_rot": 0.0,
  "qx": 0.0,
  "qy": 0.0,
  "qz": 0.0,
  "qw": 1.0
}
```

## BLE Integration

The pose data should be sent to the same BLE characteristic that was previously used for pointer control:
- **Characteristic UUID**: `1C8FD138-FC18-4846-954D-E509366AEF64`
- **Properties**: Write, WriteWithoutResponse
- **Data Format**: UTF-8 encoded JSON string

## Display Window

The app displays the pose data and a 3D scene where world = reference coordinate system. The cuboid pose in the scene uses the INPUT pose directly. The UI shows:
- Pose start status (active/inactive indicator)
- Current position values (X, Y, Z)
- Current Euler rotation values (X, Y, Z)
- Current quaternion values (qx, qy, qz, qw) - used for 3D visualization
- Last update timestamp
- Connection status

The window stays on top and can be moved around the screen for convenient monitoring.
