"""Build a frame file from frames the reconstruction engine rendered.

The engine renders along the recorded trajectory, one image per recorded camera
frame. So rendered image number N sits at the same pose as recorded video frame
number N, and the pair is what the acceptance test compares.

    python3 scripts/make_rendered_frames.py \
        --rendered data/rendered/clear/camera_front_wide_120fov \
        --usdz data/public_scene/00040136.usdz \
        --seconds 8 --out data/frames/rebuilt-00040136.npz

The output matches `make_real_frames.py`, including the pose of every frame, so
the two files differ only in where the pixels came from.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_real_frames import rig_poses, TARGET_W, TARGET_H, POLICY_HZ   # noqa: E402

VIDEO_HZ = 30


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rendered", required=True, help="a directory of rendered images")
    ap.add_argument("--usdz", required=True, help="the scene the poses come from")
    ap.add_argument("--camera", default="camera_front_wide_120fov")
    ap.add_argument("--rendered-step", type=int, default=1,
                    help="the frame step the renderer ran with")
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    stamps, poses = rig_poses(Path(args.usdz), args.camera)
    files = sorted(Path(args.rendered).glob("*.png"))
    step = VIDEO_HZ // POLICY_HZ
    wanted = int(args.seconds * POLICY_HZ)
    # Rendered file k holds camera frame k times the render step. We want every
    # third camera frame, which is 10 Hz.
    pairs = [(k, k * args.rendered_step) for k in range(len(files))
             if (k * args.rendered_step) % step == 0]
    pairs = [(k, n) for k, n in pairs if n < len(poses)][:wanted]
    if len(pairs) < wanted:
        print(f"only {len(pairs)} frames available, wanted {wanted}")
    kept = [n for _, n in pairs]

    frames = []
    for file_index, _ in pairs:
        image = Image.open(files[file_index]).convert("RGB")
        if image.size != (TARGET_W, TARGET_H):
            image = image.resize((TARGET_W, TARGET_H), Image.BILINEAR)
        frames.append(np.asarray(image, dtype=np.uint8))

    kept = np.asarray(kept)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out,
                        frames=np.asarray(frames, dtype=np.uint8),
                        stamp_s=(stamps[kept] - stamps[kept][0]) / 1e6,
                        pose_world=poses[kept],
                        pose_track=poses[kept],
                        frame_index=kept)
    print(f"wrote {out}: {len(frames)} rendered frames at {POLICY_HZ} Hz, "
          f"{frames[0].shape[1]} by {frames[0].shape[0]}")


if __name__ == "__main__":
    main()
