# neural-reconstruction--automated-driving--code

Real-world pose-paired disturbance endpoints via neural scene reconstruction.

**Owner:** unassigned. **Status:** acceptance protocol frozen 2026-09-18. The measuring
instrument runs, and it has its first numbers on a real road (2026-09-19). See
[PROOF_OF_CONCEPT.md](PROOF_OF_CONCEPT.md) and [TOOLING.md](TOOLING.md).

## The problem it solves

Our verified disturbance family needs two frames, `x_clear` and `x_cond`, **at an identical
camera pose**. Nobody publishes that.

We established why with ACDC: no pixel correspondence between adverse and reference frames,
auto-exposed so absolute photometry is gone, video-denoised so sensor noise is gone, no
controlled clear baseline, no depth. Every epsilon-box derived from it was withdrawn.

There are two ways to get paired endpoints:

1. **Collect them deliberately.** Same route, RTK poses, fixed exposure, raw frames, clear
   baseline plus adverse repeats. That is the MCity winter campaign, owned by MS CS student 2
   under `dataset--winter-driving--*`.
2. **Reconstruct them.** Rebuild a real scene from camera and LiDAR logs, then render clear
   and adverse endpoints at the same pose. That is this repository.

The two are complementary, not competing. Collection gives ground truth on one route in one
season. Reconstruction generalizes it to any logged drive.

## Why it matters commercially

It is the answer to the second objection any industry person raises, after model size:

> You only did this in a simulator.

A certificate computed on a reconstructed real road is a different conversation from a
certificate computed in CARLA. It is also the natural NVIDIA grant ask.

## Why it is not the place to start

It depends on things that do not exist yet. Feed it, do not start it:

- the winter campaign supplies the ground truth a reconstruction must be checked against
- `formal-verification--verifier-scaling--code` decides whether a certificate on
  reconstructed imagery is affordable at all
- the behavioral-validity protocol (RESEARCH_DIRECTIONS.md, Q6) supplies the test a
  reconstruction has to pass, and it is a **behavioral** test, not an image-fidelity one

## The test a reconstruction must pass

Not PSNR, not SSIM, not R-squared. Our own measurement is the caution: an analytic fog model
reproduced CARLA fog at road-ROI R-squared 0.848 and drove one policy 23.8 times harder than
real fog, while staying faithful for another. It was most wrong about the better policy.

**A reconstruction is validated when the policy responds to it the way it responds to the
real frame**, at matched poses. Design that check before building anything.

[PROTOCOL.md](PROTOCOL.md) is that design. It defines the acceptance test whose reference
is a real frame, not a rendered one. It says how to measure the tolerance band from real repeats. It
puts the known-bad control first. It also says which experiment waits on which missing piece.

## Prior art and tooling

CARLA 0.9.16 targets NVIDIA NuRec, which neurally reconstructs real driving scenes from
camera and LiDAR into CARLA. Its inputs are exactly what a log-ingestion pipeline produces.
There is directly relevant experience in Zach's Isuzu CARLA scenario-testing work, which
ingests real camera and LiDAR rosbags.

- `lab--future-plans--docs/RESEARCH_DIRECTIONS.md`, entries Q7, Q6, A3 and R1
- `_references/autonomous_driving/nvidia_2026_omnidreams.pdf`

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
