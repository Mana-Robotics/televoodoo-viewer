Please help me create a cross platform desktop application titled "Televoodoo Viewer" with the following specs:


## PLATFORM, COMPATIBILITY, TECH STACK

1. This app shall run on: Ubuntu (x86, arm), Nvidia Jetson, Raspberry OS, macOS, Windows 11
2. The core components (BLE peripheral, pose transform - both defined below) and logic shall be written in python and it shall be possible to import and use them as one python module in other python projects
3. it is allowed to choose platform-specific bluetooth libraries if necessary, choose open-source if possible
4. the desktop app shall be bundled using tauri
5. the frontend shall be done with svelte (UI framework) + shadcn-svelte (style) + threlte (3d rendering)


## MAIN FUNCTIONS

1. It shall create a BLE peripheral according to "BLUETOOTH_API_DOCUMENTATION.md" to connect to a smartphone app
2. It shall graphically present BLE authentication credentials according to "QR_CODE_READING_GUIDE.md"
3. It shall receive poses as INPUT data according to "INPUT_POSE_DATA_FORMAT.md" from BLE with minimum latency, when the connected app starts tracking poses
4. It shall transform the received INPUT pose data according to a set configuration (defined in section "OUTPUT CONFIGURATION") which can either be configured in the GUI (see below), or alternatively via configuration parameters of the python module when used within other python projects
5. It shall provide OUTPUT data based on specific configuration to potential downstream code as JSON struct with minimal latency


## OUTPUT CONFIGURATION:

- Set orientation of OUTPUT coordinate system for calculating transformed values
- Scaling factor to be applied on position values (and respective speed values) for calculating transformation
- select data which shall be included in the OUTPUT JSON struct (multiple possible)
    - absolute INPUT pose data
    - delta of INPUT pose data since begin of tracking
    - absolute transformed pose data
    - delta of transformed pose data since begin of tracking
    - corresponding velocities and rotation speeds (in radiants)
- for all poses: select which pose orientation values shall be included (multiple possible) 
    - quaternion (default)
    - euler radiant
    - eueler degree


## FRONTEND / GUI DESIGN:

THE GUI shall be structured as follows:

    - Column 1:
        - Row 1:
            - Title "Connect with BLE"
            - Display qr code for BLE authentication 
            - Display BLE connectivity status

        - Row 2:
            - Title "Scan Reference"
            - Display "aruco-marker.png"

        - Row 3:
            - Title "Data Output Settings"
            - UI Elements required to set OUTPUT data according to specs defined under "OUTPUT CONFIGURATION"
            - Allow user to save settings as JSON struct
            - Allow user to load settings from selected JSON struct


    - Column 2 (main view - 2x as wide as Column 1 and 3):
        - Title "3D Visualization"
        - Display a 3D view of a cuboid with the dimensions 0.072 x 0.114 x 0.08 meters 
        - in a 3D space with x,y,z axis ranging from -0.5 to 0.5 metres each
        - add coordinate axis and corresponding labels x,y,z colored r,g,b
        - World coordinate system equals the reference coordinate system (defined by the ArUco marker)
        - Move and rotate the cuboid according to the INPUT pose values (quaternion for orientation)
        - OUTPUT formats and transforms affect only the JSON output, not the visualization

    - Column 3:
        - Title "Pose Values"
        - Display INPUT pose values
        - Display all possible OUTPUT values that the user could choose under "OUTPUT CONFIGURATION"
        - Display OUTPUT JSON according to current user-selected "OUTPUT CONFIGURATION" as formatted JSON text
