# exploration--neural-reconstruction--code

Real-world pose-paired disturbance endpoints from neural scene reconstruction.
See `README.md`.

**Deliberately not started.** It sits on the roadmap because it has the highest
ceiling, and because work elsewhere should be shaped to feed it. Do not spend
effort here today.

## Three things block it

1. **The MCity winter campaign** (`dataset--winter-driving--*`). It supplies the
   real paired ground truth that a reconstruction must be checked against.
2. **`formal-verification--verifier-scaling--code`**. It decides whether
   certifying on reconstructed images is affordable at all.
3. **The behavioural-validity protocol** (RESEARCH_DIRECTIONS.md, Q6). It supplies
   the test a reconstruction must pass.

## The one rule you must not break

**Validate a reconstruction behaviourally. Never on image fidelity.**

The lab's own measurement is the warning. An analytic fog model reproduced CARLA
fog at road-ROI R-squared 0.848, which is a good image score. It drove one policy
23.8 times harder than real fog, and stayed faithful, at 1.2 times, for another.
It was most wrong about the better policy. Certifying against it would have been
rigorous reasoning about a disturbance the policy never meets.

So PSNR, SSIM and R-squared are not acceptance criteria here. The acceptance
criterion is this: at matched poses, the policy responds to the reconstruction the
way it responds to the real frame. Design that check before you build anything. It
is the difference between a contribution and a better-looking version of a mistake
the lab already made.

## Why paired poses are the whole point

Our verified family needs `x_clear` and `x_cond` at one identical camera pose. No
published adverse-weather dataset gives that. The lab tested ACDC and rejected it:
no pixel correspondence, auto-exposed, video-denoised, no controlled clear
baseline, no depth. Every epsilon-box derived from it was withdrawn.

Reconstruction is one of only two ways to get paired endpoints. The other is
deliberate collection, which is the MCity campaign. They complement each other.
Collection gives ground truth on one route in one season. Reconstruction
generalizes to any logged drive.

## Tooling notes

CARLA 0.9.16 targets NVIDIA NuRec, which reconstructs real driving scenes from
camera and LiDAR into CARLA. Its inputs are what a log-ingestion pipeline already
produces. Zach's Isuzu CARLA scenario-testing work ingests real camera and LiDAR
rosbags and already targets 0.9.16.

Reference: `_references/autonomous_driving/nvidia_2026_omnidreams.pdf`.

## Standing rules

The lab rules apply from the moment code exists here. Commit verdicts to git
before the closed-loop run. Keep a known-bad negative control. Do not vendor
`auto_LiRPA`. Never trade experimental quality for speed. Read
`formal-verification--steering--code/CLAUDE.md` and
`formal-verification--aeb--code/CLAUDE.md` for the current repetition rule, which
changed from ten repetitions to three.
