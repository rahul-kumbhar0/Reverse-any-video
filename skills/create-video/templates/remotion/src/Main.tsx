import React from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";

/**
 * Generic style-driven renderer.
 * Props: { timeline, spec } — see create-video SKILL.md for both schemas.
 * Implements: solid/card shots, image shots with Ken Burns, video shots,
 * headline/caption/chapter text with pop-in, safe margins, palette.
 */

type Shot = {
  start: number;
  duration: number;
  visual?: {
    type?: "card" | "image" | "video" | "solid" | "cutout";
    src?: string | null;
    bg?: string;
    kenburns?: { zoom?: number; pan?: "up" | "down" | "left" | "right" };
  };
  text?: {
    content?: string;
    role?: "headline" | "caption" | "chapter";
    highlight_words?: number[];
  };
};

const resolveSrc = (src: string) =>
  /^https?:\/\//.test(src) ? src : staticFile(src);

const ShotVisual: React.FC<{ shot: Shot; spec: any }> = ({ shot, spec }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const vis = shot.visual ?? {};
  const bg = vis.bg ?? spec?.palette?.background ?? "#101014";
  const durFrames = shot.duration * fps;

  if ((vis.type === "image" || vis.type === "video") && vis.src) {
    const kb = vis.kenburns ?? { zoom: 1.06 };
    const zoom = interpolate(frame, [0, durFrames], [1, kb.zoom ?? 1.06], {
      extrapolateRight: "clamp",
    });
    const panMap: Record<string, [number, number]> = {
      up: [0, -0.02],
      down: [0, 0.02],
      left: [-0.02, 0],
      right: [0.02, 0],
    };
    const [px, py] = panMap[kb.pan ?? ""] ?? [0, 0];
    const tx = interpolate(frame, [0, durFrames], [0, px * width]);
    const ty = interpolate(frame, [0, durFrames], [0, py * height]);
    const style: React.CSSProperties = {
      width: "100%",
      height: "100%",
      objectFit: "cover",
      transform: `scale(${zoom}) translate(${tx}px, ${ty}px)`,
    };
    return (
      <AbsoluteFill style={{ backgroundColor: bg }}>
        {vis.type === "image" ? (
          <Img src={resolveSrc(vis.src)} style={style} />
        ) : (
          <OffthreadVideo src={resolveSrc(vis.src)} style={style} muted />
        )}
      </AbsoluteFill>
    );
  }
  return <AbsoluteFill style={{ backgroundColor: bg }} />;
};

const ShotText: React.FC<{ shot: Shot; spec: any }> = ({ shot, spec }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const text = shot.text;
  if (!text?.content) return null;

  const role = text.role ?? "headline";
  const typo = spec?.typography ?? {};
  const pal = spec?.palette ?? {};
  const caps = spec?.captions ?? {};
  const margins = spec?.format?.safe_margins_pct ?? {
    top: 10,
    bottom: 15,
    sides: 6,
  };

  const pop = spring({ frame, fps, config: { damping: 200, stiffness: 300 } });
  const scale = interpolate(pop, [0, 1], [0.9, 1]);
  const opacity = interpolate(frame, [0, Math.round(0.15 * fps)], [0, 1], {
    extrapolateRight: "clamp",
  });

  let content = text.content;
  if (typo.case === "UPPERCASE" && role === "headline")
    content = content.toUpperCase();

  const sizePctH =
    role === "headline"
      ? typo.headline_size_pct_h ?? 6
      : role === "chapter"
        ? 4.5
        : 3.5;

  const positionStyle: React.CSSProperties =
    role === "headline"
      ? { justifyContent: "center" }
      : role === "chapter"
        ? { justifyContent: "flex-start", paddingTop: `${margins.top}%` }
        : caps.position === "lower-third"
          ? { justifyContent: "flex-end", paddingBottom: `${margins.bottom}%` }
          : caps.position === "top"
            ? { justifyContent: "flex-start", paddingTop: `${margins.top}%` }
            : { justifyContent: "flex-start", paddingTop: "60%" }; // chest

  const words = content.split(/\s+/);
  const highlight = new Set(text.highlight_words ?? []);
  const highlightColor =
    caps.highlight?.value ?? pal.accent ?? pal.text_primary ?? "#fff";

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        alignItems: "center",
        paddingLeft: `${margins.sides}%`,
        paddingRight: `${margins.sides}%`,
        ...positionStyle,
      }}
    >
      <div
        style={{
          fontFamily: typo.fallback_stack ?? "Inter, Arial, sans-serif",
          fontWeight: typo.weight ?? 700,
          fontSize: (sizePctH / 100) * height,
          color: pal.text_primary ?? "#fff",
          textAlign: "center",
          lineHeight: 1.1,
          textShadow: "0 2px 12px rgba(0,0,0,0.45)",
          transform: `scale(${scale})`,
          opacity,
        }}
      >
        {words.map((w, i) => (
          <span
            key={i}
            style={{ color: highlight.has(i) ? highlightColor : undefined }}
          >
            {w}{" "}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

export const Main: React.FC<{ timeline: any; spec: any }> = ({
  timeline,
  spec,
}) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill
      style={{ backgroundColor: spec?.palette?.background ?? "#000" }}
    >
      {(timeline.shots as Shot[]).map((shot, i) => (
        <Sequence
          key={i}
          from={Math.round(shot.start * fps)}
          durationInFrames={Math.max(1, Math.round(shot.duration * fps))}
        >
          <ShotVisual shot={shot} spec={spec} />
          <ShotText shot={shot} spec={spec} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
