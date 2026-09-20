"""Render one camera path through several reconstructed scenes.

The three sample scenes hold the same real clip in clear, rain and snow. Each
scene replays the same recorded ego track, so the camera visits the same pose in
all three. That is the pose pairing the whole study needs, and this script
writes it to disk.

Output, one file per scene:

    frames      (T, H, W, 3) uint8, the front-wide camera
    pose_world  (T, 4, 4) float64, the pose the simulator delivered
    pose_track  (T, 4, 4) float64, the pose the recorded track asked for
    stamp_s     (T,) float64

Run the simulator through the lab launcher first, never by hand:

    python3 -m carla_determinism launch --port 2000

Then:

    python3 scripts/render_paired_frames.py \
        --usdz data/scenes/<clip>.usdz data/scenes/<clip>-snow.usdz \
        --out data/frames --seconds 8
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import numpy as np

NUREC_EXAMPLES = Path("/home/za/carla/PythonAPI/examples/nvidia/nurec")

logging.basicConfig(format="%(asctime)s %(levelname)-7s %(message)s", level=logging.INFO)
log = logging.getLogger("render")


def load_nurec_modules():
    """The integration ships with CARLA, so borrow it rather than copy it."""
    if not NUREC_EXAMPLES.is_dir():
        raise SystemExit(f"no reconstruction example at {NUREC_EXAMPLES}")
    sys.path.insert(0, str(NUREC_EXAMPLES))
    os.chdir(NUREC_EXAMPLES)          # the example reads its camera yaml by name
    import nurec_integration          # noqa: E402
    import constants                  # noqa: E402
    return nurec_integration, constants


def pick_camera(scenario, wanted: str) -> str:
    """Use a camera the reconstruction already holds, with its own calibration.

    A camera named this way keeps the rig transform and the intrinsics of the
    real sensor, so a rendered frame lines up with the recorded one.
    """
    names = scenario.get_available_cameras()
    if not names:
        raise SystemExit("the scene lists no cameras")
    if wanted in names:
        return wanted
    forward = [n for n in names if "front_wide" in n]
    chosen = forward[0] if forward else names[0]
    log.info("camera %r not in the scene, using %r of %s", wanted, chosen, names)
    return chosen


def matrix(transform) -> np.ndarray:
    """A CARLA transform as a 4 by 4 matrix."""
    return np.array(transform.get_matrix(), dtype=float)


def render_one(usdz: Path, out_dir: Path, seconds: float, port: int,
               nurec_port: int, resolution_ratio: float, camera: str) -> Path:
    import carla
    nurec_integration, constants = load_nurec_modules()

    client = carla.Client("127.0.0.1", port)
    client.set_timeout(120.0)

    frames, stamps = [], []
    with nurec_integration.NurecScenario(client, str(usdz), port=nurec_port,
                                         move_spectator=False, fps=30) as scenario:
        name = pick_camera(scenario, camera)

        def on_image(image):
            array = np.asarray(image)
            if array.ndim == 3 and array.shape[2] == 4:
                array = array[:, :, :3]
            frames.append(array.copy())
            stamps.append(scenario.seconds_since_start())

        scenario.add_camera(name, on_image, framerate=10,
                            resolution_ratio=resolution_ratio)

        ego = scenario.actor_mapping[constants.EGO_TRACK_ID]
        delivered, asked = [], []

        scenario.start_replay()
        while not scenario.is_done() and scenario.seconds_since_start() < seconds:
            scenario.tick()
            delivered.append(matrix(ego.actor_inst.get_transform()))
            track_pose = getattr(ego, "current_track_transform", None)
            asked.append(matrix(track_pose) if track_pose is not None else np.full((4, 4), np.nan))

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (usdz.stem + ".npz")
    np.savez_compressed(out,
                        frames=np.asarray(frames, dtype=np.uint8),
                        stamp_s=np.asarray(stamps, dtype=float),
                        pose_world=np.asarray(delivered, dtype=float),
                        pose_track=np.asarray(asked, dtype=float))
    log.info("wrote %s, %d frames, %d poses", out, len(frames), len(delivered))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--usdz", nargs="+", required=True, help="scene files, in any order")
    ap.add_argument("--out", default="data/frames")
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--port", type=int, default=2000)
    ap.add_argument("--nurec-port", type=int, default=46435)
    ap.add_argument("--camera", default="camera_front_wide_120fov",
                    help="a camera the reconstruction holds")
    ap.add_argument("--resolution-ratio", type=float, default=0.5,
                    help="fraction of the rig resolution, 1.0 is 3848 by 2168")
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    for name in args.usdz:
        render_one(Path(name).resolve(), out_dir, args.seconds,
                   args.port, args.nurec_port, args.resolution_ratio, args.camera)


if __name__ == "__main__":
    main()
