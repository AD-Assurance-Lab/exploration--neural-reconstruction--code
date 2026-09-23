# report

`poc.tex` is a short note on the proof of concept. Build it with `latexmk -pdf poc.tex`.

The figures and videos are not in git. To make them, run the pipeline in `../scripts` in the
order `PROOF_OF_CONCEPT.md` gives, then run `python3 scripts/make_demo.py` from the repository
root. It writes the frames and plots into `figures/` and `demo.mp4` and `demo_fog.mp4` here.
