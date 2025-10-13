# Voodoo Control - QR Code Reading Guide

## Overview
The Voodoo Control app displays a QR code that contains the connection information needed for client devices to connect via Bluetooth Low Energy (BLE). This guide explains how to read and parse the QR code data.

## QR Code Content Format

### JSON Structure
The QR code contains a JSON string with the following structure:
```json
{
  "name": "prsntrXX",
  "code": "ABCDEF"
}
```

### Field Descriptions
- **name** (string): The BLE peripheral's advertised local name
  - Format: `prsntr` + 2-character random suffix
  - Example: `"prsntrA3"`, `"prsntrX7"`, `"prsntrZ9"`
- **code** (string): The 6-character access code for authentication
  - Format: 6 alphanumeric characters (A-Z, 0-9)
  - Example: `"ABC123"`, `"XYZ789"`, `"DEF456"`

### Example QR Code Content
```json
{
  "name": "prsntrA3",
  "code": "XYZ789"
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
      peripheralName: data.name,
      accessCode: data.code
    };
  } catch (error) {
    console.error('Failed to parse QR code:', error);
    return null;
  }
}

// Usage
const qrData = parseQRCode('{"name":"prsntrA3","code":"XYZ789"}');
console.log('Peripheral Name:', qrData.peripheralName);
console.log('Access Code:', qrData.accessCode);
```

#### Python Example
```python
import json

def parse_qr_code(qr_code_string):
    try:
        data = json.loads(qr_code_string)
        return {
            'peripheral_name': data['name'],
            'access_code': data['code']
        }
    except json.JSONDecodeError as e:
        print(f'Failed to parse QR code: {e}')
        return None

# Usage
qr_data = parse_qr_code('{"name":"prsntrA3","code":"XYZ789"}')
print('Peripheral Name:', qr_data['peripheral_name'])
print('Access Code:', qr_data['access_code'])
```

#### Swift Example
```swift
struct ConnectionInfo: Codable {
    let name: String
    let code: String
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
    print("Peripheral Name: \(connectionInfo.name)")
    print("Access Code: \(connectionInfo.code)")
}
```

## Using the QR Code Data

### 1. BLE Connection Process
1. **Scan for the peripheral** using the name from the QR code
2. **Connect** to the discovered peripheral
3. **Authenticate** using the access code from the QR code
4. **Send pose data** to the authenticated connection

### 2. Implementation Flow
```javascript
async function connectUsingQRCode(qrCodeString) {
  // Parse QR code data
  const connectionInfo = parseQRCode(qrCodeString);
  if (!connectionInfo) {
    throw new Error('Invalid QR code format');
  }
  
  // Scan for the peripheral
  const peripheral = await scanForPeripheral(connectionInfo.peripheralName);
  
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
2. **Missing fields**: JSON doesn't contain required `name` or `code` fields
3. **Wrong format**: QR code contains different data structure
4. **Scanning errors**: QR code is damaged or unreadable

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
  
  if (!data.name.startsWith('prsntr')) {
    return { valid: false, error: 'Invalid peripheral name format' };
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
// Example 1
{
  "name": "prsntrA3",
  "code": "ABC123"
}

// Example 2
{
  "name": "prsntrX7",
  "code": "XYZ789"
}

// Example 3
{
  "name": "prsntrZ9",
  "code": "DEF456"
}
```

### QR Code Generation for Testing
```javascript
// Generate test QR code data
function generateTestQRData() {
  const randomSuffix = Math.random().toString(36).substring(2, 4).toUpperCase();
  const randomCode = Math.random().toString(36).substring(2, 8).toUpperCase();
  
  return JSON.stringify({
    name: `prsntr${randomSuffix}`,
    code: randomCode
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
3. **Validate field values** (name starts with "prsntr", code is 6 characters)
4. **Test BLE connection** using the parsed data
5. **Monitor app logs** for authentication and connection details

## Support

For issues with QR code reading or parsing:
- Verify the QR code is from the latest Voodoo Control app version
- Check that the JSON format matches the specification exactly
- Ensure proper UTF-8 encoding when parsing the data
- Test with the provided example data first
