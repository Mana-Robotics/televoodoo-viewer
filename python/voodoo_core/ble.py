import json
import random
import string
import time
from typing import Callable, Iterator
from .pose import Pose


def generate_session() -> tuple[str, str]:
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
    name = f"prsntr{suffix}"
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return name, code


def simulate_pose_stream() -> Iterator[Pose]:
    t = 0.0
    while True:
        t += 0.05
        yield Pose(
            pose_start=True,
            x=0.1 * random.uniform(-1, 1),
            y=0.1 * random.uniform(-1, 1),
            z=0.1 * random.uniform(-1, 1),
            x_rot=0.0,
            y_rot=0.0,
            z_rot=0.0,
            qx=0.0,
            qy=0.0,
            qz=0.0,
            qw=1.0,
        )
        time.sleep(0.033)


def run_simulation(on_pose: Callable[[Pose], None]) -> None:
    for p in simulate_pose_stream():
        on_pose(p)


