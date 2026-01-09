# Voodoo Control - Bluetooth API Documentation

## Overview
Voodoo Control is an application that acts as a Bluetooth Low Energy (BLE) peripheral, accepting pose tracking data from connected devices. This document describes the BLE API for developers implementing client applications.

## BLE Service Configuration

### Service UUID
```
1C8FD138-FC18-4846-954D-E509366AEF61
```

### Characteristics

#### 1. Control Characteristic (NEXT/PREV)
- **UUID**: `1C8FD138-FC18-4846-954D-E509366AEF62`
- **Properties**: Write, WriteWithoutResponse
- **Purpose**: Send presentation control commands
- **Data Format**: UTF-8 string
- **Valid Commands**:
  - `"NEXT"` - Navigate to next slide
  - `"PREV"` - Navigate to previous slide

#### 2. Authentication Characteristic (Access Code)
- **UUID**: `1C8FD138-FC18-4846-954D-E509366AEF63`
- **Properties**: Write, WriteWithoutResponse
- **Purpose**: Authenticate with the peripheral
- **Data Format**: UTF-8 string (6-character access code)
- **Authentication Flow**:
  1. Connect to the peripheral
  2. Write the access code to this characteristic
  3. If correct, you'll be authenticated for other operations
  4. If incorrect, the connection will be rejected

#### 3. Pose Data Characteristic (Pointer/Pose)
- **UUID**: `1C8FD138-FC18-4846-954D-E509366AEF64`
- **Properties**: Write, WriteWithoutResponse
- **Purpose**: Send pose tracking data
- **Data Format**: UTF-8 JSON string

#### 4. Heartbeat Characteristic
- **UUID**: `1C8FD138-FC18-4846-954D-E509366AEF65`
- **Properties**: Read
- **Purpose**: Monitor connection status
- **Data Format**: 4-byte little-endian UInt32 counter

#### 5. Command Data Characteristic
- **UUID**: `1C8FD138-FC18-4846-954D-E509366AEF66`
- **Properties**: Write, WriteWithoutResponse
- **Purpose**: Send command data to the peripheral
- **Data Format**: UTF-8 JSON string containing command name and value

##### Command JSON Format
```json
{
  "command_name": value
}
```

##### Supported Commands
| Command Name | Value Type | Description |
|-------------|------------|-------------|
| `recording` | boolean | Starts (`true`) or stops (`false`) recording |
| `keep_recording` | boolean | Keep (`true`) or discard (`false`) the last recording |

##### Example Payloads

**Start Recording**
```json
{"recording":true}
```

**Stop Recording**
```json
{"recording":false}
```

**Keep Recording**
```json
{"keep_recording":true}
```

**Discard Recording**
```json
{"keep_recording":false}
```

## Pose Data JSON Format

### Required JSON Structure
```json
{
  "movement_start": true|false,
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

### Field Descriptions
- **movement_start** (boolean): When true, sets this pose as the new origin for delta calculations
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

### Example Payloads

#### Active Pose Tracking
```json
{
  "movement_start": true,
  "x": 0.1,
  "y": 0.2,
  "z": 0.05,
  "x_rot": 45.0,
  "y_rot": -30.5,
  "z_rot": 15.25,
  "qx": 0.01234,
  "qy": -0.56789,
  "qz": 0.12345,
  "qw": 0.81234
}
```

#### Inactive Pose Tracking
```json
{
  "movement_start": false,
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

## Connection Flow

### 1. Discovery
- Scan for BLE devices advertising the service UUID: `1C8FD138-FC18-4846-954D-E509366AEF61`
- The peripheral advertises with a local name pattern: `voodoo[XX]` where `[XX]` is a random 2-character suffix
- Example advertised name: `voodooA3`

### 2. Connection
- Connect to the discovered peripheral
- Discover services and characteristics
- Subscribe to the heartbeat characteristic for connection monitoring

### 3. Authentication
- Write the 6-character access code to the authentication characteristic
- The access code is displayed in the Voodoo Control app's QR code
- Wait for successful authentication before proceeding

### 4. Data Exchange
- Send pose data to the pose data characteristic
- Optionally send control commands to the control characteristic
- Monitor heartbeat characteristic to maintain connection

## Implementation Guidelines

### Connection Management
- **Auto-reconnection**: Implement automatic reconnection if the connection drops
- **Heartbeat monitoring**: Read the heartbeat characteristic periodically to detect connection issues
- **Error handling**: Handle authentication failures and connection timeouts gracefully
- **Timing considerations**: Allow sufficient time between authentication and data transmission

### Data Transmission
- **JSON encoding**: Ensure proper UTF-8 encoding of JSON data
- **Error handling**: Handle write failures and retry if necessary
- **Rate limiting**: Don't send data faster than the peripheral can process (recommended: 10-30 Hz)
- **Post-authentication delay**: Wait at least 1-2 seconds after successful authentication before sending data

### Security Considerations
- **Access code**: The access code changes each time the app starts
- **Authentication**: Always authenticate before sending data
- **Connection validation**: Verify the connection is still active before sending data

## Error Handling

### Common Error Scenarios
1. **Authentication failed**: Access code is incorrect
2. **Connection lost**: Peripheral disconnected
3. **Write failed**: Characteristic write operation failed
4. **JSON parsing error**: Invalid JSON format sent
5. **Premature data transmission**: Sending data immediately after authentication before connection is fully established

### Recommended Error Handling
```javascript
// Example error handling pattern
try {
  await writeCharacteristic(poseDataCharacteristic, jsonData);
} catch (error) {
  if (error.code === 'AUTHENTICATION_REQUIRED') {
    // Re-authenticate
    await authenticate(accessCode);
  } else if (error.code === 'CONNECTION_LOST') {
    // Attempt reconnection
    await reconnect();
  } else {
    // Log error and retry
    console.error('Write failed:', error);
    await retryWrite();
  }
}
```

### Connection Timing Issues

**Problem**: Client authenticates successfully but immediately gets "unauthenticated" errors when trying to send data.

**Root Cause**: The peripheral's connection monitor may mark the connection as stale if data is sent too quickly after authentication, before the heartbeat mechanism has time to establish the connection.

**Solution**:
1. **Wait after authentication**: Add a 1-2 second delay after successful authentication before sending any data
2. **Implement heartbeat**: Start reading the heartbeat characteristic immediately after authentication
3. **Retry logic**: If you get "unauthenticated" errors, wait a moment and retry the authentication

**Example Implementation**:
```javascript
// After successful authentication
await authenticate(accessCode);
console.log('Authentication successful');

// Wait for connection to stabilize
await new Promise(resolve => setTimeout(resolve, 2000));

// Start heartbeat monitoring
startHeartbeatMonitoring();

// Now safe to send data
await sendPoseData(poseData);
```

## Platform-Specific Notes

### iOS (Core Bluetooth)
- Use `CBPeripheralManager` for BLE operations
- Handle background modes for continuous operation
- Implement proper connection state management

### Android (Bluetooth Low Energy)
- Use `BluetoothGatt` for BLE operations
- Handle permissions for location and Bluetooth
- Implement proper service discovery

### Web (Web Bluetooth)
- Use `navigator.bluetooth.requestDevice()` for device selection
- Handle user gesture requirements for BLE operations
- Implement proper error handling for browser limitations

## Testing

### Test Data
Use the provided test JSON payloads to verify your implementation:

```json
// Test active pose
{
  "movement_start": true,
  "x": 100.5,
  "y": 200.25,
  "z": 50.75,
  "yaw": 45.0,
  "pitch": -30.5,
  "roll": 15.25
}

// Test inactive pose
{
  "movement_start": false,
  "x": 0.0,
  "y": 0.0,
  "z": 0.0,
  "yaw": 0.0,
  "pitch": 0.0,
  "roll": 0.0
}
```

### Debugging
- Enable BLE logging in your development environment
- Monitor the Voodoo Control app's console output for debugging information
- Use BLE debugging tools to inspect characteristic values

### Troubleshooting Connection Issues

**Symptoms**: 
- Authentication succeeds but data transmission fails with "unauthenticated" errors
- Logs show: "🚫 Denied unauthenticated request" immediately after successful authentication

**Debug Steps**:
1. **Check timing**: Ensure you wait 1-2 seconds after authentication before sending data
2. **Monitor logs**: Look for "🔐 Central [UUID] is now authenticated" in the Voodoo Control logs
3. **Verify heartbeat**: Ensure your client is reading the heartbeat characteristic regularly
4. **Check connection state**: Verify the BLE connection is still active before sending data

**Common Fixes**:
- Add delay after authentication: `await new Promise(resolve => setTimeout(resolve, 2000))`
- Implement proper heartbeat monitoring
- Add retry logic for failed writes
- Ensure you're not sending data too frequently

## Support

For technical support or questions about the API:
- Check the Voodoo Control app's console output for detailed logging
- Verify JSON format matches the specification exactly
- Ensure proper UTF-8 encoding of all data
- Test with the provided example payloads first

## Version Information

- **API Version**: 1.0
- **Last Updated**: January 2025
- **Compatible with**: Voodoo Control macOS app
