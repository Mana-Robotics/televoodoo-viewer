from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import math
from .pose import Pose


@dataclass
class OutputConfig:
    includeFormats: Dict[str, bool]
    includeOrientation: Dict[str, bool]
    scale: float
    outputAxes: Dict[str, float]
    # Pose of Target Coordinate System relative to reference/world (Euler radians)
    targetFrame: Optional[Dict[str, float]] = None


class PoseTransformer:
    def __init__(self, config: OutputConfig) -> None:
        self.config = config
        self._origin: Pose | None = None

    @staticmethod
    def _quat_multiply(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        ax, ay, az, aw = a
        bx, by, bz, bw = b
        return (
            aw*bx + ax*bw + ay*bz - az*by,
            aw*by - ax*bz + ay*bw + az*bx,
            aw*bz + ax*by - ay*bx + az*bw,
            aw*bw - ax*bx - ay*by - az*bz,
        )

    @staticmethod
    def _quat_conjugate(q: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        x, y, z, w = q
        return (-x, -y, -z, w)

    @staticmethod
    def _rotate_vector_by_quat(v: Tuple[float, float, float], q: Tuple[float, float, float, float]) -> Tuple[float, float, float]:
        # v' = q * (v,0) * q_conj
        vx, vy, vz = v
        x, y, z, w = q
        # compute cross products efficiently
        # t = 2 * cross(q.xyz, v)
        tx = 2 * (y*vz - z*vy)
        ty = 2 * (z*vx - x*vz)
        tz = 2 * (x*vy - y*vx)
        # v' = v + w*t + cross(q.xyz, t)
        vpx = vx + w*tx + (y*tz - z*ty)
        vpy = vy + w*ty + (z*tx - x*tz)
        vpz = vz + w*tz + (x*ty - y*tx)
        return (vpx, vpy, vpz)

    def _apply_scale(self, value: float) -> float:
        return value * float(self.config.scale)

    def transform(self, pose: Pose) -> Dict[str, Any]:
        if self._origin is None and pose.pose_start:
            self._origin = pose

        absolute_input = {
            "pose_start": pose.pose_start,
            "x": pose.x,
            "y": pose.y,
            "z": pose.z,
            "qx": pose.qx,
            "qy": pose.qy,
            "qz": pose.qz,
            "qw": pose.qw,
        }

        if self.config.includeOrientation.get("euler_radian") or self.config.includeOrientation.get("euler_degree"):
            absolute_input.update({
                "x_rot": pose.x_rot,
                "y_rot": pose.y_rot,
                "z_rot": pose.z_rot,
            })

        delta_input = None
        if self._origin is not None:
            delta_input = {
                "dx": pose.x - self._origin.x,
                "dy": pose.y - self._origin.y,
                "dz": pose.z - self._origin.z,
            }

        # Transform pose from reference/world to target coordinates if targetFrame provided
        tx, ty, tz = 0.0, 0.0, 0.0
        # target orientation in radians (XYZ)
        txr, tyr, tzr = 0.0, 0.0, 0.0
        if self.config.targetFrame:
            tx = float(self.config.targetFrame.get("x", 0.0))
            ty = float(self.config.targetFrame.get("y", 0.0))
            tz = float(self.config.targetFrame.get("z", 0.0))
            txr = float(self.config.targetFrame.get("x_rot", 0.0))
            tyr = float(self.config.targetFrame.get("y_rot", 0.0))
            tzr = float(self.config.targetFrame.get("z_rot", 0.0))

        # build quaternion from Euler XYZ radians
        cx, sx = math.cos(txr/2.0), math.sin(txr/2.0)
        cy, sy = math.cos(tyr/2.0), math.sin(tyr/2.0)
        cz, sz = math.cos(tzr/2.0), math.sin(tzr/2.0)
        # XYZ intrinsic
        tqw = cx*cy*cz - sx*sy*sz
        tqx = sx*cy*cz + cx*sy*sz
        tqy = cx*sy*cz - sx*cy*sz
        tqz = cx*cy*sz + sx*sy*cz

        # position in target: R_T^T * (p_ref - t)
        px, py, pz = pose.x - tx, pose.y - ty, pose.z - tz
        invT = (-tqx, -tqy, -tqz, tqw)
        tposx, tposy, tposz = self._rotate_vector_by_quat((px, py, pz), invT)
        # orientation in target: qT^{-1} * q_ref
        qrel = self._quat_multiply(invT, (pose.qx, pose.qy, pose.qz, pose.qw))

        absolute_transformed = {
            "x": self._apply_scale(tposx * self.config.outputAxes.get("x", 1)),
            "y": self._apply_scale(tposy * self.config.outputAxes.get("y", 1)),
            "z": self._apply_scale(tposz * self.config.outputAxes.get("z", 1)),
            "qx": qrel[0],
            "qy": qrel[1],
            "qz": qrel[2],
            "qw": qrel[3],
        }

        delta_transformed = None
        if self._origin is not None:
            dx = pose.x - self._origin.x
            dy = pose.y - self._origin.y
            dz = pose.z - self._origin.z
            # rotate delta by inv target rotation, then scale/axes
            ddx, ddy, ddz = self._rotate_vector_by_quat((dx, dy, dz), invT)
            delta_transformed = {
                "dx": self._apply_scale(ddx * self.config.outputAxes.get("x", 1)),
                "dy": self._apply_scale(ddy * self.config.outputAxes.get("y", 1)),
                "dz": self._apply_scale(ddz * self.config.outputAxes.get("z", 1)),
            }

        result: Dict[str, Any] = {}
        if self.config.includeFormats.get("absolute_input"):
            result["absolute_input"] = absolute_input
        if self.config.includeFormats.get("delta_input") and delta_input is not None:
            result["delta_input"] = delta_input
        if self.config.includeFormats.get("absolute_transformed"):
            result["absolute_transformed"] = absolute_transformed
        if self.config.includeFormats.get("delta_transformed") and delta_transformed is not None:
            result["delta_transformed"] = delta_transformed
        return result


