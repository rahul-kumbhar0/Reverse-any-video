import React from "react";
import {
  AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence, interpolate, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import words from "../public/cooker/words.json";
import lipsync from "../public/cooker/lipsync.json";
import aCut from "../public/cooker/cutaway.anchors.json";
import aWeight from "../public/cooker/weight.anchors.json";
import aSafety from "../public/cooker/safety.anchors.json";
import { PuppetTrack, PoseCue, Triggers } from "./puppet/PuppetTrack";

/* "Why does a pressure cooker whistle?" — 45 s, photoreal-tech-explainer style. */
export const COOKER_SECONDS = 45;

const C = { white: "#FFFFFF", dim: "#9A9AA0", amber: "#E0A33E", blue: "#3478F6", surface: "#141418" };
const FONT = "-apple-system, 'SF Pro Display', Inter, 'Helvetica Neue', Arial, sans-serif";
type W = { word: string; start: number; end: number; line: string };
const WORDS = words.words as W[];

/* ---------------------------------------------------------------- shot timeline */
const SHOTS = [
  { id: "hero", from: 0, to: 5.9 },
  { id: "cutaway", from: 5.9, to: 12.9 },
  { id: "evidence", from: 12.9, to: 24.4 },
  { id: "weight", from: 24.4, to: 33.8 },
  { id: "safety", from: 33.8, to: 38.3 },
  { id: "pullback", from: 38.3, to: 42.1 },
  { id: "cta", from: 42.1, to: 45 },
];
const XF = 0.3; // push-crossfade overlap (style: morphs, not hard cuts)

const ShotLayer: React.FC<{ from: number; to: number; children: React.ReactNode }> = ({ from, to, children }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const t = frame / fps;
  const local = t - from;
  const fadeIn = from === 0 ? 1 : interpolate(local, [0, XF], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const push = interpolate(local, [0, XF], [1.05, 1], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <Sequence from={Math.round(from * fps)} durationInFrames={Math.round((to - from + XF) * fps)}>
      <AbsoluteFill style={{ opacity: fadeIn, transform: `scale(${push})` }}>{children}</AbsoluteFill>
    </Sequence>
  );
};

const Video: React.FC<{ src: string }> = ({ src }) => (
  <OffthreadVideo src={staticFile(`cooker/${src}`)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
);

/* ---------------------------------------------------------------- tracked labels */
type Anchors = { fps: number; anchors: Record<string, number[][]> };
const at = (a: Anchors, name: string, t: number) => {
  const tr = a.anchors[name];
  const f = Math.min(Math.max(t * a.fps, 0), tr.length - 1);
  const i = Math.floor(f), j = Math.min(i + 1, tr.length - 1), k = f - i;
  return [tr[i][0] + (tr[j][0] - tr[i][0]) * k, tr[i][1] + (tr[j][1] - tr[i][1]) * k];
};

const Label: React.FC<{ a: Anchors; name: string; text: string; shotFrom: number; showAt: number; up?: number }> = ({
  a, name, text, shotFrom, showAt, up = 70,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;                          // composition time (inside Sequence: local)
  const tc = t + shotFrom;
  const [nx, ny] = at(a, name, t);
  const x = nx * width, y = ny * height;
  const lineIn = interpolate(tc, [showAt, showAt + 0.2], [0, 1], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const textIn = interpolate(tc, [showAt + 0.1, showAt + 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tw = 380;
  const tx = Math.min(Math.max(x - tw / 2, width * 0.04), width * 0.96 - tw);
  return (
    <>
      <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" }}>
        <circle cx={x} cy={y} r={6 * lineIn} fill="white" />
        <line x1={x} y1={y} x2={x} y2={y - up * lineIn} stroke="white" strokeWidth={2} opacity={lineIn} />
      </svg>
      <div style={{ position: "absolute", left: tx, top: y - up - 52, width: tw, display: "flex", justifyContent: "center",
        opacity: textIn, transform: `translateY(${(1 - textIn) * 6}px)` }}>
        <span style={{ fontFamily: FONT, fontSize: 25, fontWeight: 600, letterSpacing: 3, color: C.white, padding: "7px 14px",
          borderRadius: 10, background: "rgba(10,10,12,0.72)", border: "1px solid rgba(255,255,255,0.16)" }}>{text}</span>
      </div>
    </>
  );
};

const Footnote: React.FC<{ left?: string; right?: string }> = ({ left, right }) => (
  <>
    {left ? <div style={{ position: "absolute", bottom: "26%", left: "4%", fontFamily: FONT, fontSize: 22, color: "#7A7A80" }}>{left}</div> : null}
    {right ? <div style={{ position: "absolute", bottom: "26%", right: "4%", fontFamily: FONT, fontSize: 22, color: "#7A7A80", textAlign: "right" }}>{right}</div> : null}
  </>
);

/* ---------------------------------------------------------------- evidence: gauge + thermometer */
const Gauge: React.FC<{ value: number }> = ({ value }) => {
  // dial 0..3 atm over 240 degrees
  const ang = -120 + (value / 3) * 240;
  return (
    <svg viewBox="-160 -160 320 320" style={{ width: 420, height: 420 }}>
      <circle r={150} fill="#0E0E12" stroke="#3A3A42" strokeWidth={6} />
      <circle r={138} fill="none" stroke="#24242A" strokeWidth={2} />
      {Array.from({ length: 31 }, (_, i) => {
        const a = ((-120 + i * 8) * Math.PI) / 180, major = i % 10 === 0;
        return <line key={i} x1={Math.sin(a) * (major ? 108 : 118)} y1={-Math.cos(a) * (major ? 108 : 118)}
          x2={Math.sin(a) * 130} y2={-Math.cos(a) * 130} stroke={i > 20 ? "#E05A3E" : "#C8CAD0"} strokeWidth={major ? 5 : 2} />;
      })}
      {[0, 1, 2, 3].map((n) => {
        const a = ((-120 + n * 80) * Math.PI) / 180;
        return <text key={n} x={Math.sin(a) * 86} y={-Math.cos(a) * 86 + 10} fill="#E8E8EC" fontSize={28} fontFamily={FONT} textAnchor="middle" fontWeight={600}>{n}</text>;
      })}
      <text y={56} fill="#9A9AA0" fontSize={20} fontFamily={FONT} textAnchor="middle" letterSpacing={3}>ATM</text>
      <g transform={`rotate(${ang})`}>
        <path d="M-5 14 L0 -122 L5 14Z" fill={C.amber} />
      </g>
      <circle r={14} fill="#2A2A30" stroke={C.amber} strokeWidth={3} />
    </svg>
  );
};

const Thermo: React.FC<{ temp: number; glow: number }> = ({ temp, glow }) => {
  const fill = interpolate(temp, [80, 125], [0.15, 0.95], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
      <svg viewBox="0 0 80 360" style={{ width: 90, height: 400 }}>
        <rect x={26} y={10} width={28} height={290} rx={14} fill="#16161A" stroke="#3A3A42" strokeWidth={3} />
        <rect x={33} y={10 + 280 * (1 - fill)} width={14} height={280 * fill + 10} rx={7} fill={C.amber} />
        <circle cx={40} cy={318} r={34} fill={C.amber} stroke="#3A3A42" strokeWidth={3} />
        <circle cx={40} cy={318} r={44} fill={C.amber} opacity={0.15 * glow} />
      </svg>
      <div style={{ fontFamily: FONT, color: C.white }}>
        <div style={{ fontSize: 30, color: C.dim, letterSpacing: 2 }}>BOILING POINT</div>
        <div style={{ fontSize: 150, fontWeight: 700, lineHeight: 1, color: temp > 101 ? C.amber : C.white,
          textShadow: `0 0 ${40 * glow}px rgba(224,163,62,${0.5 * glow})` }}>{Math.round(temp)}°C</div>
        <div style={{ fontSize: 28, color: C.dim, marginTop: 10 }}>{temp > 101 ? "inside the cooker" : "open pot"}</div>
      </div>
    </div>
  );
};

const Evidence: React.FC<{ shotFrom: number }> = ({ shotFrom }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tc = frame / fps + shotFrom;
  const atm = interpolate(tc, [13.3, 15.4], [1, 2], { easing: Easing.inOut(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const gaugeOut = interpolate(tc, [16.0, 16.5], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const thermoIn = interpolate(tc, [16.2, 16.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const temp = interpolate(tc, [17.6, 19.0, 19.67, 20.3], [100, 100, 108, 120], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = interpolate(tc, [19.7, 20.4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const zoom = 1.08 + (tc - shotFrom) * 0.006;
  return (
    <AbsoluteFill>
      <Img src={staticFile("cooker/cutaway_last.png")} style={{ width: "100%", height: "100%", objectFit: "cover",
        filter: "blur(18px) brightness(0.45)", transform: `scale(${zoom})` }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 260 }}>
        <div style={{ position: "absolute", opacity: gaugeOut, transform: `scale(${0.96 + 0.04 * gaugeOut})`, textAlign: "center" }}>
          <Gauge value={atm} />
          <div style={{ fontFamily: FONT, fontSize: 34, color: C.white, marginTop: 10 }}>
            <span style={{ color: C.dim }}>air outside </span>1 atm <span style={{ color: C.dim }}>→ cooker </span>
            <span style={{ color: C.amber, fontWeight: 700 }}>~2 atm</span>
          </div>
        </div>
        <div style={{ position: "absolute", opacity: thermoIn, transform: `scale(${0.96 + 0.04 * thermoIn})` }}>
          <Thermo temp={temp} glow={glow} />
        </div>
      </AbsoluteFill>
      <Footnote left="Typical: ~1 bar (15 psi) above air pressure" />
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- share-sheet CTA */
const ShareSheet: React.FC<{ shotFrom: number }> = ({ shotFrom }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tc = frame / fps + shotFrom;
  const rise = interpolate(tc, [42.15, 42.55], [0, 1], { easing: Easing.out(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tap = tc > 43.7;
  const people = [["M", "mummy"], ["R", "rahul"], ["P", "priya"], ["A", "arjun"]];
  return (
    <AbsoluteFill>
      <Img src={staticFile("cooker/pullback_last.png")} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(14px) brightness(0.5)" }} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", paddingBottom: 300 }}>
        <div style={{ width: 860, borderRadius: 40, background: C.surface, border: "1px solid #2E2E34", padding: "46px 50px 64px",
          fontFamily: FONT, transform: `translateY(${(1 - rise) * 600}px)` }}>
          <div style={{ width: 90, height: 8, borderRadius: 4, background: "#3A3A40", margin: "0 auto 36px" }} />
          <div style={{ height: 76, borderRadius: 20, background: "#22222A", display: "flex", alignItems: "center", padding: "0 28px",
            color: C.dim, fontSize: 30, marginBottom: 42 }}>🔍&nbsp; Search</div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            {people.map(([ini, name], i) => (
              <div key={ini} style={{ textAlign: "center" }}>
                <div style={{ width: 130, height: 130, borderRadius: 65, background: `hsl(${20 + i * 70}, 38%, 36%)`, display: "flex",
                  alignItems: "center", justifyContent: "center", fontSize: 52, color: C.white, fontWeight: 700,
                  border: i === 0 && tap ? `5px solid ${C.blue}` : "5px solid transparent", transform: i === 0 && tap ? "scale(0.95)" : "none" }}>{ini}</div>
                <div style={{ color: i === 0 && tap ? C.blue : C.dim, fontSize: 26, marginTop: 14 }}>{i === 0 && tap ? "Sent ✓" : name}</div>
              </div>
            ))}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- captions from word timings */
type Tok = { text: string; start: number; style?: "bold" | "box" };
const MERGES: { seq: string[]; text: string; style?: "bold" | "box" }[] = [
  { seq: ["one", "hundred", "and", "twenty", "degrees"], text: "120°C", style: "box" },
  { seq: ["one", "hundred"], text: "100°C." },
];
const BOX = new Set(["whistles", "cooker", "steam", "gasket", "double", "dal", "weight", "lifts", "whistle", "safety", "pressure", "them", "minutes"]);
const BOLD = new Set(["inside", "nowhere", "heavy", "tiny", "vent", "blocked", "melts", "extra", "every", "rushes", "sealed", "seals", "boils", "send"]);
const PUNCT: Record<string, string> = { whistles: "whistles.", cooker: "cooker?", steam: "steam.", go: "go.", outside: "outside.",
  minutes: "minutes.", vent: "vent.", out: "out.", whistle: "whistle!", first: "first.", pressure: "pressure", them: "them." };

const buildPhrases = (): Tok[][] => {
  const phrases: Tok[][] = [];
  let cur: Tok[] = [];
  let usedBox = false;
  let i = 0;
  const flush = () => { if (cur.length) phrases.push(cur); cur = []; usedBox = false; };
  while (i < WORDS.length) {
    const w = WORDS[i];
    const m = MERGES.find((mm) => mm.seq.every((s, k) => WORDS[i + k]?.word.toLowerCase() === s));
    let tok: Tok;
    if (m) {
      tok = { text: m.text, start: w.start, style: m.style };
      i += m.seq.length;
    } else {
      const lw = w.word.toLowerCase();
      tok = { text: PUNCT[lw] && (WORDS[i + 1]?.line !== w.line || lw === "whistle") ? PUNCT[lw] : w.word, start: w.start,
        style: BOX.has(lw) && !usedBox ? "box" : BOLD.has(lw) ? "bold" : undefined };
      i += 1;
    }
    if (tok.style === "box") usedBox = true;
    const prev = WORDS[i - 1];
    const next = WORDS[i];
    cur.push(tok);
    const sentenceEnd = !next || next.line !== prev.line;
    const pause = next && next.start - prev.end > 0.28;
    if (sentenceEnd || pause || cur.length >= 4) flush();
  }
  flush();
  return phrases;
};
const PHRASES = buildPhrases();

const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;
  let pi = -1;
  PHRASES.forEach((p, i) => { if (t >= p[0].start - 0.06) pi = i; });
  if (pi < 0) return null;
  const ph = PHRASES[pi];
  return (
    <div style={{ position: "absolute", top: "7%", left: "5%", right: "5%", textAlign: "center", fontFamily: FONT, fontSize: height * 0.032, lineHeight: 1.45 }}>
      {ph.map((tok, k) => {
        const op = interpolate(t, [tok.start - 0.04, tok.start + 0.08], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        if (tok.style === "box") {
          const d = interpolate(t, [tok.start, tok.start + 0.2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <span key={k} style={{ position: "relative", display: "inline-block", padding: "2px 14px", margin: "0 4px", borderRadius: 10,
              border: `3px solid rgba(52,120,246,${d})`, background: `rgba(52,120,246,${0.1 * d})`, color: C.white, fontWeight: 700, opacity: op }}>
              {tok.text}
              <span style={{ position: "absolute", left: -8, top: -8, width: 14, height: 14, borderRadius: 7, background: C.blue, opacity: d }} />
              <span style={{ position: "absolute", right: -8, bottom: -8, width: 14, height: 14, borderRadius: 7, background: C.blue, opacity: d }} />
            </span>
          );
        }
        return <span key={k} style={{ display: "inline-block", margin: "0 6px", color: tok.style === "bold" ? C.white : C.dim,
          fontWeight: tok.style === "bold" ? 700 : 400, opacity: op, transform: `translateY(${(1 - op) * 6}px)` }}>{tok.text}</span>;
      })}
    </div>
  );
};

/* ---------------------------------------------------------------- presenter direction */
const CUES: PoseCue[] = [
  { t: 0, pose: "explain" }, { t: 3.0, pose: "think" }, { t: 5.9, pose: "point_up" }, { t: 8.8, pose: "explain" },
  { t: 12.9, pose: "fist" }, { t: 16.2, pose: "point_up" }, { t: 21.8, pose: "thumbs_up" }, { t: 24.4, pose: "point_up" },
  { t: 27.7, pose: "explain" }, { t: 32.15, pose: "wow" }, { t: 33.8, pose: "think" }, { t: 38.3, pose: "explain" },
  { t: 42.1, pose: "peace" },
];
const TRIGGERS: Triggers = {
  whistles: { pose: "wow", dur: 0.7 }, twenty: { pose: "wow", dur: 1.0 }, lifts: { pose: "fist", dur: 0.7 },
  melts: { pose: "shrug", dur: 0.9 }, minutes: { pose: "thumbs_up", dur: 0.8 },
};

/* ---------------------------------------------------------------- root */
export const CookerReel: React.FC = () => {
  const { height } = useVideoConfig();
  const S = Object.fromEntries(SHOTS.map((s) => [s.id, s]));
  return (
    <AbsoluteFill style={{ background: "#050507" }}>
      <ShotLayer {...S.hero}>
        <Video src="hero.mp4" />
        <Footnote left="Illustrative · unbranded cooker" />
      </ShotLayer>
      <ShotLayer {...S.cutaway}>
        <Video src="cutaway.mp4" />
        <Label a={aCut as Anchors} name="gasket" text="RUBBER GASKET" shotFrom={5.9} showAt={9.3} up={80} />
        <Footnote left="Cutaway illustration" />
      </ShotLayer>
      <ShotLayer {...S.evidence}><Evidence shotFrom={12.9} /></ShotLayer>
      <ShotLayer {...S.weight}>
        <Video src="weight.mp4" />
        <Label a={aWeight as Anchors} name="weight" text="WEIGHT VALVE" shotFrom={24.4} showAt={25.6} up={90} />
        <Footnote left="Magnified illustration" />
      </ShotLayer>
      <ShotLayer {...S.safety}>
        <Video src="safety.mp4" />
        <Label a={aSafety as Anchors} name="plug" text="SAFETY VALVE" shotFrom={33.8} showAt={36.1} up={110} />
        <Footnote left="Fusible-alloy safety plug" />
      </ShotLayer>
      <ShotLayer {...S.pullback}><Video src="pullback.mp4" /></ShotLayer>
      <ShotLayer {...S.cta}><ShareSheet shotFrom={42.1} /></ShotLayer>

      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, transparent 52%, rgba(0,0,0,0.55) 100%)" }} />
      <Captions />
      <div style={{ position: "absolute", left: "50%", bottom: -70, transform: "translateX(-50%)",
        width: height * 0.25 * (400 / 520), height: height * 0.25 }}>
        <PuppetTrack character="kai" cues={CUES} triggers={TRIGGERS} words={WORDS} lipsync={lipsync as any} />
      </div>
      <Audio src={staticFile("cooker/audio.wav")} />
    </AbsoluteFill>
  );
};
