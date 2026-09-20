# PROOF_OF_CONCEPT.md, a first run with the NVIDIA tools

Written 2026-09-19. It answers one question: what can these tools actually do on this
machine, and which part of our own study does each step serve?

The plan is deliberately small. Nothing here certifies anything, and nothing here needs the
winter campaign. Each stage produces something you can look at, and each one ends with a
number we keep.

## What we already have, and it is more than expected

The checks behind this plan are all done, so the plan rests on facts rather than hope.

| Thing | State on this machine |
|---|---|
| Sample scenes, one real clip in clear, rain and snow | Public, no license click, 2.4 GB each. |
| The open driving policy, 10 billion parameters | Public, no license click, 22.2 GB. |
| The renderer | Our own CARLA 0.9.16 already carries the reconstruction engine (NuRec 25.07). |
| The graphics card | One `RTX 5090`, 32 GB, driver 595.84. The renderer asks for 24 GB, so it fits. |
| A working deep-learning environment | Torch 2.13 with CUDA 13, in the steering and scaling repositories. |
| Disk | 1.4 TB free. |

Two things we cannot run here, and it is better to say so now.

- The generative world model wants a card with 80 GB or more, so it will not generate video
  on this machine. We do not need it to. The sample scenes already carry the weather variants
  we want to look at, and an offload patch for smaller cards is in review upstream.
- The large public driving datasets need a license click by a signed-in account, so they are
  not part of the first two stages.

## Stage 1. Show a real scene, in three weathers, at one camera path

**Download:** about 7.1 GB, three scene files of one real clip.

**Do this.** Load each scene in CARLA, drive one fixed camera path through all three, and
save the frames. Keep the determinism rules the lab already uses, since this is the same
simulator.

**What it shows.** A real street, rebuilt from a real capture, rendered clear and then wet and
then snowy, with the camera in the same place each time. That image strip is the whole
argument of this repository. No published adverse-weather dataset can give you the same
picture.

**What we record.** The pose we asked for, the pose the renderer delivered, the time per
frame, and the memory used. Pose error is a protocol measurement in its own right, so this
stage quietly completes one row of the schedule.

**What could go wrong.** The scenes come from the 2026 release and our simulator carries the
2025 reconstruction engine, so the file may not load. If that happens, the container from the
NVIDIA registry is the fallback, and the finding itself is worth writing down.

## Stage 2. Ask a real driving policy what it sees

**Download:** 22.2 GB, the open policy.

**Do this.** Run the policy over the frames from the first stage, one weather at a time, and
record its output at every pose. Then take the difference between the clear response and the snowy
response, pose by pose.

**What it shows.** We can measure how a real-world policy reacts to a disturbance on real
scene geometry, at a fixed pose. That measurement sits at the center of our acceptance test.
It also gives the lab its first response numbers on real imagery rather than simulator
imagery.

**The label this number carries.** The snow in those scenes is a model's idea of snow, and
nobody has checked it against real snow at that place. So the number is a demonstration of the
instrument, not evidence about snow. Write `unvalidated` next to it and mean it.

## Stage 3. Turn that measurement into the instrument the protocol asks for

No download. Small code.

Wrap the second stage in something reusable: two image sets, one policy, matched poses in,
and a per-pose response gap out, per policy. That is the measuring device the acceptance test needs,
and every later stage uses it. Keep the known-bad control beside it from the first day, so the
instrument has rejected something before we ever trust it.

## Stage 4. The honest scientific step, once we settle the license

**Needs:** one license click on a signed-in account, then a few scenes.

The public reconstruction set comes from real captures, and those captures are public too.
So for one scene we can hold the real frame and the rebuilt frame at one pose, and ask the
policy about both. That is the clear-frame step of our acceptance test, on real data, with no
collection at all.

Read the license first, because it permits use for internal development, and we publish.

## What this proves, and what it does not

Once the instrument exists, at the end of the third stage, we can say this. We can produce
pose-paired endpoints on real scene geometry, and we can measure what they do to a real
driving policy. That is the capability this repository was waiting for.

We still cannot say that a generated snowy frame resembles real snow at that place. Only the
winter campaign settles that, and the protocol keeps the rule.

## Order and cost

| Stage | Download | Work | Gives |
|---|---|---|---|
| 1, render the scene | 7.1 GB | An afternoon, if the scene loads. | Frames, and pose error. |
| 2, ask the policy | 22.2 GB | An afternoon. | The first response gap on real imagery. |
| 3, build the instrument | none | A day. | The instrument, with its control. |
| 4, the real comparison | a license click | Two days. | The first result worth publishing. |

---

# Run log

## 2026-09-19, the first sitting

**Downloads started.** The three scene files and the 22.2 GB policy are coming down into
`data/`, which git ignores. Neither one asked for a token or a license click.

**The code is written and it parses.** Four pieces, and the instrument has a passing smoke
test on synthetic paths.

| File | What it does |
|---|---|
| `src/neural_reconstruction/response.py` | The instrument. Two predicted paths in, one gap in meters out, with the policy's own sampling spread beside it. |
| `scripts/render_paired_frames.py` | Replays one recorded track through several scenes and saves frames and poses. |
| `scripts/run_policy.py` | Runs the open policy over those frames and saves the predicted paths. |
| `scripts/make_known_bad.py` | Paints the known-bad fog on a frame set, for the control. |
| `scripts/response_gap.py` | Compares two response files and prints the verdict numbers. |

**One thing you have to run yourself.** The renderer runs inside a container, and this machine
has no container runtime. Installing one needs your password, which I cannot give. Either run
the vendor script, which also installs the graphics toolkit and pulls the image:

```
! bash /home/za/carla/PythonAPI/examples/nvidia/nurec/install_nurec.sh
```

or do the same three things by hand:

```
! sudo apt-get install -y docker.io
! sudo apt-get install -y nvidia-container-toolkit
! sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
! docker pull docker.io/carlasimulator/nvidia-nurec-grpc:0.2.0
```

The vendor script asks for a Hugging Face token so it can fetch the public scene collection.
We already hold the sample scenes, so you can skip that part.

## What the first numbers will look like

Two findings are already visible from the model card, and both change the study design.

**The response is a path, not a steering angle.** The policy predicts 6.4 seconds of
trajectory at 10 Hz, with text reasoning beside it. So the open-loop statistic in the protocol
needs a second form: distance between two predicted paths, in meters, at a stated horizon.
The instrument reports it at 1, 3 and 6 seconds.

**The policy samples, so it disagrees with itself.** The trajectory decoder is a diffusion
model, and the same frame gives a slightly different path each time. That spread is a floor
under every gap we measure, and it limits how finely we can judge any reconstruction. The instrument
measures the spread at every pose and refuses to call a gap real until it clears the floor.
This is the band from section 3 of the protocol, arriving from an unexpected direction, and it
costs nothing to measure.

## 2026-09-19, later. Everything is in place except two clicks

**Done and verified on this machine.**

- The three scene files are on disk, 6.6 GB in `data/scenes`.
- The policy weights are on disk, 21 GB in `data/models`.
- The policy environment installs and runs. Torch 2.8 with CUDA 12.8 drives the `RTX 5090`,
  which reports compute capability 12.0, and a half-precision matrix product runs on it.
  We skip flash attention, so the model falls back to the built-in attention path.
- The container runtime now installs and runs, thanks to your vendor-script run.

**Two things still block the first frame, and both are gates rather than bugs.**

*The graphics toolkit for containers.* The vendor script fetches a package list from an
address NVIDIA retired, so it stops with a 404. The current address works. These four
commands replace the part that failed:

```
! curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
! curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
! sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit && sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
! docker pull docker.io/carlasimulator/nvidia-nurec-grpc:0.2.0
```

*The policy's text front end.* The weights are open, but the tokenizer and image processor
come from the model they were built on, and that one is gated. Loading stops with a plain
message: "Access to model nvidia/Cosmos-Reason2-8B is restricted and you are not in the
authorized list." Accept the terms once while
signed in, then hand the token to this machine:

```
! hf auth login
```

Nothing else in our pipeline touches a gated resource. Our own loader reads the rendered
frames, so the large driving dataset stays out of the first run.

**What runs the moment those two clear.**

```
python3 -m carla_determinism launch --port 2000
python3 scripts/render_paired_frames.py --usdz data/scenes/*.usdz --seconds 8
python3 scripts/run_policy.py --frames data/frames/<scene>.npz --samples 8
python3 scripts/response_gap.py --a data/responses/<clear>.npz --b data/responses/<snow>.npz
```

## 2026-09-19, the instrument runs

The policy loads and answers on this machine. These numbers come from the lab's own simulator
frames, so they say nothing about fog and nothing about the policy. They show that the
plumbing works and that the instrument can tell an image effect from noise.

| Measurement | Value |
|---|---|
| Time per pose, one trajectory | 1.2 seconds |
| Peak graphics memory | 23.3 GB of the 32 GB card |
| Weight loading | Seconds, from the local copy |
| Text front end | The built-in attention path, no flash attention |

**The first finding, and it changes how we measure.** The policy samples its reasoning text
and its trajectory, so it disagrees with itself. With sampling on, four samples a pose, the
spread between samples was 0.84 m over a three-second horizon. The known-bad fog moved the
mean path by 0.50 m. The disturbance sat *below* the noise, so the instrument reported
nothing, which is the correct answer to a badly designed measurement.

Turn the sampling off and fix the seed, and the picture changes:

| Comparison | Mean gap | Peak gap | Poses above the floor |
|---|---|---|---|
| The same frames twice | 0.000 m | 0.000 m | 0 of 7 |
| Clear against the known-bad fog | 0.091 m | 0.181 m | 7 of 7 |

A repeat run reproduces the first run exactly, so the floor is zero and every meter of gap
belongs to the image. That is the configuration a gap measurement needs.

**Both numbers stay in the record.** The repeatable configuration says what the image did.
The sampled configuration says what the deployed policy does on its own. Its 0.84 m of
self-disagreement is a fact about the policy, and any certificate has to carry it.

**Still blocked:** the render step. The graphics toolkit for containers did not install, so
`nvidia-ctk` is still missing and the container cannot see the card. The render image itself
is here, 12.4 GB, pulled and ready.

## 2026-09-19, the render step, and the version wall

The container runtime now sees the card. Inside the render container, the card reports
itself correctly, so the graphics path works end to end.

The render still fails, and the reason is the one this plan listed as the risk. Our simulator
ships the 2025 reconstruction engine, and the sample scenes come from the 2026 release. The
engine loads the scene, then stops:

> Failed to create backend: Unknown calib name='free-pose-calib'.

The scene file is sound. It holds 100 seconds of a real drive, six cameras at 2,994 frames
each, lidar, and the recorded rig trajectory. The renderer in our simulator simply predates
the calibration format it uses.

**Three ways past it, and they differ in what they buy.**

1. **Use a scene from the public reconstruction collection.** The simulator integration targets that
   collection, so the versions match. It needs one license
   acceptance on Hugging Face, and one scene is about 2 GB. We lose the weather variants,
   because those scenes are clear only. We gain the better experiment: the rebuilt frame
   against the real recorded frame at one pose.
2. **Get the newer engine from the NVIDIA registry.** It would render the weather triple we
   already hold. Pulling it needs an account and a key on that registry, because the registry turns away an
   anonymous pull.
3. **Wait for a newer simulator release** that carries a newer engine. No date, no work.

The first is the shortest path to a number that means something. The second is the only path
that keeps the snow.

## 2026-09-19, the first numbers on a real road

The render step stayed blocked, so we went around it. Each scene in the public collection
ships with the real front-wide video beside the reconstruction, and the scene file carries the
recorded rig trajectory. That is a real drive with known poses, and it needs no renderer.

The clip is a night drive on a multi-lane road, 20 seconds, six cameras, recorded at 3840 by
2160 and 30 frames a second. We used the first 8 seconds of the forward camera at 10 Hz, 1,920 by 1,080, with the
recorded poses. The rig moved 148 m, so the drive sits near 18 m/s.

**The policy behaves like itself on this data.** It reports "Keep lane since the lane is clear
ahead" and predicts 19.6 m of travel in one second, 57.4 m in three and 110.8 m in six. That
matches the recorded speed, which is the first sign that the inputs reach it correctly.

**The instrument caught a bug in our own input.** The first run predicted a path running
backwards. The scene file stores the rig pose in the world, and we had inverted it, which
mirrors the ego history. The policy followed the mirrored history faithfully. A sign error in
a pose convention is exactly the defect that a fidelity score would never reveal.

### What a known-bad fog does to a real policy

Repeatable configuration, greedy text, one fixed seed. The table below covers seven poses.
The report in `report/poc.pdf` repeats the run at all 65 poses of the clip.

| Horizon | Mean gap | Peak gap | Poses above the floor |
|---|---|---|---|
| 1 second | 0.05 m | 0.09 m | 7 of 7 |
| 3 seconds | 0.29 m | 0.51 m | 7 of 7 |
| 6 seconds | 1.15 m | 2.25 m | 7 of 7 |

The same frames run twice reproduce exactly, so the floor is 0.00 m and every meter above
belongs to the fog.

### What the policy does to itself

Sampled configuration, four samples a pose, the way the policy would actually drive.

| Horizon | Mean self-disagreement | Worst pose |
|---|---|---|
| 1 second | 0.23 m | 0.41 m |
| 3 seconds | 1.67 m | 3.07 m |
| 6 seconds | 4.37 m | 6.80 m |

**Read those two tables together.** The policy disagrees with itself by four to six times more
than heavy fog moves it. A disturbance of this size is invisible in deployment unless you hold
the sampling still. Our certificates describe one deterministic function, so a certificate
about this policy has to cover the sampling distribution, or say plainly that it does not.

### What these numbers are not

One clip, one camera of the four the policy expects, seven poses, eight seconds of a clear
night drive. The fog is our known-bad control with an image row standing in for depth, not a
measured disturbance. Four samples give a coarse estimate of the spread. Nothing here is a
result about fog, and nothing here is a certificate. It is the instrument working, on real
frames, with numbers we can now argue about.

## 2026-09-20, the report, the video, and the way past the version wall

The one-page note is `report/poc.pdf`. It carries the method and the result, and its second
page holds the limits, the defect we caught, and the commands.

The video is `report/demo.mp4`. It runs the whole clip at 10 frames a second. Each frame shows the
real image, the same image under the known-bad fog, and the two planned paths below them.

Both come from `scripts/make_demo.py`, which reads the saved responses.

The dense run covers all 65 poses of the clip, rather than the seven in the table above. The
numbers hold: 0.05 m at one second, 0.33 m at three, and 1.20 m at six, against a sampled
spread of 0.23 m, 1.67 m and 4.37 m.

### Getting the newer render engine

The engine our simulator ships is from 2025, and both released scene sets are from 2026. The
newer engine sits in the NVIDIA registry as `nvidia/nre/nre-ga`, tag `26.04.01`, 13.31 GB. It
serves the same kind of gRPC interface that our client already speaks.

That container asks for a card with at least 24 GB, and for driver 580 or newer on this
architecture. It also asks for CUDA 12.8 or newer, Docker 23 or newer, and the container
toolkit 1.13.5 or newer. This machine has 32 GB, driver 595.84, Docker 29.8 and toolkit 1.20.

Four steps, and only the first two need you.

1. Sign in at `ngc.nvidia.com`. A free personal account is enough.
2. Generate a personal API key, with the catalog service included in its scope.
3. Log the machine in, pasting the key as the password:

```
docker login nvcr.io -u '$oauthtoken'
```

4. Pull the image and point the render script at it:

```
docker pull nvcr.io/nvidia/nre/nre-ga:26.04.01
export NUREC_IMAGE=nvcr.io/nvidia/nre/nre-ga:26.04.01
```

One risk sits in step 4. The newer service may have changed its interface, and our client code
carries the 2025 message definitions. If it refuses to talk, we regenerate those definitions
from the container's own files, which is a small job rather than a new project.

## 2026-09-20, the wall comes down, and the first acceptance measurement

The 2026 engine pulled from the NVIDIA registry, and it renders on this card without a
simulator in the loop. Its `render` command walks the recorded trajectory and writes one image
per recorded camera frame. Rendered frame number N therefore sits at the pose of recorded
frame N, which is the pose pairing the whole study needs.

We rendered the forward camera of the public clip at its native 1920 by 1080. We then ran the
policy over the rebuilt frames and over the real ones, at the same 65 poses, in the repeatable
configuration.

### The clear-frame step, on real data

| Horizon | Rebuilt against real, mean | worst pose | The known-bad fog, mean | worst pose |
|---|---|---|---|---|
| 1 second | 0.04 m | 0.25 m | 0.05 m | 0.34 m |
| 3 seconds | 0.25 m | 1.29 m | 0.33 m | 1.52 m |
| 6 seconds | 0.80 m | 4.20 m | 1.20 m | 3.20 m |

**Read the two halves against each other.** The reconstruction moves the policy about as much
as heavy fog does. At six seconds its worst pose moves the policy further than the fog's worst
pose. A certificate over a fog-sized disturbance, computed on this rebuild, would rest on a
substrate whose own error is the size of the disturbance.

That is what the clear-frame step exists to find, and it found it on the first clip we tried.
The finding is a measurement rather than a verdict: one clip, one camera, one policy, and an
engine with settings we have not explored.

### The weather scenes are prompts, not reconstructions

The three sample scenes render identically, to the byte. We compared their archives, and they
share one reconstruction checkpoint. They differ in three entries: the first image, one camera
frame, and a metadata line that names the scene `clipgt-snow_...` rather than `clipgt-...`.

So the snow and the rain live in a seed image for the generative world model, not in the
splats. The reconstruction engine renders the scene it reconstructed, which is the clear one.
Those variants become usable when we can run the generative model, and that wants a card with
80 GB. Nobody should treat those three files as three reconstructions.
