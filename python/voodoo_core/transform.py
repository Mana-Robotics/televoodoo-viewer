from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from .pose import Pose


@dataclass
class OutputConfig:
    includeFormats: Dict[str, bool]
    includeOrientation: Dict[str, bool]
    scale: float
    outputAxes: Dict[str, float]


class PoseTransformer:
    def __init__(self, config: OutputConfig) -> None:
        self.config = config
        self._origin: Pose | None = None

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

        absolute_transformed = {
            "x": self._apply_scale(pose.x * self.config.outputAxes.get("x", 1)),
            "y": self._apply_scale(pose.y * self.config.outputAxes.get("y", 1)),
            "z": self._apply_scale(pose.z * self.config.outputAxes.get("z", 1)),
            "qx": pose.qx,
            "qy": pose.qy,
            "qz": pose.qz,
            "qw": pose.qw,
        }

        delta_transformed = None
        if self._origin is not None:
            delta_transformed = {
                "dx": self._apply_scale((pose.x - self._origin.x) * self.config.outputAxes.get("x", 1)),
                "dy": self._apply_scale((pose.y - self._origin.y) * self.config.outputAxes.get("y", 1)),
                "dz": self._apply_scale((pose.z - self._origin.z) * self.config.outputAxes.get("z", 1)),
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


