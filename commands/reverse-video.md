---
description: Reverse-engineer a reference video into a reusable style skill
argument-hint: <video-path-or-url> [style-name]
---

Reverse-engineer the video given in $ARGUMENTS into a reusable style skill.

Use the `reverse-video` skill from this plugin and follow its pipeline completely:
probe → cut detection → frame extraction → audio analysis → transcript → vision pass →
generate `skills/generated/<style-name>/` (SKILL.md + style-spec.json + assets).

If the argument is a URL, download it with yt-dlp if available; otherwise ask for a local
file. If no style name was given, derive a descriptive kebab-case one. For long sessions
or when the user asks for it to run in the background, delegate to the
`video-reverse-engineer` agent instead of running inline.
