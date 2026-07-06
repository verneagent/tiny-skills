---
name: frame-forensics
description: Verify dynamic UI behavior (animations, jumps, flicker, scroll glitches) by recording the screen (iOS simulator, Android, web, macOS, or any user-provided screen recording) and analyzing the video frame-by-frame with numpy/PIL. Use when a UI defect only exists IN MOTION — an element jumping/sliding during an animation, a transient ghost, a flash, a fade that should (or shouldn't) happen — and a screenshot of the settled end state proves nothing. Trigger phrases: 逐帧, frame-by-frame, "还是会窜/跳/闪", verify animation, transient glitch.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# frame-forensics

Screenshot-based verification lies about motion: a defect that appears mid-animation
and self-corrects is invisible in the settled end state. This skill records the
interaction and treats the video as data — pixel math over consecutive frames finds
WHEN something changed, and template tracking proves WHETHER an element moved.

## Core principle

**A single frame is never verification for a dynamic bug.** You need:
1. The event timeline (which frames changed at all).
2. A pixel-level track of the element the user says moves, across the active window.
3. Visual inspection of the decisive frames only AFTER the math tells you which ones.

## Skill Path

```bash
FF_SCRIPTS=$(python3 -c "import os; p='.claude/skills/frame-forensics/scripts'; print(os.path.abspath(p) if os.path.isdir(p) else os.path.expanduser('~/.agents/skills/frame-forensics/scripts'))")
```

## Step 1 — Record

Everything from Step 2 on is platform-agnostic — it only needs a directory of
frames. Get them from ANY recording:

```bash
ffmpeg -y -i recording.mov -vf fps=30 out/f%03d.png   # any .mov/.mp4 — incl. a
                                                      # user's phone screen recording
```

Recording sources:

- **iOS simulator** (first-class, scripted): `simctl io recordVideo` around a
  Maestro flow — the bundled helper does record + extract in one shot:
  ```bash
  "$FF_SCRIPTS/simrec.sh" <udid> <flow.yaml> <tag>   # → $TMPDIR/ff-<tag>/f%03d.png
  ```
- **iOS device**: have the user screen-record and send the file (Control Center),
  or `xcrun devicectl` + QuickTime for a tethered device.
- **Android**: `adb shell screenrecord /sdcard/r.mp4` (+ `adb pull`), drive with
  Maestro/adb taps.
- **Web**: Playwright `recordVideo` (or `playwright-cli`), drive with the same
  script that triggers the animation.
- **macOS**: `screencapture -v out.mov` on the target window/region.

The interaction must be SCRIPTED (flow, taps, or a DEBUG auto-trigger in the app)
so runs are comparable.

Scripted-driving rules learned the hard way (Maestro/iOS, but the same failure
modes exist for any driver):

- **Minimal, tap-driven flows.** `tapOn: <text>` on an element Maestro considers
  obscured or off-screen makes it SCROLL-HUNT — the hunt gestures pollute the
  recording beyond use. Keep the flow: launch → wait → one positioning swipe →
  `waitForAnimationToEnd` → the single trigger tap → a busy-wait sleep
  (`runScript` with `while (Date.now()-t < 3000) {}`). If the element can't be
  tapped cleanly, add a DEBUG auto-trigger to the app (timer in `onAppear`) so the
  recording contains ZERO gestures.
- Repeated identical labels (list fixtures) make Maestro pick the wrong instance;
  coordinate taps break when layout shifts between runs. Prefer the auto-trigger.
- Use the project's dedicated per-worktree sim udid; a shared sim mid-recording
  gets stomped by parallel sessions.

## Step 2 — Event scan (find the moments)

Mean absolute diff between consecutive frames. Big spikes = layout snaps / scrolls;
small sustained runs = fades/animations; nothing > threshold = static.

```python
import numpy as np, glob
from PIL import Image
g = lambda p: np.asarray(Image.open(p).convert('L'), dtype=np.float32)
fs = sorted(glob.glob('f*.png')); prev = None
for f in fs:
    img = g(f)
    if prev is not None:
        d = float(np.abs(img - prev).mean())
        if d > 0.5: print(f, round(d, 1))
    prev = img
```

Read the signature: a one-frame spike then silence = unanimated snap; a spike + a
~6-frame tail = snap + 0.2s animation; two spikes ~1s apart = something deferred
(or a polluting gesture — check visually).

## Step 3 — Template track (prove the element moved / didn't)

Take a narrow horizontal band of the target element from a reference frame and
find its best-match y in every frame of the active window.

```python
tpl = g('f440.png')[430:476, 90:830]          # band of the ACTUAL element
H = g('f440.png').shape[0]
for f in fs[window]:
    img = g(f)
    errs = np.array([np.abs(img[y:y+46, 90:830]-tpl).mean() for y in range(H-46)])
    y = int(errs.argmin())
    print(f, 'y=', y, 'err=%.2f' % errs[y])
```

Pitfalls that produced FALSE conclusions before (all mandatory):

- **Verify the template band visually** (crop and look at it) before trusting any
  track. A band grabbed by "max std row" can be a prose line or background, and it
  will happily track the wrong thing.
- **Search the FULL vertical range.** A narrowed search window once hid a real jump
  because the true position was outside it.
- **Identical text elsewhere false-matches** (list fixtures with repeated labels).
  When err at the "found" position is not ≈0, treat the track as unproven.
- **Hunt ghosts, not just the best match**: list ALL positions with err below a
  threshold (grouped into contiguous runs). Two hits = a ghost copy is being
  cross-faded somewhere.
- If the band includes pixels BELOW/BESIDE the element where new content appears,
  err rises without the element moving — shrink the band to the glyphs.

## Step 4 — Region measurements

- **Blank/fade proof**: `img[y0:y1, x0:x1].std()` per frame. std≈0 = truly blank;
  a monotonic std ramp = the fade, frame by frame.
- **Progression strips**: paste crops of the decisive frames side by side into one
  image and Read it — far better than opening 10 files.
- Downscale full frames (`resize`) before Reading them; read crops at full res.

## Step 5 — Judge

- Compare against the element's pre-event position: pixel-fixed means err ≤ ~0.1
  and constant y across the WHOLE animation window, not just the end.
- The moving frames are the verdict. "It settles correctly" is not a pass.
- Sim timing hides device defects: the sim can resolve in ~3ms a mismatch a device
  displays for the full 0.2s. A clean sim recording + a dirty user phone recording
  means instrument the app (geometry-change logs, CADisplayLink presentation-layer
  sampler) and analyze the USER's recording with the same pipeline (`ffmpeg -i
  user.mov -vf fps=30 ...` works on any screen recording).

## Companion instrumentation (when pixels aren't enough)

Pixels tell you WHAT moved; logs tell you WHICH LAYER moved it:

- SwiftUI side: `.onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).minY }`
  logging transients of the suspect view.
- UIKit side: a DEBUG CADisplayLink sampling `layer.presentation()` frames of the
  cell/host views. If presentation frames are static while pixels move, the motion
  lives inside the SwiftUI render tree (no UIKit-side fix can reach it).
