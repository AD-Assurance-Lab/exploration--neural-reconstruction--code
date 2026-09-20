# report

`poc.tex` is the one-page note on the proof of concept, with the method and the
limits on its second page. Build it with `latexmk -pdf poc.tex`.

## The images are not in git, on purpose

The figures and the two videos come from NVIDIA's driving data, and that license
permits use for internal development of automated driving with NVIDIA
technology. This repository is public, so the pixels stay out until we have read
that clause with a public repository in mind. The numbers, the method and the
scripts are here, and they are what a reader needs to check the work.

Nobody should add the images back without that reading.

## Making them again

Accept the dataset terms on Hugging Face, fetch one scene with its forward video,
then run the pipeline in `../scripts`. `PROOF_OF_CONCEPT.md` lists the commands
in order. One command rebuilds every figure and both videos from the saved
policy responses:

```
python3 scripts/make_demo.py
```

That writes `figures/frame_clear.png`, `figures/frame_rebuilt.png`,
`figures/frame_fog.png`, the two plots, `demo.mp4` and `demo_fog.mp4`.
