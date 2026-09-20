"""Build a small frame file so the policy pipeline can run without a renderer.

This is a plumbing test and nothing else. The images come from the lab's own
simulator captures, and the ego history is a straight line at a fixed speed. The
policy learned on real roads, so whatever it predicts here says nothing about
the policy and nothing about the scene. It only shows that the weights load,
that the inputs are shaped correctly, and what one prediction costs in memory
and in seconds.

    python3 scripts/make_smoke_frames.py --frames-dir <a folder of png frames> \
        --count 40 --out data/frames/smoke.npz
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

SPEED_MS = 10.0
STEP_S = 0.1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames-dir", required=True)
    ap.add_argument("--count", type=int, default=40)
    ap.add_argument("--out", default="data/frames/smoke.npz")
    args = ap.parse_args()

    files = sorted(Path(args.frames_dir).glob("*.png"))[:args.count]
    if len(files) < 20:
        raise SystemExit("need at least 20 frames")
    frames = np.stack([np.asarray(Image.open(f).convert("RGB")) for f in files])

    # A straight track at a fixed speed, so the history is well formed.
    poses = np.repeat(np.eye(4)[None], len(frames), axis=0)
    poses[:, 0, 3] = np.arange(len(frames)) * SPEED_MS * STEP_S

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, frames=frames.astype(np.uint8),
                        stamp_s=np.arange(len(frames)) * STEP_S,
                        pose_world=poses, pose_track=poses)
    print(f"wrote {out}, {frames.shape[0]} frames of {frames.shape[2]} by {frames.shape[1]}")


if __name__ == "__main__":
    main()
