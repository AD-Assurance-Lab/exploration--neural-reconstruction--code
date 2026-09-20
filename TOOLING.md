# TOOLING.md, what the NVIDIA stack gives this study

Written 2026-09-19. Sources: `_references/autonomous_driving/nvidia_2026_omnidreams.pdf`,
and the public pages listed at the end.

**Short answer: yes, in part.** Two blockers this repository called fatal are now smaller.
One tool can also repeat the lab's oldest mistake at higher resolution. Read section 4 before
anyone writes a weather prompt.

## 1. The three tools, in one line each

- **Neural reconstruction, `NuRec`.** It rebuilds a real scene from a real capture, as
  splats. It stays anchored to the capture. It degrades once the camera leaves the capture
  path.
- **`OmniDreams`.** A generative world model, trained on 21 thousand hours of driving. It
  generates video conditioned on an abstract scene map, a first frame, and a text prompt. The
  prompt sets weather, lighting and time of day, and it does not move the road geometry
  (report, section 9.3.1).
- **`Alpamayo`.** An open driving policy that reads real camera images. Version 1.5 holds 10
  billion parameters. Version 2 Super holds 34 billion. The weights are public.

## 2. What is public, and how large it is

| Asset | Size |
|---|---|
| Reconstructed scenes | Over 1,500 scenes, 20 seconds each, 6 camera views. |
| The source driving data | 1,700 hours, 306,152 clips, 7 cameras at 1080p and 30 frames a second, with lidar, radar, camera intrinsics, sensor extrinsics and ego poses. 133 TB. |
| The generative model | Code and weights, both public. |
| The policy | Weights, public, under the OpenMDW-1.1 license. |

Two limits to settle before anyone starts a download.

- **License.** The driving-data license permits use "solely for your internal development of
  autonomous vehicles and automated driving assisted systems using NVIDIA technology". Decide
  whether a published measurement sits inside that sentence. The quotation keeps its source
  spelling.
- **Hardware.** Real-time generation needs `GB300` class hardware. This lab has one
  `RTX 5090` with 32 GB. We do not need real time. A certificate needs frames at poses, which
  is an offline job. The 10 billion parameter policy fits in 32 GB at half precision, with
  little room to spare. The 34 billion parameter policy does not.

## 3. What this unblocks

The charter says we have no real paired data and no reconstruction. Both statements are now
partly out of date.

- **The reconstructions come from real captures, and those captures are public.** For a scene
  that appears in both sets, we hold a real frame and a rebuilt frame at nearly the same pose.
  That is the clear-frame step of the acceptance test, with no collection at all.
- **The open policy reads real photographs.** Our own students cannot. They learned on CARLA
  images and they only respond to CARLA images. A test on real frames needs a policy that
  drives on real frames, and that policy now exists with open weights.
- **Pose delivery is measurable today.** Ask the renderer for a recorded pose. Compare what it
  delivers against the recorded pose.

## 4. What it does not give, and the trap inside it

A text prompt turns one seed scene into a clear frame and a snowy frame, at one pose. That
looks like the pair the verified family needs. It is not, on its own.

Neither frame in that pair is a real snowy frame. The snow is a learned guess about snow. The
lab already measured what such a guess costs. An analytic fog model reproduced simulator fog
at road-ROI R-squared 0.848, which is a good image score. It then drove one policy 23.8 times
harder than real fog, and stayed faithful at 1.2 times for the other. A generative model with a better image score does not
remove that failure. It hides it better.

So a generated adverse endpoint stays unvalidated until real paired adverse frames exist. The
winter campaign is still the only source of those. Until then, use the prompts for negative
controls and for candidate boxes, and label every cell they touch.

## 5. The ranking trap, and the experiment it suggests

The report validates the generative simulator against the reconstruction in one main way. It
swaps the sensor backend under a fixed orchestrator, then checks that the ranking of four
policy classes holds across 501 scenes (report, figure 13). Ranking is a behavioral check, and
it is a coarse one.

Our fog measurement is a case where two instruments agreed on which policy was better, and
disagreed by 23.8 times on how hard the disturbance was. Ranking survived. Magnitude did not.
The same gap is measurable here with public assets alone. Drive one policy at one set of poses
through both sensor backends. Compare the per-pose response, not the rank.

## 6. Where verification fits

We cannot certify a 10 billion parameter policy, and nothing here suggests otherwise. The open
policy is the reference, not the certified network. The certified network stays small. Distill
a student on this imagery, certify the student, then check the student against the reference
policy. The cost curve for that comes from `formal-verification--verifier-scaling--code`.

## 7. The experiment list, revised

| Experiment | What it needs | Status |
|---|---|---|
| **Pose delivery.** Render a reconstructed scene at recorded poses and measure the error. | Public reconstructions and one GPU. | Ready. |
| **The null test.** Compare the open policy's response on a rebuilt clear frame against its response on the real frame at that pose. | Public reconstructions, the source clips, the open policy. | Ready. |
| **The band.** Measure real-to-real response spread at one pose. | Real repeats. Stationary segments give the same-pose part. Repeated passes over one road give the rest. | Partly ready. Search the public clips for both. The full band still wants the winter campaign. |
| **Ranking against magnitude.** One policy, one set of poses, two sensor backends, per-pose response. | Both backends and the open policy. | Ready. |
| **Adverse endpoints.** Certify against a generated snow or fog endpoint. | Real paired adverse frames to check it against. | Blocked on the winter campaign. |
| **Certificate comparison.** Certify on rebuilt endpoints, then compare the radius against the real pairs. | A distilled student and the four rows above. | Blocked. |

## 8. What to check first, in about half a day

1. Read the driving-data license with a publication in mind. This gates everything else.
2. Confirm that one named scene appears in both the reconstruction set and the source set, and
   that the poses line up.
3. Run the open policy on one real clip on this machine. Record memory use and time per frame.
4. Render one reconstructed scene at its recorded poses. Measure the pose error.

Nothing above asks for a download of 133 TB. Each check works on one scene.

## Sources

- [NVIDIA OmniDreams report](https://arxiv.org/abs/2606.03159), and the local copy in
  `_references/autonomous_driving/nvidia_2026_omnidreams.pdf`
- [The reconstructed scenes](https://huggingface.co/datasets/nvidia/PhysicalAI-Autonomous-Vehicles-NuRec)
- [The source driving data](https://huggingface.co/datasets/nvidia/PhysicalAI-Autonomous-Vehicles)
- [The open policy, version 1.5](https://huggingface.co/nvidia/Alpamayo-1.5-10B)
- [The open policy, version 2 Super](https://huggingface.co/nvidia/Alpamayo2-Super)
- [The renderer documentation](https://docs.nvidia.com/nurec/av/index.html)
