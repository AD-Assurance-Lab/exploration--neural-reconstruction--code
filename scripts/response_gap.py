"""Compare two sets of policy responses, pose by pose.

Give it two files from `run_policy.py` that came from the same camera path. It
reports the gap at each pose, the policy's own sampling spread beside it, and
the ratio between them. A gap under the spread is not a measurement.

    python3 scripts/response_gap.py --a data/responses/<clear>.npz \
        --b data/responses/<snow>.npz --horizon 3.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from neural_reconstruction import response as R      # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True, help="one response file, usually the clear one")
    ap.add_argument("--b", required=True, help="the other response file")
    ap.add_argument("--horizon", type=float, default=3.0, help="seconds of path compared")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    a, b = np.load(args.a), np.load(args.b)
    poses_a, poses_b = list(a["poses"]), list(b["poses"])
    shared = [p for p in poses_a if p in poses_b]
    if not shared:
        raise SystemExit("the two files share no pose, so there is nothing to compare")

    results = []
    for pose in shared:
        results.append(R.compare(a["traj"][poses_a.index(pose)],
                                 b["traj"][poses_b.index(pose)],
                                 horizon_s=args.horizon, pose_index=int(pose)))

    summary = R.summarize(results)
    summary["a"], summary["b"] = args.a, args.b
    print(json.dumps(summary, indent=2))
    if summary["gap_mean_m"] <= summary["floor_mean_m"]:
        print("\nThe gap sits inside the policy's own sampling spread. "
              "Nothing is measured here yet.")
    if args.out:
        Path(args.out).write_text(json.dumps(
            {"summary": summary, "per_pose": R.as_rows(results)}, indent=2))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
