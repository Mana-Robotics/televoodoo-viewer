import asyncio
import json
import struct
import threading
import time
from typing import Any, Dict, List, Optional, Callable
import logging
import signal

from dbus_next.service import (ServiceInterface, method, dbus_property,
                               PropertyAccess)
from dbus_next.aio import MessageBus
from dbus_next.constants import BusType
from dbus_next import Variant


# Shared UUIDs with macOS implementation
SERVICE_UUID = "1C8FD138-FC18-4846-954D-E509366AEF61"
_evt_cb: Optional[Callable[[Dict[str, Any]], None]] = None


def emit_event(evt: Dict[str, Any]) -> None:
    print(json.dumps(evt), flush=True)
    cb = _evt_cb
    if cb is not None:
        try:
            cb(evt)
        except Exception:
            pass

# Reduce noisy dbus-next internal error logs for benign Property.Set attempts
logging.getLogger('dbus_next').setLevel(logging.CRITICAL)
logging.getLogger('dbus_next.message_bus').setLevel(logging.CRITICAL)

class _DbusNoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if 'the property is readonly' in msg:
            return False
        if 'InterfacesAdded for org.bluez.GattCharacteristic1' in msg:
            return False
        if 'does not have property "TxPower"' in msg:
            return False
        return True

logging.getLogger().addFilter(_DbusNoiseFilter())
CHAR_CONTROL_UUID = "1C8FD138-FC18-4846-954D-E509366AEF62"
CHAR_AUTH_UUID = "1C8FD138-FC18-4846-954D-E509366AEF63"
CHAR_POSE_UUID = "1C8FD138-FC18-4846-954D-E509366AEF64"
CHAR_HEARTBEAT_UUID = "1C8FD138-FC18-4846-954D-E509366AEF65"


class GattService(ServiceInterface):
    def __init__(self, path: str, uuid: str, primary: bool = True, includes: Optional[List[str]] = None):
        super().__init__("org.bluez.GattService1")
        self._path = path
        self._uuid = uuid
        self._primary = primary
        self._includes = includes or []

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore[override]
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":  # type: ignore[override]
        return self._primary

    @dbus_property(access=PropertyAccess.READ)
    def Includes(self) -> "ao":  # type: ignore[override]
        return self._includes


class GattCharacteristic(ServiceInterface):
    def __init__(self, path: str, uuid: str, service_path: str, flags: List[str]):
        super().__init__("org.bluez.GattCharacteristic1")
        self._path = path
        self._uuid = uuid
        self._service_path = service_path
        self._flags = flags
        self._value: bytes = b""
        self._notifying = False
        self._notify_thread: Optional[threading.Thread] = None
        self._notify_supplier: Optional[callable] = None

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore[override]
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> "o":  # type: ignore[override]
        return self._service_path

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":  # type: ignore[override]
        return self._flags

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":  # type: ignore[override]
        return self._notifying

    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> "ay":  # type: ignore[override]
        return self._value

    @method()
    def ReadValue(self, options: 'a{sv}') -> 'ay':  # type: ignore[override]
        # Support offset reads if provided by BlueZ
        try:
            offset_var = options.get("offset")
            if offset_var is not None:
                offset = int(offset_var.value)
                if offset < 0:
                    offset = 0
                return list(self._value[offset:])
            return list(self._value)
        except Exception:
            return list(self._value)

    @method()
    def WriteValue(self, value: 'ay', options: 'a{sv}') -> None:  # type: ignore[override]
        # Respect offset for long writes; we only support offset 0
        try:
            offset_var = options.get("offset")
            if offset_var is not None and int(offset_var.value) != 0:
                # For simplicity, ignore non-zero offsets (not supported)
                return
        except Exception:
            pass
        self._value = bytes(value)

    @method()
    def StartNotify(self) -> None:  # type: ignore[override]
        self._notifying = True
        try:
            self.emit_properties_changed({"Notifying": Variant("b", True)})
        except Exception:
            pass
        emit_event({"type": "ble_subscribe", "char": self._uuid})
        # Push current value immediately so subscribers receive something right away
        try:
            if self._value:
                self.set_value_and_notify(self._value)
        except Exception:
            pass

    @method()
    def StopNotify(self) -> None:  # type: ignore[override]
        self._notifying = False
        try:
            self.emit_properties_changed({"Notifying": Variant("b", False)})
        except Exception:
            pass
        emit_event({"type": "ble_unsubscribe", "char": self._uuid})

    def set_value_and_notify(self, value: bytes) -> None:
        self._value = value
        try:
            # Emit PropertiesChanged for Value to notify subscribers
            self.emit_properties_changed({"Value": Variant("ay", self._value)})
        except Exception as e:  # noqa: BLE001
            emit_event({"type": "error", "message": f"notify failed: {e}"})


class HeartbeatCharacteristic(GattCharacteristic):
    def __init__(self, path: str, service_path: str):
        super().__init__(path, CHAR_HEARTBEAT_UUID, service_path, ["read", "notify"])
        self.heartbeat_counter = 0
        self._hb_thread = threading.Thread(target=self._hb_loop, daemon=True)
        self._hb_thread.start()

    def _hb_loop(self) -> None:
        while True:
            try:
                self.heartbeat_counter = (self.heartbeat_counter + 1) & 0xFFFFFFFF
                b = struct.pack('<I', self.heartbeat_counter)
                # update cached value regardless; clients can read
                self._value = b
                # if subscribed, send a notify via PropertiesChanged
                if self._notifying:
                    self.set_value_and_notify(b)
                    # Log connectivity heartbeat in sync with notifies
                    emit_event({"type": "heartbeat"})
                time.sleep(1.0)
            except Exception as e:  # noqa: BLE001
                emit_event({"type": "error", "message": f"hb_loop: {e}"})

    def ReadValue(self, options: 'a{sv}') -> 'ay':  # type: ignore[override]
        # Serve current heartbeat value and log a heartbeat read similar to macOS
        try:
            b = struct.pack('<I', self.heartbeat_counter)
            self._value = b
            emit_event({"type": "heartbeat"})
        except Exception as e:  # noqa: BLE001
            emit_event({"type": "error", "message": f"hb_read: {e}"})
        return list(self._value)


class AuthCharacteristic(GattCharacteristic):
    def __init__(self, path: str, service_path: str, expected_code: str):
        super().__init__(path, CHAR_AUTH_UUID, service_path, ["write", "write-without-response"])
        self._expected_code = expected_code

    def WriteValue(self, value: 'ay', options: 'a{sv}') -> None:  # type: ignore[override]
        super().WriteValue(value, options)
        try:
            code = bytes(value).decode("utf-8")
            if code == self._expected_code:
                emit_event({"type": "ble_auth_ok"})
            else:
                emit_event({"type": "ble_auth_failed"})
        except Exception as e:  # noqa: BLE001
            emit_event({"type": "error", "message": f"auth write: {e}"})


class ControlCharacteristic(GattCharacteristic):
    def __init__(self, path: str, service_path: str):
        super().__init__(path, CHAR_CONTROL_UUID, service_path, ["write", "write-without-response"])

    def WriteValue(self, value: 'ay', options: 'a{sv}') -> None:  # type: ignore[override]
        super().WriteValue(value, options)
        try:
            cmd = bytes(value).decode("utf-8")
            emit_event({"type": "ble_control", "cmd": cmd})
        except Exception as e:  # noqa: BLE001
            emit_event({"type": "error", "message": f"control write: {e}"})


class PoseCharacteristic(GattCharacteristic):
    def __init__(self, path: str, service_path: str):
        super().__init__(path, CHAR_POSE_UUID, service_path, ["write", "write-without-response"])

    def WriteValue(self, value: 'ay', options: 'a{sv}') -> None:  # type: ignore[override]
        super().WriteValue(value, options)
        try:
            buf = bytes(value) if not isinstance(value, (bytes, bytearray)) else value
            js = buf.decode("utf-8")
            try:
                raw = json.loads(js)
                emit_event({"type": "pose", "data": {"absolute_input": raw}})
            except Exception as e:  # noqa: BLE001
                emit_event({"type": "error", "message": f"pose json: {e}"})
        except Exception as e:  # noqa: BLE001
            emit_event({"type": "error", "message": f"pose write: {e}"})


class LEAdvertisement(ServiceInterface):
    def __init__(self, path: str, local_name: str, service_uuids: List[str]):
        super().__init__("org.bluez.LEAdvertisement1")
        self._path = path
        self._local_name = local_name
        self._service_uuids = service_uuids
        self._include_tx_power = False
        self._tx_power = 0  # dBm (int16)

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> "s":  # type: ignore[override]
        return "peripheral"

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> "s":  # type: ignore[override]
        return self._local_name

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> "as":  # type: ignore[override]
        return self._service_uuids

    @dbus_property(access=PropertyAccess.READ)
    def IncludeTxPower(self) -> "b":  # type: ignore[override]
        return self._include_tx_power

    @dbus_property(access=PropertyAccess.READ)
    def TxPower(self) -> "n":  # type: ignore[override]
        return self._tx_power

    @method()
    def Release(self) -> None:  # type: ignore[override]
        pass


class GattApplication(ServiceInterface):
    """Implements org.freedesktop.DBus.ObjectManager that BlueZ requires for a GATT app."""

    def __init__(self, path: str, managed: Dict[str, Dict[str, Dict[str, Variant]]]):
        super().__init__("org.freedesktop.DBus.ObjectManager")
        self._path = path
        self._managed = managed

    @method()
    def GetManagedObjects(self) -> "a{oa{sa{sv}}}":  # type: ignore[override]
        return self._managed


async def _run_ble_app(name: str, expected_code: str) -> None:
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    # Stop event set by SIGINT/SIGTERM
    stop_event = asyncio.Event()
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except Exception:
                pass
    except Exception:
        pass

    # Ensure adapter exists and is powered
    try:
        root_path = "/org/bluez/hci0"
        adapter_int = await bus.introspect("org.bluez", root_path)
        adapter_obj = bus.get_proxy_object("org.bluez", root_path, adapter_int)
        props = adapter_obj.get_interface("org.freedesktop.DBus.Properties")
        powered_var = await props.call_get("org.bluez.Adapter1", "Powered")
        powered = bool(powered_var.value)
        if not powered:
            # Do not try to set adapter power here (requires privileges and causes noisy errors).
            # Instead, emit a helpful message and continue.
            emit_event({"type": "warn", "message": "Bluetooth adapter is off. Run 'bluetoothctl power on' and retry."})
    except Exception as e:  # noqa: BLE001
        emit_event({"type": "error", "message": f"adapter check: {e}"})

    # Build GATT tree
    app_path = "/org/voodoocontrol/app"
    service_path = f"{app_path}/service0"
    hb_char_path = f"{service_path}/char0"
    auth_char_path = f"{service_path}/char1"
    ctrl_char_path = f"{service_path}/char2"
    pose_char_path = f"{service_path}/char3"

    service = GattService(service_path, SERVICE_UUID, True)
    hb_char = HeartbeatCharacteristic(hb_char_path, service_path)
    auth_char = AuthCharacteristic(auth_char_path, service_path, expected_code)
    ctrl_char = ControlCharacteristic(ctrl_char_path, service_path)
    pose_char = PoseCharacteristic(pose_char_path, service_path)

    # Build managed objects map for ObjectManager
    managed: Dict[str, Dict[str, Dict[str, Variant]]] = {
        service_path: {
            "org.bluez.GattService1": {
                "UUID": Variant("s", SERVICE_UUID),
                "Primary": Variant("b", True),
                "Includes": Variant("ao", []),
            }
        },
        hb_char_path: {
            "org.bluez.GattCharacteristic1": {
                "UUID": Variant("s", CHAR_HEARTBEAT_UUID),
                "Service": Variant("o", service_path),
                "Flags": Variant("as", ["read", "notify"]),
            }
        },
        auth_char_path: {
            "org.bluez.GattCharacteristic1": {
                "UUID": Variant("s", CHAR_AUTH_UUID),
                "Service": Variant("o", service_path),
                "Flags": Variant("as", ["write", "write-without-response"]),
            }
        },
        ctrl_char_path: {
            "org.bluez.GattCharacteristic1": {
                "UUID": Variant("s", CHAR_CONTROL_UUID),
                "Service": Variant("o", service_path),
                "Flags": Variant("as", ["write", "write-without-response"]),
            }
        },
        pose_char_path: {
            "org.bluez.GattCharacteristic1": {
                "UUID": Variant("s", CHAR_POSE_UUID),
                "Service": Variant("o", service_path),
                "Flags": Variant("as", ["write", "write-without-response"]),
            }
        },
    }

    # Export ObjectManager and all nodes
    app = GattApplication(app_path, managed)
    bus.export(app_path, app)
    bus.export(service_path, service)
    bus.export(hb_char_path, hb_char)
    bus.export(auth_char_path, auth_char)
    bus.export(ctrl_char_path, ctrl_char)
    bus.export(pose_char_path, pose_char)

    # Register application with BlueZ
    introspection = await bus.introspect("org.bluez", "/org/bluez/hci0")
    obj = bus.get_proxy_object("org.bluez", "/org/bluez/hci0", introspection)
    gatt_manager = obj.get_interface("org.bluez.GattManager1")

    # Register GATT application
    try:
        await gatt_manager.call_register_application(app_path, {})
        emit_event({"type": "ble_service_added", "uuid": SERVICE_UUID})
    except Exception as e:  # noqa: BLE001
        emit_event({"type": "error", "message": f"RegisterApplication: {e}"})

    # Register advertisement (using adapter root object for manager)
    adv_path = "/org/voodoocontrol/adv0"
    adv = LEAdvertisement(adv_path, name, [SERVICE_UUID])
    bus.export(adv_path, adv)
    adv_manager = None
    try:
        adapter_root = "/org/bluez/hci0"
        adv_introspection = await bus.introspect("org.bluez", adapter_root)
        adv_obj = bus.get_proxy_object("org.bluez", adapter_root, adv_introspection)
        adv_manager = adv_obj.get_interface("org.bluez.LEAdvertisingManager1")
        await adv_manager.call_register_advertisement(adv_path, {})
        emit_event({"type": "ble_advertising", "name": name})
        emit_event({"type": "ble_advertising_started"})
    except Exception as e:  # noqa: BLE001
        emit_event({"type": "error", "message": f"RegisterAdvertisement: {e}"})

    # Wait for Ctrl+C / SIGTERM
    try:
        await stop_event.wait()
    finally:
        # Cleanup: unregister advertisement and application
        try:
            if adv_manager is not None:
                await adv_manager.call_unregister_advertisement(adv_path)
        except Exception:
            pass
        try:
            await gatt_manager.call_unregister_application(app_path, {})
        except Exception:
            pass
        try:
            bus.disconnect()
        except Exception:
            pass


def run_ubuntu_peripheral(name: str, expected_code: str, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
    try:
        global _evt_cb
        _evt_cb = callback
        # Kick off asyncio loop and run until cancelled
        asyncio.run(_run_ble_app(name, expected_code))
    except KeyboardInterrupt:
        pass
    except Exception as e:  # noqa: BLE001
        emit_event({"type": "error", "message": f"BLE peripheral failed: {e}"})



