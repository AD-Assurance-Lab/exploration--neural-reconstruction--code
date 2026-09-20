"""Build a frame file from a real recorded clip and its recorded poses.

The public reconstruction collection ships each scene with the real front-wide
video beside it, and the scene file carries the rig trajectory. That is enough
to ask a policy what it would do on the real road, at known poses, with no
renderer in the loop.

    python3 scripts/make_real_frames.py \
        --usdz data/public_scene/00040136.usdz \
        --video data/public_scene/camera_front_wide_120fov.mp4 \
        --seconds 8 --out data/frames/real-00040136.npz

Output matches `render_paired_frames.py`, so the rest of the pipeline does not
care which one made the file.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import numpy as np

TARGET_W, TARGET_H = 1920, 1080     # the policy's trained input size
POLICY_HZ = 10


def rig_poses(usdz: Path, camera: str):
    """Per-frame camera timestamps and rig poses, from the scene file."""
    with zipfile.ZipFile(usdz) as z:
        rig = json.loads(z.read("rig_trajectories.json"))["rig_trajectories"][0]
    key = next(k for k in rig["cameras_frame_timestamps_us"] if k.startswith(camera))
    stamps = np.asarray(rig["cameras_frame_timestamps_us"][key], dtype=np.int64)
    mats = np.asarray(rig["cameras_frame_T_rig_worlds"][key], dtype=float)
    # Each frame carries two poses, the start and the end of the exposure.
    # Take the start, which is when the shutter opened.
    if mats.ndim == 4:
        mats = mats[:, 0]
    # The file already stores the rig pose in the world, which is what the rest
    # of the pipeline wants. Inverting it here mirrors the ego history, and the
    # policy then predicts a path that runs backwards.
    poses = mats
    return stamps, poses


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--usdz", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--camera", default="camera_front_wide_120fov")
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import av
    from PIL import Image

    stamps, poses = rig_poses(Path(args.usdz), args.camera)
    container = av.open(args.video)
    stream = container.streams.video[0]
    video_hz = float(stream.average_rate)
    step = max(1, int(round(video_hz / POLICY_HZ)))
    wanted = int(args.seconds * POLICY_HZ)

    frames, kept = [], []
    for index, frame in enumerate(container.decode(stream)):
        if index % step:
            continue
        if index >= len(poses):
            break
        image = Image.fromarray(frame.to_ndarray(format="rgb24"))
        if image.size != (TARGET_W, TARGET_H):
            image = image.resize((TARGET_W, TARGET_H), Image.BILINEAR)
        frames.append(np.asarray(image, dtype=np.uint8))
        kept.append(index)
        if len(frames) >= wanted:
            break

    kept = np.asarray(kept)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out,
                        frames=np.asarray(frames, dtype=np.uint8),
                        stamp_s=(stamps[kept] - stamps[kept][0]) / 1e6,
                        pose_world=poses[kept],
                        pose_track=poses[kept])
    moved = np.linalg.norm(poses[kept][-1][:3, 3] - poses[kept][0][:3, 3])
    print(f"wrote {out}: {len(frames)} frames at {POLICY_HZ} Hz, "
          f"{frames[0].shape[1]} by {frames[0].shape[0]}, the rig moved {moved:.1f} m")


if __name__ == "__main__":
    main()
