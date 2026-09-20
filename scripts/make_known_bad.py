"""Paint the known-bad fog on a rendered frame set.

`PROTOCOL.md` section 5 asks for a control that the check has to reject, and it
names the one the lab already measured. An analytic fog model reproduced
simulator fog at road-ROI R-squared 0.848, drove one policy 23.8 times harder
than real fog, and stayed faithful at 1.2 times for the other.

This script paints that model onto frames, with a row index standing in for
depth. Nobody should mistake this for a disturbance we believe. It exists so the
instrument has something it must reject before we trust any other verdict.

    python3 scripts/make_known_bad.py --frames data/frames/<scene>.npz \
        --beta 0.06 --out data/frames
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def koschmieder(frames: np.ndarray, beta: float, horizon_l: float = 210.0) -> np.ndarray:
    """Attenuate toward a bright horizon, with the image row standing for depth.

    A row proxy is wrong on purpose. Real depth comes from the reconstruction,
    and the point of a control is that it is wrong in a way we can measure.
    """
    height = frames.shape[1]
    row = np.arange(height, dtype=np.float32)
    depth = 4.0 + 120.0 * np.exp(-3.0 * (row / height))      # far at the top
    transmission = np.exp(-beta * depth)[None, :, None, None]
    out = frames.astype(np.float32) * transmission + horizon_l * (1.0 - transmission)
    return np.clip(out, 0, 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", required=True)
    ap.add_argument("--beta", type=float, default=0.06, help="extinction, per meter")
    ap.add_argument("--out", default="data/frames")
    args = ap.parse_args()

    data = dict(np.load(args.frames))
    data["frames"] = koschmieder(data["frames"], args.beta)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (Path(args.frames).stem + f"-knownbad-beta{args.beta:g}.npz")
    np.savez_compressed(out, **data)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
