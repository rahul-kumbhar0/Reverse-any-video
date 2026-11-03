import React from "react";
import { Composition } from "remotion";
import { Main } from "./Main";
import timeline from "../timeline.json";
import spec from "../style-spec.json";

const fps = (timeline as any).fps ?? (spec as any).format?.fps ?? 30;
const width = (timeline as any).width ?? (spec as any).format?.width ?? 1080;
const height = (timeline as any).height ?? (spec as any).format?.height ?? 1920;
const totalSeconds = (timeline as any).shots.reduce(
  (acc: number, s: any) => Math.max(acc, s.start + s.duration),
  0
);

export const Root: React.FC = () => (
  <Composition
    id="Main"
    component={Main}
    durationInFrames={Math.ceil(totalSeconds * fps)}
    fps={fps}
    width={width}
    height={height}
    defaultProps={{ timeline, spec } as any}
  />
);
