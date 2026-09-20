"""Make the demonstration videos and the report figures.

It reads the frame files and the saved policy responses, then writes:

    report/figures/frame_clear.png    one real frame
    report/figures/frame_rebuilt.png  the reconstruction at that pose
    report/figures/frame_fog.png      the known-bad fog on the real frame
    report/figures/gap_horizon.pdf    three sources of path difference
    report/figures/gap_time.pdf       the reconstruction gap at every pose
    report/demo.mp4                   real against the reconstruction
    report/demo_fog.mp4               real against the known-bad fog

    python3 scripts/make_demo.py
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from neural_reconstruction import response as R      # noqa: E402

HORIZONS = (1.0, 3.0, 6.0)
ROOT = Path(__file__).resolve().parents[1]
REAL_FRAMES = "real-00040136.npz"
FOG_FRAMES = "real-00040136-knownbad-beta0.06.npz"
REBUILT_FRAMES = "rebuilt-00040136.npz"


def load(name: str) -> dict:
    d = np.load(ROOT / "data" / "responses" / name)
    return {"traj": d["traj"], "poses": list(d["poses"])}


def gap_series(a: dict, b: dict, horizon: float):
    shared = [p for p in a["poses"] if p in b["poses"]]
    out = []
    for p in shared:
        out.append(R.compare(a["traj"][a["poses"].index(p)],
                             b["traj"][b["poses"].index(p)],
                             horizon_s=horizon, pose_index=int(p)))
    return shared, out


def make_figures(real, fog, rebuilt, sampled, out_dir: Path) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 8, "font.family": "serif",
                         "axes.spines.top": False, "axes.spines.right": False})

    summary = {"horizons": {}}
    fog_mean, fog_peak, reb_mean, reb_peak, spread = [], [], [], [], []
    for h in HORIZONS:
        g = np.array([r.gap_m for r in gap_series(real, fog, h)[1]])
        b = np.array([r.gap_m for r in gap_series(real, rebuilt, h)[1]])
        s = np.array([R.sampling_spread(sampled["traj"][i], h)
                      for i in range(sampled["traj"].shape[0])])
        fog_mean.append(g.mean()); fog_peak.append(g.max())
        reb_mean.append(b.mean()); reb_peak.append(b.max())
        spread.append(s.mean())
        summary["horizons"][h] = {
            "fog_mean_m": float(g.mean()), "fog_peak_m": float(g.max()),
            "rebuilt_mean_m": float(b.mean()), "rebuilt_peak_m": float(b.max()),
            "spread_mean_m": float(s.mean()), "poses": int(len(b))}

    fig, ax = plt.subplots(figsize=(3.3, 1.75), constrained_layout=True)
    x = np.arange(len(HORIZONS))
    ax.bar(x - 0.26, reb_mean, 0.25, label="the reconstruction", color="#2f855a")
    ax.bar(x, fog_mean, 0.25, label="the known-bad fog", color="#2b6cb0")
    ax.bar(x + 0.26, spread, 0.25, label="the policy's own sampling", color="#c05621")
    ax.plot(x - 0.26, reb_peak, "k^", markersize=4, label="worst pose")
    ax.plot(x, fog_peak, "k^", markersize=4)
    ax.set_xticks(x); ax.set_xticklabels([f"{h:g} s" for h in HORIZONS])
    ax.set_xlabel("prediction horizon"); ax.set_ylabel("path difference (m)")
    ax.legend(frameon=False, fontsize=6.5, loc="upper left")
    fig.savefig(out_dir / "gap_horizon.pdf"); plt.close(fig)

    poses, results = gap_series(real, rebuilt, 3.0)
    fig, ax = plt.subplots(figsize=(3.3, 1.8), constrained_layout=True)
    ax.plot(np.asarray(poses) / 10.0, [r.gap_m for r in results], color="#2f855a", lw=1.2)
    ax.axhline(0.0, color="0.6", lw=0.8, ls="--")
    ax.set_xlabel("time into the clip (s)")
    ax.set_ylabel("reconstruction gap\nat 3 s (m)")
    fig.savefig(out_dir / "gap_time.pdf"); plt.close(fig)
    return summary


def panel(image_a, image_b, traj_a, traj_b, second, gap, out_path, title_b):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(12.8, 6.4), dpi=100)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.35, 1.0], hspace=0.16, wspace=0.05)
    for col, (image, title) in enumerate(((image_a, "real frame"), (image_b, title_b))):
        ax = fig.add_subplot(grid[0, col])
        ax.imshow(image); ax.set_axis_off(); ax.set_title(title, fontsize=11)

    ax = fig.add_subplot(grid[1, :])
    ax.plot(traj_a[:, 0], traj_a[:, 1], color="#2b6cb0", lw=2,
            label="planned path, real frame")
    ax.plot(traj_b[:, 0], traj_b[:, 1], color="#c05621", lw=2, ls="--",
            label="planned path, the other frame")
    ax.set_xlim(0, 130); ax.set_ylim(-6, 6)
    ax.set_xlabel("distance ahead (m)", fontsize=10)
    ax.set_ylabel("sideways (m)", fontsize=10)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.set_title(f"t = {second:4.1f} s,  the two paths differ by {gap:.2f} m over three seconds",
                 fontsize=11)
    fig.savefig(out_path, facecolor="white")
    plt.close(fig)


def make_video(real, other, frames_b: str, title_b: str, out_path: Path,
               fps: int = 10) -> int:
    frames_a = np.load(ROOT / "data/frames" / REAL_FRAMES)["frames"]
    frames_b_data = np.load(ROOT / "data/frames" / frames_b)["frames"]
    shared = [p for p in real["poses"] if p in other["poses"]]

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for n, pose in enumerate(shared):
            ta = real["traj"][real["poses"].index(pose)][0]
            tb = other["traj"][other["poses"].index(pose)][0]
            panel(frames_a[pose][::2, ::2], frames_b_data[pose][::2, ::2], ta, tb,
                  pose / 10.0, R.path_gap(ta, tb, 3.0), tmp / f"{n:04d}.png", title_b)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
                        "-i", str(tmp / "%04d.png"), "-c:v", "libx264", "-pix_fmt",
                        "yuv420p", "-crf", "20", str(out_path)], check=True)
    return len(shared)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args()

    out_dir = ROOT / "report" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    real = load("real-00040136-dense.npz")
    fog = load("real-00040136-knownbad-beta0.06-dense.npz")
    rebuilt = load("rebuilt-00040136-dense.npz")
    sampled = load("real-00040136-sampled.npz")

    import imageio.v3 as iio
    for name, source in (("frame_clear.png", REAL_FRAMES),
                         ("frame_fog.png", FOG_FRAMES),
                         ("frame_rebuilt.png", REBUILT_FRAMES)):
        iio.imwrite(out_dir / name,
                    np.load(ROOT / "data/frames" / source)["frames"][40][::2, ::2])

    summary = make_figures(real, fog, rebuilt, sampled, out_dir)
    if not args.no_video:
        summary["video_poses"] = make_video(
            real, rebuilt, REBUILT_FRAMES, "the reconstruction, at the same pose",
            ROOT / "report" / "demo.mp4")
        make_video(real, fog, FOG_FRAMES, "the known-bad fog on the same frame",
                   ROOT / "report" / "demo_fog.mp4")
    (ROOT / "report" / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
