# Patterns that transfer between apps

These are decision aids, not bundled or tested app integrations.

| App class | Useful structured surface to discover | What the GUI must confirm |
| --- | --- | --- |
| CAD / 3D | Native Python/API, parametric model, exporter | Scale, topology, camera, material/render appearance |
| Vector / layout | SVG, scripting, native document API | Typography, clipping, alignment, page/export bounds |
| Raster editor | App scripting, layers, masks, native project | Edge quality, blend modes, color profile, transparency |
| Spreadsheet | Native formulas/API, workbook libraries | Recalculation, references, formatting, chart readability |
| Video / audio | Native scripting, timeline interchange, render CLI | Timing, transitions, synchronization, actual playback |
| Browser / Electron | Existing DOM/accessibility tools | Correct page, dialogs, canvas, final submitted state |
| Proprietary desktop app | Menus, shortcuts, OS accessibility when available | Focus, modal state, correct file and saved result |

For each app, discover the real installed capabilities. For example, a workbook library may
write formulas without calculating them; an interchange format may lose effects or layers;
an exported PDF may look right while the native document is broken. Test the round trip that
matters for the deliverable. Avoid replacing a native project with a lossy format silently.
