---
description: Generate a new video in a reverse-engineered style
argument-hint: <style-name> "<content brief>" [duration]
---

Create a new video per $ARGUMENTS: the first token is the style name (a folder under
`skills/generated/`), the rest is the content brief.

Use the `create-video` skill from this plugin: load the style skill + style-spec.json,
write the script to the style's formula and show it for approval, build timeline.json to
the style's pacing numbers, render (Remotion preferred, FFmpeg assembler fallback),
verify against the style's fidelity checklist by looking at extracted frames, and deliver
the MP4 + script + timeline.

If no style name matches, list the available folders under `skills/generated/` and ask.
For long renders, delegate to the `video-director` agent.
