# PROTOCOL.md, the acceptance test for a reconstruction

**This file wins.** When a result and this file disagree about the study design, this file
is right.

Frozen 2026-09-18. Not locked. No code exists here. No capture and no reconstruction exist
either. Amendments go in section 12, each with a date and a reason.

The charter gives one rule: validate a reconstruction behaviorally, never on image fidelity.
The lab loses a rule that has no procedure behind it. This file is the procedure. It comes
before any building, as the charter asks.

---

## 0. The claim

> At matched camera poses on a real road, a policy responds to a reconstructed frame the way
> it responds to the real frame. Where it does not, we report how large the gap is and at
> which pose it opens.

The deliverable is the measured gap, per policy, with the failures kept in. "The
reconstruction looks right" is not a result here.

## 1. What a reconstruction must deliver

| | |
|---|---|
| **Endpoints** | `x_clear` and `x_cond` at one identical camera pose. |
| **Space** | Full sensor resolution, before crop and downsample. Never the network input. |
| **Exposure** | Fixed and recorded. Auto exposure is off, always. |
| **Pose** | Six degrees of freedom, with the pose error stated for each frame (section 6). |
| **Reference** | A real frame of the same scene at the same pose. |
| **Policies** | A policy that reads the frame under test. See the first amendment: the parent study's students read simulator images only. |

The check cannot run on a reconstruction that gives a picture but no pose record. Such a
reconstruction fails at intake.

## 2. The reconstruction check

The multi-condition study checks a disturbance model before it certifies any axis against
that model (`formal-verification--multi-condition--code/PROTOCOL.md`, section 4, re-scoped by
its fidelity-gate amendment, A2). That file names three kinds of disturbance source:
simulator-rendered, photographed and modeled. Reconstruction is a fourth kind. Its reference
is not a rendered frame. It is a real frame, and that is the whole reason this repository can
answer the simulator objection.

| Source of the disturbance | What the check compares against | The check |
|---|---|---|
| The simulator renders it | nothing, the simulator is the endpoint | none |
| A photograph supplies it | nothing, plus a magnitude label | none |
| We model it | the physical law the model claims | the physical-law check |
| We model it, and the simulator also renders it | the rendered frame | the behavioral check |
| **We reconstruct it** | **the real frame at the same pose** | **the reconstruction check** |

**The reconstruction check runs in three steps. Keep this order.**

- **Step 1, the band.** Measure how much the policy response moves between two real frames of
  the same scene at the same pose. This is the noise floor of the test. Until it exists,
  "responds the same way" has no number behind it. Section 3 says how to measure it.
- **Step 2, the clear frame.** Reconstruct the clear frame only. Compare the policy response
  on the reconstructed clear frame with the response on the real clear frame at that pose. Do
  not put a disturbance on a reconstruction that fails this step.
- **Step 3, the adverse frame.** Compare the policy response on the reconstructed adverse
  frame with the response on the real adverse frame at that pose.

A step passes when the response gap stays inside the band for **every** policy, not on
average. The lab's fog measurement is why: the analytic model stayed faithful at 1.2 times
for one policy and drove the other 23.8 times harder. An average of the two would have
reported a pass.

A failed step is a result, not a blocker. Record which step failed and for which policy.

## 3. Measure the band, do not declare it

Do not pick a tolerance factor because it looks reasonable. Measure the spread the real world
already has, then hold the reconstruction to it.

Two sources of real spread, measured apart:

1. **Repeat spread.** Drive the route again in the same condition. Take the frame pairs that
   share a pose. Measure how much the policy response moves between them.
2. **Same-pose nuisance.** Two raw frames at one pose still differ by shot noise and by small
   exposure drift. Capture repeated frames from a standing vehicle and measure the same way.

Rules that follow from the measurement:

- The tolerance factor may never be looser than the measured band.
- Measure the band for each policy. Two policies do not share one noise floor.
- If the band is wider than the effect the study wants to certify, this route cannot support
  the test. Record that and say so. It is a finding about the method, not a setback.

Write the band and the tolerance factor into the record before the first verdict.

## 4. The statistic

Declare the statistic for each experiment before the run. Choosing it after seeing the
numbers is a curve fit.

- **Open loop, frame against frame:** the difference in the commanded steering angle at the
  matched pose.
- **Closed loop:** the lab's statistic rule applies unchanged. A sustained failure takes the
  lap-wide mean. A localized, event-shaped failure takes the peak. Getting this wrong fails
  in both directions, which the parent studies already show.

## 5. The known-bad control

Mandatory, per the lab rule. Run it before you believe any verdict from this check.

The control is the analytic Koschmieder fog model. Its record is the reason this repository
has a behavioral rule at all. The model scored road-ROI R-squared 0.848 against CARLA fog,
which is a good image score. It then drove `S_mixed` 23.8 times harder than real fog, and
stayed at 1.2 times for `S_clear`. It was most wrong about the better policy.

Paint that model on a reconstructed clear frame and put the result through the check. **The
check must reject it.** If the check passes the known bad, the check has a defect. No other
verdict from it counts until you find that defect.

## 6. Pose is part of the test, not an assumption

"Matched pose" is the premise under every step above, so measure it.

- Record the requested pose and the delivered pose for every rendered frame. Report the
  error.
- Measure how much the policy response moves across a pose error of that size, on real frames
  alone. Call it the pose share of the band.
- If the pose share fills the band, the check has no room left to see a reconstruction error.
  Tighten the pose before going on.

RTK poses give the real pose on the collected route. The renderer reports the delivered pose.
Do not infer one of these numbers from the other.

## 7. What may never be an acceptance criterion

PSNR, SSIM, LPIPS and R-squared. Report them if they help a reader picture the scene. They
never decide the check. A cell that passes on image scores alone is not a pass, and the
record refuses it.

The lab measured the reason. A good image score sat beside a behavioral error of 23.8 times.
The error was largest for the better policy.

## 8. Blind protocol and repetitions

Lab-wide, and not optional here:

- Declare the split before capture.
- **Commit verification verdicts to git before the matching closed-loop run.** That is what
  makes a verdict a prediction instead of a description.
- Check the order mechanically. Do not rely on memory.
- Write the pre-registered prediction for each experiment before its first capture.
- Every closed-loop number is a rate over three repetitions. The rule changed from ten to
  three. The multi-condition protocol still says ten because it predates the change.
- If two repetitions of one cell disagree, find the defect. Do not drive more laps.

## 9. Labeling

Every certified cell computed on reconstructed imagery carries `reconstructed: true` and the
step of the check it passed. Cells on reconstructed imagery are never pooled with cells on
real captures or with cells on rendered captures. Each reported number says which source made
it.

## 10. The experiments, and what each one waits for

| Experiment | Steps it serves | Status on 2026-09-18 |
|---|---|---|
| **Measure the band** on real frames only. No reconstruction. | step 1 | Partly ready. A stationary segment in the public clips gives the same-pose part. The repeat part still needs the MCity winter campaign. |
| **Build the known-bad control** and confirm the check rejects it. | steps 1 and 2 | Ready once the check code exists. It can run on CARLA pairs, where matched poses are free. |
| **Measure pose delivery.** Does the renderer put the camera where you asked? | section 6 | Ready. Public reconstructions supply the scene and the recorded poses. |
| **Run the clear-frame step on public data.** Compare a policy's response on a rebuilt clear frame against its response on the real frame at that pose. | step 2 | Ready. The reconstructions, their source clips and an open real-world policy are all public. |
| **Compare certificates.** Certify on reconstructed endpoints, then compare the radius with the one from the real collected pairs, same route and same policy. | steps 2 and 3 | Blocked on the rows above, and on a distilled student. |

Build the known-bad control before the band data arrives. A check that has never rejected
anything is not evidence.

### What the schedule depends on

- `dataset--winter-driving--*` does not exist in the workspace on 2026-09-18. It supplies the
  real paired ground truth for the band and for the certificate comparison.
- `formal-verification--verifier-scaling--code` measured its first two phases on 2026-09-12.
  It decides whether a certificate on reconstructed imagery is affordable.
- `TOOLING.md` says what the public NVIDIA assets supply, and what they cannot supply.
- The behavioral-validity protocol (`RESEARCH_DIRECTIONS.md`, Q6) is not in this workspace.
  When it arrives, reconcile it with this file and record the difference as an amendment.

## 11. What would falsify this study

- **The band swallows the test.** If real-to-real spread is as large as the reconstruction
  error we want to detect, behavioral validation needs another route, another statistic or
  another sensor setup.
- **The clear frame passes and the adverse frame fails for every policy.** Then reconstruction
  reproduces the geometry but not the disturbance, and the paired-endpoint claim fails on its
  own terms.
- **The check passes the known-bad control.** Then the check is wrong, and we withdraw every
  verdict it gave.

Each of these is publishable. None of them is a reason to loosen the check.

## 12. Amendments

### 1. The policy row was wrong, and public assets moved three rows of the schedule

**Date: 2026-09-19. This file had no capture behind it, and no recorded verdict.**

**The defect.** Section 1 named the parent study's two students as the policies under test.
Those students learned on simulator images and they respond to simulator images. A frame from
a real road means nothing to them. So the test as frozen could not run on the data it was
written for. The defect turned up while reading the NVIDIA tooling, which is the
right place for it.

**The change.** The policy row now asks for a policy that reads the frame under test. For a
real frame that means an open real-world policy, such as the one named in `TOOLING.md`. For a
simulator frame the parent students still apply. Record which policy produced each number.

**What else moved.** Three rows of the schedule in section 10 changed status. The
reconstructions, their source captures and an open real-world policy are all public now. Pose
delivery is ready. The clear-frame step is ready. The band is partly ready, because a
stationary segment gives two real frames at one pose.

**What did not move.** No public asset supplies a real adverse frame paired with a real clear
frame at one pose. A generated snow or fog endpoint is a guess about snow or fog, whatever its
image score. The rule in section 7 stands. The winter campaign is still the only source of a
validated adverse endpoint, and `TOOLING.md` section 4 says why in full.

**Cost.** One more field per cell: the policy that produced the response.

### 2. The policy runs twice, in two configurations, and we keep both numbers

**Date: 2026-09-19. Measured on simulator frames, before any real capture.**

**What we found.** The open policy samples its reasoning text and its trajectory, so it
disagrees with itself on one identical frame. Four samples a pose sat 0.84 m apart over a
three-second horizon. A deliberately heavy fog moved the mean path by only 0.50 m. The
disturbance hid under the policy's own noise.

**The change.** Every gap measurement runs the policy in a repeatable configuration: greedy
text, one trajectory, one fixed seed. A repeat run then reproduces the first exactly, the
floor is zero, and the gap belongs to the image. Declare the configuration with the
statistic, before the run, as section 4 already requires.

**The second number.** A repeatable run says nothing about the policy people would deploy,
which samples every time. So each cell also carries the sampled spread at the same poses. A
certificate that ignores it is a certificate about a policy nobody drives.

**Cost.** Two runs of the policy for each image set instead of one. On this machine that is
about a second a pose, so the cost is small.

Format for each one: a numbered heading, the date, what the defect was, what changed, and
what the change costs. An amendment is cheap. An undocumented drift is what costs a year.
