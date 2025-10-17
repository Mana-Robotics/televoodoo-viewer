# Pose Frequency Example

Measure the time delta between incoming pose samples and save a plot.

## Usage

Simulated input (10 seconds) and save to `pose_frequency.png`:

```bash
python examples/pose_frequency/pose_frequency.py --source sim --duration 10 --out pose_frequency.png
```

BLE input (macOS or Ubuntu; requires proper permissions and dependencies):

```bash
python examples/pose_frequency/pose_frequency.py --source ble --duration 10 --out pose_frequency.png
```

If `--duration` is omitted:
- sim: Ctrl+C to stop
- ble on macOS: the script attempts a graceful stop of the CoreFoundation run loop on Ctrl+C

The resulting `image pose_frequency.png` is stored in the pythond working directory (PWD), which by default is the `python` directory where the `.venv` is based in.

## Dependencies

This example requires `matplotlib` for plotting:

```bash
pip install matplotlib
```

The core BLE dependencies are already specified in `python/requirements.txt` for platform-specific needs (`pyobjc` on macOS, BlueZ/dbus on Ubuntu). Ensure your environment satisfies those prerequisites.


