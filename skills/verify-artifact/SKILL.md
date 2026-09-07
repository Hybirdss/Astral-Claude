---
name: verify-artifact
description: Verify saved creative or desktop-app deliverables against the user's request using structural checks and visual inspection. Use before handing off renders, documents, models, or exports.
---

# Verify an artifact

Build acceptance checks from the user's actual brief. Spend verification effort where failures
would invalidate the result; a routine small edit does not need a new test framework.

- **Identity:** Resolve the exact output path. Check format, nonzero size, and that it belongs
  to this run. A similarly named old render is not evidence.
- **Structure:** Open or parse the native file. Check requested dimensions, units, pages,
  layers, frames, formulas, camera, or objects. Verify exports did not drop essential content.
- **Appearance:** Open the exported image/document in an available image or app viewer.
  Compare framing, alignment, legibility, clipping, and requested visual details. For motion
  or audio, inspect enough of the timeline/playback to support the claim.
- **Round trip:** Reopen the saved native document when practical. Check dependency paths,
  missing assets, and editability. Do not overwrite the working document just to validate.
- **Handoff:** Give the native source path, requested exports, what was actually inspected,
  and any unmet criterion. Never describe an unviewed image as visually verified.

If checks fail, return to the working skill and repair the largest relevant defect. Once the
acceptance conditions pass, deliver; do not keep making unrequested aesthetic changes.
