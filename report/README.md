# report

`poc.tex` is a short note on the proof of concept. Build it with `latexmk -pdf poc.tex`.

The figures and the two videos are not in git. They come from NVIDIA's driving data, and
its license allows use for internal development of automated driving with NVIDIA
technology. This repository is public, so keep the images out until someone reads that
clause with a public repository in mind.

To make them again, run the pipeline in `../scripts` in the order that
`PROOF_OF_CONCEPT.md` gives. Then run this from the repository root:

    python3 scripts/make_demo.py

It writes the three frames and the two plots into `figures/`, and `demo.mp4` and
`demo_fog.mp4` into this folder.
