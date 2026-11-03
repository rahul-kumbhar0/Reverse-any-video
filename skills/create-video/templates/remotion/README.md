# Remotion render template

Copied by the create-video skill into a work directory, next to the two data files it reads:

```
work/
├── package.json, remotion.config.ts, src/   (this template)
├── style-spec.json                           (from the style skill)
├── timeline.json                             (built per the create-video skill)
└── public/                                   (images/video assets referenced by timeline)
```

```bash
npm install
npx remotion render Main out/video.mp4
```

`src/Main.tsx` is intentionally generic — it renders whatever the spec + timeline say.
Style-specific devices (progress bars, cutouts, grids) get added as new components per
the style skill's layout description.
