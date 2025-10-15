import argparse
import json
import signal
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

import platform
import qrcode

from voodoo_core import Pose, OutputConfig, PoseTransformer
from voodoo_core.ble import generate_session


def load_config(path: Optional[str]) -> OutputConfig:
    if not path:
        return OutputConfig(
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

    # Resolve config path; if relative, also try next to this script
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        alt = Path(__file__).parent.joinpath(path)
        if alt.exists():
            p = alt
    data: Dict[str, Any] = json.loads(p.read_text())
    tf_deg = data.get("targetFrameDegrees")
    targetFrame = None
    if tf_deg:
        # convert degrees to radians for runtime config
        import math
        targetFrame = {
            "x": float(tf_deg.get("x", 0.0)),
            "y": float(tf_deg.get("y", 0.0)),
            "z": float(tf_deg.get("z", 0.0)),
            "x_rot": math.radians(float(tf_deg.get("x_rot_deg", 0.0))),
            "y_rot": math.radians(float(tf_deg.get("y_rot_deg", 0.0))),
            "z_rot": math.radians(float(tf_deg.get("z_rot_deg", 0.0))),
        }
    else:
        tf = data.get("targetFrame")
        if tf:
            targetFrame = tf

    return OutputConfig(
        includeFormats=data.get(
            "includeFormats",
            {
                "absolute_input": True,
                "delta_input": False,
                "absolute_transformed": True,
                "delta_transformed": False,
            },
        ),
        includeOrientation=data.get(
            "includeOrientation",
            {"quaternion": True, "euler_radian": False, "euler_degree": False},
        ),
        scale=float(data.get("scale", 1.0)),
        outputAxes=data.get("outputAxes", {"x": 1.0, "y": 1.0, "z": 1.0}),
        targetFrame=targetFrame,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Poll current OUTPUT pose at a fixed rate")
    parser.add_argument("--config", type=str, required=True, help="Path to voodoo_settings.json")
    parser.add_argument("--hz", type=float, default=5.0, help="Polling frequency in Hz (default 5)")
    args = parser.parse_args()

    # Show BLE auth QR on startup so iOS app can connect
    name, code = generate_session()
    print(json.dumps({"type": "session", "name": name, "code": code}), flush=True)

    # Print QR with name+code per QR spec
    qr_payload = json.dumps({"name": name, "code": code})
    qr = qrcode.QRCode(border=1)
    qr.add_data(qr_payload)
    qr.make()
    qr.print_ascii(invert=True)

    # Load config and create transformer
    config = load_config(args.config)
    transformer = PoseTransformer(config)

    # Shared latest pose
    latest: Dict[str, Any] = {}
    latest_lock = threading.Lock()

    # BLE event callback: feed incoming poses into transformer; mirror events to stdout
    def evt_cb(evt: Dict[str, Any]) -> None:
        print(json.dumps(evt), flush=True)
        if evt.get("type") == "pose":
            ai = evt.get("data", {}).get("absolute_input", {})
            try:
                pose = Pose(
                    pose_start=bool(ai.get("pose_start", False)),
                    x=float(ai.get("x", 0.0)),
                    y=float(ai.get("y", 0.0)),
                    z=float(ai.get("z", 0.0)),
                    x_rot=float(ai.get("x_rot", 0.0)),
                    y_rot=float(ai.get("y_rot", 0.0)),
                    z_rot=float(ai.get("z_rot", 0.0)),
                    qx=float(ai.get("qx", 0.0)),
                    qy=float(ai.get("qy", 0.0)),
                    qz=float(ai.get("qz", 0.0)),
                    qw=float(ai.get("qw", 1.0)),
                )
            except Exception:
                return
            out = transformer.transform(pose)
            with latest_lock:
                latest.clear()
                latest.update(out)

    # Poller at requested frequency (background thread)
    period = 1.0 / max(0.1, float(args.hz))

    def poller() -> None:
        while True:
            time.sleep(period)
            with latest_lock:
                if latest:
                    print(json.dumps({"polled_output": latest}), flush=True)

    t_poll = threading.Thread(target=poller, daemon=True)
    t_poll.start()

    # Graceful shutdown on Ctrl+C / SIGTERM by stopping the CoreFoundation main run loop
    try:
        import CoreFoundation as CF  # type: ignore
    except Exception:
        CF = None  # type: ignore

    def stop_run_loop(*_args: object) -> None:
        if CF is not None:
            try:
                CF.CFRunLoopStop(CF.CFRunLoopGetMain())
            except Exception:
                pass

    signal.signal(signal.SIGINT, lambda *_: stop_run_loop())
    signal.signal(signal.SIGTERM, lambda *_: stop_run_loop())

    # Run BLE peripheral appropriate to platform (lazy import to avoid macOS deps on Linux)
    try:
        system = platform.system().lower()
        distro = ""
        if system == "linux":
            try:
                with open("/etc/os-release", "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    if "ubuntu" in content:
                        distro = "ubuntu"
            except Exception:
                pass
        if system == "darwin":
            from voodoo_core.ble_peripheral_macos import run_macos_peripheral  # lazy import
            run_macos_peripheral(name, code, evt_cb)
        elif system == "linux" and distro == "ubuntu":
            from voodoo_core.ble_peripheral_ubuntu import run_ubuntu_peripheral  # lazy import
            run_ubuntu_peripheral(name, code, evt_cb)
        else:
            raise RuntimeError(f"Unsupported platform for BLE peripheral: {platform.platform()}")
    except Exception as e:
        print(json.dumps({"type": "error", "message": f"BLE peripheral failed: {e}"}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


