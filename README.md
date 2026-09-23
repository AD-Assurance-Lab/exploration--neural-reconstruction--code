# exploration--neural-reconstruction--code

Tests whether a neural reconstruction of a real road can stand in for the real camera
frames: a driving policy must respond to a rebuilt frame the way it responds to the real
frame at the same pose.

- `PROTOCOL.md`: the acceptance test.
- `PROOF_OF_CONCEPT.md`: the commands in order and the run log.
- `TOOLING.md`: what the NVIDIA tools can and cannot do.
- `scripts/`: render frames, run the policy and compare responses.
- `src/neural_reconstruction/`: the code that measures the gap between two responses.
- `report/`: a short LaTeX note.

`data/` holds the scenes, models, frames and responses. Git ignores it.

Apache License 2.0. See `LICENSE` and `NOTICE`.
