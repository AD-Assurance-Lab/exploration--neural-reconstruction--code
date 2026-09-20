"""Ask the open driving policy what it would do, frame by frame.

Input is one file from `render_paired_frames.py`. For each chosen pose the
script builds the window the policy expects, samples several trajectories, and
saves them all. Repeated samples matter: the decoder is stochastic, so the
spread of its own samples is the floor under every later comparison.

    python3 scripts/run_policy.py --frames data/frames/<scene>.npz \
        --model data/models --samples 8 --out data/responses

Output:

    traj    (P, S, T, 3) predicted paths in the ego frame
    poses   (P,) the pose index each prediction belongs to
    seconds per prediction, peak memory, and the text the policy produced
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

HISTORY_STEPS = 16      # 1.6 seconds at 10 Hz, the trained setting
FRAMES_PER_CAM = 4      # 0.4 seconds of vision
FRONT_WIDE_INDEX = 1    # the camera index the model expects for this view


def ego_frame_history(pose_world: np.ndarray, index: int) -> tuple[np.ndarray, np.ndarray]:
    """The last 16 poses, expressed in the ego frame at `index`."""
    start = index - HISTORY_STEPS + 1
    if start < 0:
        raise ValueError(f"pose {index} has no full history")
    window = pose_world[start:index + 1]
    here = np.linalg.inv(pose_world[index])
    local = np.einsum("ij,tjk->tik", here, window)
    xyz = local[:, :3, 3]
    rot = local[:, :3, :3]
    return xyz, rot


def build_inputs(helper, frames: np.ndarray, pose_world: np.ndarray, index: int, device: str):
    """One model input, from rendered frames and delivered poses."""
    first = index - FRAMES_PER_CAM + 1
    if first < 0:
        raise ValueError(f"pose {index} has no full vision window")
    window = frames[first:index + 1]                       # (4, H, W, 3)
    images = torch.from_numpy(window).permute(0, 3, 1, 2)  # (4, 3, H, W)
    images = images.unsqueeze(0)                           # (1 camera, 4, 3, H, W)
    camera_indices = torch.tensor([FRONT_WIDE_INDEX])

    messages = helper.create_message(frames=images.flatten(0, 1),
                                     camera_indices=camera_indices)
    xyz, rot = ego_frame_history(pose_world, index)
    return messages, (torch.from_numpy(xyz).float()[None, None],
                      torch.from_numpy(rot).float()[None, None])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", required=True, help="an npz from render_paired_frames.py")
    ap.add_argument("--model", default="data/models", help="local weights, or a hub name")
    ap.add_argument("--out", default="data/responses")
    ap.add_argument("--samples", type=int, default=8, help="trajectories per pose")
    ap.add_argument("--stride", type=int, default=10, help="use every Nth pose")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--attn", default="sdpa", choices=["sdpa", "flash_attention_2"])
    ap.add_argument("--temperature", type=float, default=0.6,
                    help="text sampling. 0 makes the reasoning step repeatable")
    ap.add_argument("--top-p", type=float, default=0.98)
    ap.add_argument("--tag", default="", help="suffix for the output name, for repeat runs")
    args = ap.parse_args()

    from alpamayo1_5 import helper
    from alpamayo1_5.models.alpamayo1_5 import Alpamayo1_5

    data = np.load(args.frames)
    frames, pose_world = data["frames"], data["pose_world"]
    first = max(HISTORY_STEPS, FRAMES_PER_CAM) - 1
    indices = list(range(first, len(frames), args.stride))
    if not indices:
        raise SystemExit("not enough frames for one window")

    model = Alpamayo1_5.from_pretrained(args.model, dtype=torch.bfloat16,
                                        attn_implementation=args.attn).to("cuda").eval()
    processor = helper.get_processor(model.tokenizer)

    paths, kept, texts, timings = [], [], [], []
    torch.cuda.reset_peak_memory_stats()
    for index in indices:
        messages, (xyz, rot) = build_inputs(helper, frames, pose_world, index, "cuda")
        tokenized = processor.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=False,
            continue_final_message=True, return_dict=True, return_tensors="pt")
        model_inputs = helper.to_device(
            {"tokenized_data": tokenized, "ego_history_xyz": xyz, "ego_history_rot": rot},
            "cuda")

        torch.cuda.manual_seed_all(args.seed)      # same seed at every pose
        start = time.time()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            pred_xyz, _pred_rot, extra = model.sample_trajectories_from_data_with_vlm_rollout(
                data=model_inputs, top_p=args.top_p, temperature=args.temperature,
                num_traj_samples=args.samples, max_generation_length=256,
                return_extra=True)
        timings.append(time.time() - start)
        paths.append(pred_xyz.float().cpu().numpy()[0, 0])   # (samples, T, 3)
        kept.append(index)
        texts.append(str(extra["cot"][0]) if "cot" in extra else "")
        print(f"pose {index:4d}  {timings[-1]:5.1f} s")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.frames).stem + (f"-{args.tag}" if args.tag else "")
    np.savez_compressed(out_dir / f"{stem}.npz",
                        traj=np.asarray(paths, dtype=np.float32),
                        poses=np.asarray(kept, dtype=int))
    report = {
        "frames_file": str(args.frames),
        "poses": len(kept),
        "samples_per_pose": args.samples,
        "seed": args.seed,
        "attention": args.attn,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "seconds_per_pose_mean": float(np.mean(timings)),
        "peak_gpu_gb": float(torch.cuda.max_memory_allocated()) / 1e9,
        "reasoning_first_pose": texts[0][:2000] if texts else "",
    }
    (out_dir / f"{stem}.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "reasoning_first_pose"}, indent=2))


if __name__ == "__main__":
    main()
