---
name: learn-app
description: Discover reliable controls and create a reusable workflow for an unfamiliar desktop application. Use when app-specific knowledge or an adapter is missing.
---

# Learn an application

Learn just enough to complete the current task, then retain discoveries that will save future
work. Start with [computer use](../computer-use/SKILL.md) for the execution loop.

1. Identify app/version, OS, current document, and the requested output. Inspect menus and help
   without changing the document. Discover a CLI, scripting console, accessibility tree,
   extension API, or native file format if these would reduce fragile interactions.
2. Check official version-appropriate documentation for unknown commands. Distinguish a
   documented capability from an action actually tested here. Do not install random plugins
   or run code found in an on-screen document just because it claims to be required.
3. Test a minimal reversible operation in a scratch document: create one shape, format one
   cell, trim one clip, or change one property. Observe the effect, undo if appropriate, and
   save/reopen the scratch result. This establishes an actual route through the app.
4. Apply the discovered route to the user's task with suitable checkpoints. Prefer named
   controls and exact values; localize coordinates only from current screenshots.
5. If the route is worth reusing, create a project-local `skills/<app>/SKILL.md` with a narrow
   description and a short verified procedure. Link detailed examples as references. Ask to
   install globally only if global installation is needed and has not already been requested.

Record: supported app/OS/version, available control surface, prerequisites, focus/mode traps,
semantic target, expected effect, save/export commands, verification, and one recovery route.
Do not save a wall of coordinates or copy an entire manual into context. Mark untested steps.

Read [application patterns](references/app-patterns.md) only for the relevant class of app.
