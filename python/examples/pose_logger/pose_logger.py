import argparse
import json
import signal
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from voodoo_core import Pose, OutputConfig, PoseTransformer
from voodoo_core.ble import run_simulation, generate_session
from voodoo_core.ble_peripheral_macos import run_macos_peripheral
import qrcode


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

    p = Path(path)
    data: Dict[str, Any] = json.loads(p.read_text())
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
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Log poses using voodoo_core")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON OutputConfig (same format the app saves)",
    )
    parser.add_argument(
        "--ble",
        action="store_true",
        help="Run macOS BLE peripheral (requires pyobjc on macOS)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Auto-exit after N seconds (works in both simulated and BLE modes)",
    )
    args = parser.parse_args()

    if args.ble:
        name, code = generate_session()
        print(json.dumps({"type": "session", "name": name, "code": code}), flush=True)

        # Print QR with name+code per QR spec
        qr_payload = json.dumps({"name": name, "code": code})
        qr = qrcode.QRCode(border=1)
        qr.add_data(qr_payload)
        qr.make()
        qr.print_ascii(invert=True)

        # service heartbeat (not BLE connectivity)
        def heartbeat() -> None:
            counter = 0
            while True:
                counter += 1
                print(json.dumps({"type": "service_heartbeat", "counter": counter}), flush=True)
                time.sleep(1.0)

        threading.Thread(target=heartbeat, daemon=True).start()

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

        # Optional auto-exit timer
        if args.duration is not None:
            def timer_stop() -> None:
                time.sleep(max(0.0, float(args.duration)))
                stop_run_loop()
            threading.Thread(target=timer_stop, daemon=True).start()

        try:
            run_macos_peripheral(name, code)
        except Exception as e:
            print(json.dumps({"type": "error", "message": f"BLE peripheral failed: {e}"}), flush=True)
        return 0
    else:
        config = load_config(args.config)
        transformer = PoseTransformer(config)

        def on_pose(pose: Pose) -> None:
            out = transformer.transform(pose)
            print(json.dumps(out), flush=True)

        # For downstream projects: replace run_simulation with your pose source that
        # calls on_pose(Pose(...)) for each incoming sample.
        if args.duration is not None:
            t = threading.Thread(target=run_simulation, args=(on_pose,), daemon=True)
            t.start()
            time.sleep(max(0.0, float(args.duration)))
        else:
            try:
                run_simulation(on_pose)
            except KeyboardInterrupt:
                pass
        return 0


if __name__ == "__main__":
    raise SystemExit(main())


