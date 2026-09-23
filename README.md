# exploration--neural-reconstruction--code

This repository tests whether a neural reconstruction of a real road can stand in for the
real camera frames. The test is behavioral: a driving policy must respond to a rebuilt frame
the way it responds to the real frame at the same pose.

A first proof of concept runs on one public NVIDIA clip. On that clip, the rebuilt frames
move the policy about as much as a heavy fog does.

- `PROTOCOL.md` defines the acceptance test.
- `PROOF_OF_CONCEPT.md` has the plan, the commands in order and the run log.
- `TOOLING.md` says what the NVIDIA tools can and cannot do on this machine.
- `scripts/` renders frames, runs the policy and compares its responses.
- `src/neural_reconstruction/` holds the code that measures the gap between two responses.
- `report/` holds a short LaTeX note on the proof of concept.

`data/` holds the scenes, models, frames and responses, about 41 GB, and git ignores it.

Apache License 2.0. See `LICENSE` and `NOTICE`.
