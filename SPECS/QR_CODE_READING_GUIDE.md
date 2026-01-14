# Televoodoo - QR Code Reading Guide

## Overview
The Televoodoo app displays a QR code that contains the connection information needed for the phone app to connect. The phone app supports multiple transport types (WiFi, USB, BLE) and uses mDNS for service discovery. This guide explains how to read and parse the QR code data.

## QR Code Content Format

### JSON Structure
The QR code contains a JSON string with the following structure:
```json
{
  "name": "voodooXX",
  "code": "ABCDEF",
  "transport": "wifi"
}
```

### Field Descriptions
- **name** (string): The service/peripheral name (used for mDNS discovery)
  - Format: `voodoo` + 2-character random suffix
  - Example: `"voodooA3"`, `"voodooX7"`, `"voodooZ9"`
  - For WiFi/USB: Phone discovers via mDNS: `<name>._televoodoo._udp.local.`
  - For BLE: Phone scans for BLE peripheral with this advertised name
- **code** (string): The 6-character access code for authentication
  - Format: 6 alphanumeric characters (A-Z, 0-9)
  - Example: `"ABC123"`, `"XYZ789"`, `"DEF456"`
- **transport** (string): The connection type
  - Values: `"wifi"`, `"usb"`, or `"ble"`
  - `"wifi"`: Connect over WiFi network (phone and computer on same network)
  - `"usb"`: Connect over USB tethering (mDNS discovery on USB interface)
  - `"ble"`: Connect via Bluetooth Low Energy

### Example QR Code Contents

#### WiFi Connection
```json
{
  "name": "voodooA3",
  "code": "XYZ789",
  "transport": "wifi"
}
```

#### USB Connection
```json
{
  "name": "voodooB7",
  "code": "ABC123",
  "transport": "usb"
}
```

#### BLE Connection
```json
{
  "name": "voodooZ9",
  "code": "DEF456",
  "transport": "ble"
}
```

## How to Read the QR Code

### 1. QR Code Scanning
Use any QR code scanner to read the content:
- **Mobile apps**: Built-in camera apps, dedicated QR scanners
- **Desktop tools**: Online QR decoders, desktop QR scanner apps
- **Programming libraries**: ZXing, QuaggaJS, etc.

### 2. Parse the JSON Data
Once you have the raw string from the QR code, parse it as JSON:

#### JavaScript Example
```javascript
function parseQRCode(qrCodeString) {
  try {
    const data = JSON.parse(qrCodeString);
    return {
      serviceName: data.name,
      accessCode: data.code,
      transport: data.transport || 'ble'  // Default to BLE for backward compat
    };
  } catch (error) {
    console.error('Failed to parse QR code:', error);
    return null;
  }
}

// Usage
const qrData = parseQRCode('{"name":"voodooA3","code":"XYZ789","transport":"wifi"}');
console.log('Service Name:', qrData.serviceName);
console.log('Access Code:', qrData.accessCode);
console.log('Transport:', qrData.transport);
```

#### Python Example
```python
import json

def parse_qr_code(qr_code_string):
    try:
        data = json.loads(qr_code_string)
        return {
            'service_name': data['name'],
            'access_code': data['code'],
            'transport': data.get('transport', 'ble')  # Default to BLE
        }
    except json.JSONDecodeError as e:
        print(f'Failed to parse QR code: {e}')
        return None

# Usage
qr_data = parse_qr_code('{"name":"voodooA3","code":"XYZ789","transport":"wifi"}')
print('Service Name:', qr_data['service_name'])
print('Access Code:', qr_data['access_code'])
print('Transport:', qr_data['transport'])
```

#### Swift Example
```swift
struct ConnectionInfo: Codable {
    let name: String
    let code: String
    let transport: String?
    
    var effectiveTransport: String {
        return transport ?? "ble"
    }
}

func parseQRCode(_ qrCodeString: String) -> ConnectionInfo? {
    guard let data = qrCodeString.data(using: .utf8),
          let connectionInfo = try? JSONDecoder().decode(ConnectionInfo.self, from: data) else {
        print("Failed to parse QR code")
        return nil
    }
    return connectionInfo
}

// Usage
if let connectionInfo = parseQRCode(qrCodeString) {
    print("Service Name: \(connectionInfo.name)")
    print("Access Code: \(connectionInfo.code)")
    print("Transport: \(connectionInfo.effectiveTransport)")
}
```

## Using the QR Code Data

### Connection Process by Transport Type

#### WiFi / USB Connection (mDNS Discovery)
1. **Discover the service** via mDNS: `<name>._televoodoo._udp.local.`
2. **Connect** to the discovered UDP endpoint (IP:port from mDNS TXT record)
3. **Send HELLO** with the access code for authentication
4. **Receive ACK** confirming connection
5. **Send pose data** to the authenticated connection

#### BLE Connection
1. **Scan for the peripheral** using the name from the QR code
2. **Connect** to the discovered BLE peripheral
3. **Write to auth characteristic** with the access code
4. **Receive auth confirmation** 
5. **Send pose data** to the authenticated connection

### Implementation Flow

#### WiFi/USB Example (mDNS + UDP)
```javascript
async function connectUsingQRCode(qrCodeString) {
  const connectionInfo = parseQRCode(qrCodeString);
  if (!connectionInfo) {
    throw new Error('Invalid QR code format');
  }
  
  if (connectionInfo.transport === 'wifi' || connectionInfo.transport === 'usb') {
    // Discover via mDNS
    const service = await discoverMDNS(`${connectionInfo.serviceName}._televoodoo._udp.local.`);
    
    // Connect via UDP and authenticate
    const socket = await connectUDP(service.ip, service.port);
    await sendHello(socket, connectionInfo.accessCode);
    
    return socket;
  } else {
    // BLE connection
    const peripheral = await scanForPeripheral(connectionInfo.serviceName);
    await connectToPeripheral(peripheral);
    await authenticateWithCode(connectionInfo.accessCode);
    return peripheral;
  }
}
```

#### BLE Example
```javascript
async function connectBLE(qrCodeString) {
  const connectionInfo = parseQRCode(qrCodeString);
  if (!connectionInfo) {
    throw new Error('Invalid QR code format');
  }
  
  // Scan for the peripheral by name
  const peripheral = await scanForPeripheral(connectionInfo.serviceName);
  
  // Connect to the peripheral
  await connectToPeripheral(peripheral);
  
  // Authenticate with the access code
  await authenticateWithCode(connectionInfo.accessCode);
  
  // Now ready to send pose data
  return peripheral;
}
```

## QR Code Characteristics

### Technical Details
- **Encoding**: UTF-8
- **Error Correction Level**: Medium (M)
- **Size**: 300x300 pixels (as displayed in the app)
- **Format**: Standard QR Code (not Micro QR)

### Visual Appearance
- **Black and white** square pattern
- **High contrast** for easy scanning
- **Sufficient quiet zone** around the code
- **Clear, sharp edges** for reliable scanning

## Error Handling

### Common Issues
1. **Invalid JSON**: QR code doesn't contain valid JSON
2. **Missing fields**: JSON doesn't contain required `name`, `code`, or `transport` fields
3. **Wrong format**: QR code contains different data structure
4. **Scanning errors**: QR code is damaged or unreadable
5. **mDNS discovery fails**: Service not found (check network connectivity)

### Validation
```javascript
function validateQRCodeData(data) {
  if (!data || typeof data !== 'object') {
    return { valid: false, error: 'Invalid data type' };
  }
  
  if (!data.name || typeof data.name !== 'string') {
    return { valid: false, error: 'Missing or invalid name field' };
  }
  
  if (!data.code || typeof data.code !== 'string' || data.code.length !== 6) {
    return { valid: false, error: 'Missing or invalid code field' };
  }
  
  if (!data.name.startsWith('voodoo')) {
    return { valid: false, error: 'Invalid service name format' };
  }
  
  // Validate transport if present
  const validTransports = ['wifi', 'usb', 'ble'];
  if (data.transport && !validTransports.includes(data.transport)) {
    return { valid: false, error: 'Invalid transport type' };
  }
  
  return { valid: true };
}
```

## Security Considerations

### Access Code Security
- **Temporary**: Access codes change each time the app starts
- **Random**: Codes are generated using secure random methods
- **Short-lived**: Codes are only valid while the app is running
- **Single-use**: Each code is unique per session

### Best Practices
- **Don't store** access codes permanently
- **Regenerate** QR codes periodically for security
- **Validate** QR code data before using
- **Handle** authentication failures gracefully

## Testing

### Test QR Code Data
Use these example QR code contents for testing:

```json
// WiFi Example
{
  "name": "voodooA3",
  "code": "ABC123",
  "transport": "wifi"
}

// USB Example
{
  "name": "voodooX7",
  "code": "XYZ789",
  "transport": "usb"
}

// BLE Example
{
  "name": "voodooZ9",
  "code": "DEF456",
  "transport": "ble"
}
```

### QR Code Generation for Testing
```javascript
// Generate test QR code data
function generateTestQRData(transport = 'wifi') {
  const randomSuffix = Math.random().toString(36).substring(2, 4).toUpperCase();
  const randomCode = Math.random().toString(36).substring(2, 8).toUpperCase();
  
  return JSON.stringify({
    name: `voodoo${randomSuffix}`,
    code: randomCode,
    transport: transport
  });
}
```

## Integration Examples

### Mobile App Integration
```javascript
// React Native example
import { RNCamera } from 'react-native-camera';

function QRCodeScanner() {
  const handleQRCodeRead = (event) => {
    const connectionInfo = parseQRCode(event.data);
    if (connectionInfo) {
      // Proceed with BLE connection
      connectToVoodooControl(connectionInfo);
    }
  };
  
  return (
    <RNCamera
      onBarCodeRead={handleQRCodeRead}
      style={{ flex: 1 }}
    />
  );
}
```

### Web App Integration
```javascript
// Web Bluetooth with QR code scanning
import Quagga from 'quagga';

function initializeQRScanner() {
  Quagga.init({
    inputStream: {
      name: "Live",
      type: "LiveStream",
      target: document.querySelector('#scanner')
    },
    decoder: {
      readers: ["code_128_reader", "qr_reader"]
    }
  }, (err) => {
    if (err) {
      console.error('Scanner initialization failed:', err);
      return;
    }
    Quagga.start();
  });
  
  Quagga.onDetected((data) => {
    const qrData = parseQRCode(data.codeResult.code);
    if (qrData) {
      connectToVoodooControl(qrData);
    }
  });
}
```

## Troubleshooting

### Common Problems
1. **QR code not scanning**: Ensure good lighting and stable camera
2. **Invalid JSON**: Check if QR code is from the correct app version
3. **Connection fails**: Verify the peripheral name and access code
4. **Authentication fails**: Ensure the access code is current and correct

### Debug Steps
1. **Verify QR code content** by scanning with a generic QR reader
2. **Check JSON format** matches the expected structure
3. **Validate field values** (name starts with "voodoo", code is 6 characters)
4. **Test BLE connection** using the parsed data
5. **Monitor app logs** for authentication and connection details

## Support

For issues with QR code reading or parsing:
- Verify the QR code is from the latest Voodoo Control app version
- Check that the JSON format matches the specification exactly
- Ensure proper UTF-8 encoding when parsing the data
- Test with the provided example data first
