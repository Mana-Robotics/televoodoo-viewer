import argparse
import json
import sys
import threading
import time
from voodoo_core.ble import generate_session, run_simulation
from voodoo_core.transform import OutputConfig, PoseTransformer
import platform


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="")
    args = parser.parse_args()

    name, code = generate_session()
    print(json.dumps({"type": "session", "name": name, "code": code}), flush=True)

    config = OutputConfig(
        includeFormats={
            "absolute_input": True,
            "delta_input": False,
            "absolute_transformed": True,
            "delta_transformed": False,
        },
        includeOrientation={
            "quaternion": True,
            "euler_radian": False,
            "euler_degree": False,
        },
        scale=1.0,
        outputAxes={"x": 1.0, "y": 1.0, "z": 1.0},
    )
    transformer = PoseTransformer(config)

    def on_pose(pose):
        out = transformer.transform(pose)
        print(json.dumps({"type": "pose", "data": out}), flush=True)

    # heartbeat thread
    def heartbeat():
        counter = 0
        while True:
            counter += 1
            # service heartbeat, not BLE connectivity
            print(json.dumps({"type": "service_heartbeat", "counter": counter}), flush=True)
            time.sleep(1.0)

    threading.Thread(target=heartbeat, daemon=True).start()

    # start BLE peripheral based on platform
    try:
        system = platform.system().lower()
        distro = ""
        if system == "linux":
            # Try to detect Ubuntu via /etc/os-release
            try:
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    if "ubuntu" in content:
                        distro = "ubuntu"
            except Exception:
                pass

        if system == "darwin":
            from voodoo_core.ble_peripheral_macos import run_macos_peripheral  # lazy import
            run_macos_peripheral(name, code)
        elif system == "linux" and distro == "ubuntu":
            from voodoo_core.ble_peripheral_ubuntu import run_ubuntu_peripheral  # lazy import
            run_ubuntu_peripheral(name, code)
        else:
            raise RuntimeError(f"Unsupported platform for BLE peripheral: {platform.platform()}")
    except Exception as e:
        print(json.dumps({"type": "error", "message": f"BLE peripheral failed: {e}"}), flush=True)

    # do not simulate poses by default; enable with --simulate
    if args.config == "--simulate":
        run_simulation(on_pose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


