# CLAUDE.md - read this before doing anything

New repository, deliberately not yet started. Real-world pose-paired disturbance endpoints
via neural scene reconstruction. See `README.md`.

## Do not start this before its dependencies

It is placed on the roadmap now because it is the highest-ceiling direction and because
work elsewhere should be shaped to feed it. It is not the place to spend effort today.

Blocked on three things:

1. **The MCity winter campaign** (`dataset--winter-driving--*`), which supplies the real
   paired ground truth a reconstruction has to be checked against.
2. **`formal-verification--verifier-scaling--code`**, which decides whether certifying on
   reconstructed imagery is affordable at all.
3. **The behavioral-validity protocol** (RESEARCH_DIRECTIONS.md, Q6), which supplies the test
   a reconstruction has to pass.

## The one rule that must not be violated here

**A reconstruction is validated behaviorally, never on image fidelity.**

The lab's own measurement is the caution. An analytic fog model reproduced CARLA fog at
road-ROI R-squared 0.848, which is a good image score, and drove one policy 23.8 times harder
than real fog while staying faithful (1.2x) for another. It was **most wrong about the better
policy**. Certifying against it would have been rigorous reasoning about a disturbance the
policy never experiences.

PSNR, SSIM and R-squared are therefore not acceptance criteria for anything in this
repository. The acceptance criterion is: **at matched poses, the policy responds to the
reconstruction the way it responds to the real frame.** Design that check before building
anything, because it is the difference between this being a contribution and it being a
better-looking version of a mistake we already made.

## Why paired poses are the whole point

Our verified family needs `x_clear` and `x_cond` at an **identical camera pose**. No published
adverse-weather dataset provides that. ACDC was tested and rejected: no pixel correspondence,
auto-exposed, video-denoised, no controlled clear baseline, no depth. Every epsilon-box
derived from it was withdrawn.

Reconstruction is one of only two ways to get paired endpoints. The other is deliberate
collection, which is the MCity campaign. They are complementary: collection gives ground
truth on one route in one season, reconstruction generalizes to any logged drive.

## Tooling notes

CARLA 0.9.16 targets NVIDIA NuRec, which reconstructs real driving scenes from camera and
LiDAR into CARLA. Its inputs are what a log-ingestion pipeline already produces. There is
directly relevant experience in Zach's Isuzu CARLA scenario-testing work, which ingests real
camera and LiDAR rosbags and already targets 0.9.16.

Reference: `_references/autonomous_driving/nvidia_2026_omnidreams.pdf`.

## Inherited standing rules

The lab-wide rules apply from the moment code exists here: blind protocol with verdicts
committed before closed-loop runs, failure rates over at least 10 repetitions with Wilson
intervals, a known-bad negative control, no vendoring of `auto_LiRPA`, and no trading
experimental quality for speed. See
`formal-verification--automated-driving--code/CLAUDE.md`.
