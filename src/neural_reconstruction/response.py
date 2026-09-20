"""The measuring instrument: how far apart are two policy responses at one pose?

`PROTOCOL.md` asks for one number per pose, per policy, and it asks for the band
that number has to sit inside. This module computes both, and it keeps the two
apart on purpose. A gap without a band means nothing.

The policy in the first proof of concept predicts a trajectory rather than a
steering angle, and it samples that trajectory from a diffusion decoder. So the
response is a path, and the same input gives a slightly different path each
time. Both facts are handled here:

* `path_gap` reduces two paths to one distance, in meters.
* `sampling_spread` measures how far apart repeated samples of ONE input sit.
  That spread is the floor of the band. No reconstruction can be judged finer.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import combinations

import numpy as np

# The horizon the gap is measured over. The policy predicts 6.4 seconds at
# 10 Hz. A short horizon is dominated by the current lane position, and a long
# one by route choice, so the gap is reported at both.
HORIZONS_S = (1.0, 3.0, 6.0)
STEP_S = 0.1


def _clip(path: np.ndarray, horizon_s: float) -> np.ndarray:
    n = max(1, int(round(horizon_s / STEP_S)))
    return path[:n]


def path_gap(a: np.ndarray, b: np.ndarray, horizon_s: float = 3.0) -> float:
    """Mean distance in meters between two predicted paths, over one horizon.

    Both paths are (T, 2) or (T, 3) in the ego frame at the same pose. Only the
    ground plane counts, because a lateral error is what leaves a lane.
    """
    a, b = np.asarray(a, float)[:, :2], np.asarray(b, float)[:, :2]
    n = min(len(a), len(b))
    a, b = _clip(a[:n], horizon_s), _clip(b[:n], horizon_s)
    return float(np.linalg.norm(a - b, axis=1).mean())


def lateral_gap(a: np.ndarray, b: np.ndarray, horizon_s: float = 3.0) -> float:
    """The part of the gap that moves the car sideways, in meters."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = min(len(a), len(b))
    a, b = _clip(a[:n], horizon_s), _clip(b[:n], horizon_s)
    return float(np.abs(a[:, 1] - b[:, 1]).max())


def sampling_spread(samples: np.ndarray, horizon_s: float = 3.0) -> float:
    """How far apart repeated samples of one input sit, in meters.

    `samples` is (S, T, 2 or 3) from one identical input. The value returned is
    the mean pairwise distance. It is the noise floor of any gap measured with
    this policy, so report it beside every gap.
    """
    samples = np.asarray(samples, float)
    if len(samples) < 2:
        return 0.0
    pairs = [path_gap(x, y, horizon_s) for x, y in combinations(samples, 2)]
    return float(np.mean(pairs))


@dataclass
class PoseResult:
    """One pose, one policy, one pair of image sources."""

    pose_index: int
    horizon_s: float
    gap_m: float
    lateral_gap_m: float
    spread_a_m: float
    spread_b_m: float

    @property
    def floor_m(self) -> float:
        """The larger of the two sampling spreads. The gap must beat this."""
        return max(self.spread_a_m, self.spread_b_m)

    @property
    def above_floor(self) -> bool:
        return self.gap_m > self.floor_m


def compare(samples_a: np.ndarray, samples_b: np.ndarray,
            horizon_s: float = 3.0, pose_index: int = 0) -> PoseResult:
    """Compare two image sources at one pose.

    Each input is (S, T, 2 or 3): S repeated samples from the same policy on the
    same frame. The gap uses the mean path of each source, and the spread of
    each source travels with it.
    """
    samples_a = np.asarray(samples_a, float)
    samples_b = np.asarray(samples_b, float)
    mean_a = samples_a.mean(axis=0)
    mean_b = samples_b.mean(axis=0)
    return PoseResult(
        pose_index=pose_index,
        horizon_s=horizon_s,
        gap_m=path_gap(mean_a, mean_b, horizon_s),
        lateral_gap_m=lateral_gap(mean_a, mean_b, horizon_s),
        spread_a_m=sampling_spread(samples_a, horizon_s),
        spread_b_m=sampling_spread(samples_b, horizon_s),
    )


def summarize(results: list[PoseResult]) -> dict:
    """Per-pose results into the numbers a verdict needs."""
    if not results:
        return {}
    gaps = np.array([r.gap_m for r in results])
    floors = np.array([r.floor_m for r in results])
    return {
        "poses": len(results),
        "horizon_s": results[0].horizon_s,
        "gap_mean_m": float(gaps.mean()),
        "gap_peak_m": float(gaps.max()),
        "floor_mean_m": float(floors.mean()),
        "ratio_mean": float(gaps.mean() / floors.mean()) if floors.mean() else float("inf"),
        "poses_above_floor": int(sum(r.above_floor for r in results)),
        "worst_pose": int(results[int(gaps.argmax())].pose_index),
    }


def as_rows(results: list[PoseResult]) -> list[dict]:
    return [asdict(r) for r in results]
