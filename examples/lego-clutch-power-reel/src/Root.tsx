import React from "react";
import { Composition } from "remotion";
import { Main, TOTAL_SECONDS } from "./Main";

export const Root: React.FC = () => (
  <Composition
    id="Main"
    component={Main}
    durationInFrames={Math.ceil(TOTAL_SECONDS * 30)}
    fps={30}
    width={1080}
    height={1920}
  />
);
