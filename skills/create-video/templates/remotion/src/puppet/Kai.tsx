import React from "react";
import type { Brows, Pose, Viseme } from "./Nova";

/**
 * Kai — ORIGINAL presenter character, semi-realistic illustrated style (gradient shading,
 * real lips/eyes/nose, knuckled hands). Same layer API as Nova (poses, visemes, blinks,
 * brows, head drift) so PuppetTrack/lipsync drive it unchanged.
 * Signature: orange over-ear headphones around the neck, mustard overshirt, rolled sleeves.
 */

const OUT = "#22150F";
const SKIN = "#A9724F", SKIN_SH = "#87573B", SKIN_DEEP = "#6E4430", SKIN_HI = "#C48C66";
const LIP = "#7C4636", LIP_HI = "#97584A", MOUTH = "#3A1414", TONGUE = "#B85A5A", TEETH = "#F3EEE6";
const HAIR = "#17110E", HAIR_HI = "#3B2C24", HAIR_FADE = "#2A1E18";
const SHIRT = "#D6A03A", SHIRT_SH = "#AE7E26", SHIRT_HI = "#EDBF5E";
const TEE = "#1D1D21", TEE_HI = "#2C2C33";
const PHONE = "#E8762C", PHONE_SH = "#B9561B", PHONE_BAND = "#26262C";
const IRIS = "#4A2A19", SCLERA = "#F2EBE3";

/* ------------------------------------------------------------- hands (knuckled) */
type Prim =
  | { k: "cap"; x1: number; y1: number; x2: number; y2: number; w: number }
  | { k: "rr"; x: number; y: number; w: number; h: number; r: number };
const finger = (x: number, y1: number, y2: number, w = 11, x2 = x): Prim => ({ k: "cap", x1: x, y1, x2, y2, w });
const PALM: Prim = { k: "rr", x: -21, y: -50, w: 42, h: 46, r: 14 };
const KNUCKLES: Prim[] = [-14, -5, 4, 13].map((x) => finger(x, -50, -57, 11));
type HandType = "open" | "relaxed" | "point" | "fist" | "thumb" | "peace";
const HAND: Record<HandType, Prim[]> = {
  open: [PALM, finger(-15, -48, -79, 10.5, -19), finger(-5, -50, -88, 10.5), finger(5, -50, -86, 10.5), finger(15, -48, -75, 10, 19),
    { k: "cap", x1: -18, y1: -20, x2: -36, y2: -45, w: 12 }],
  relaxed: [PALM, finger(-13, -48, -75), finger(-4, -50, -81), finger(5, -50, -79), finger(14, -48, -71),
    { k: "cap", x1: -18, y1: -22, x2: -28, y2: -44, w: 12 }],
  point: [PALM, ...KNUCKLES.slice(1), finger(-12, -50, -96, 10.5), { k: "cap", x1: -16, y1: -24, x2: 4, y2: -36, w: 12 }],
  fist: [PALM, ...KNUCKLES, { k: "cap", x1: -18, y1: -26, x2: 6, y2: -38, w: 12 }],
  thumb: [{ k: "rr", x: -24, y: -44, w: 48, h: 40, r: 14 }, { k: "cap", x1: -12, y1: -42, x2: -12, y2: -78, w: 13 },
    ...[-30, -20, -10].map((y) => ({ k: "cap" as const, x1: 18, y1: y, x2: 26, y2: y, w: 10 }))],
  peace: [PALM, finger(5, -50, -58), finger(14, -48, -56), finger(-14, -50, -92, 10.5, -24), finger(-3, -50, -94, 10.5, 4),
    { k: "cap", x1: -16, y1: -24, x2: 6, y2: -36, w: 12 }],
};
const draw = (prims: Prim[], fill: string, grow: number, key: string) =>
  prims.map((p, i) => p.k === "cap"
    ? <line key={key + i} x1={p.x1} y1={p.y1} x2={p.x2} y2={p.y2} stroke={fill} strokeWidth={p.w + grow} strokeLinecap="round" />
    : <rect key={key + i} x={p.x - grow / 2} y={p.y - grow / 2} width={p.w + grow} height={p.h + grow} rx={p.r + grow / 2} fill={fill} />);
const creases = (prims: Prim[]) => prims.filter((p) => p.k === "cap" && Math.abs(p.y2 - p.y1) > 20).map((p, i) => {
  const c = p as Extract<Prim, { k: "cap" }>;
  const mx = c.x1 + (c.x2 - c.x1) * 0.55, my = c.y1 + (c.y2 - c.y1) * 0.55;
  return <path key={"c" + i} d={`M${mx - 3.5} ${my} Q${mx} ${my + 1.5} ${mx + 3.5} ${my}`} stroke={SKIN_DEEP} strokeWidth={1.3} fill="none" opacity={0.7} />;
});

const Hand: React.FC<{ type: HandType; x: number; y: number; angle: number; flip?: boolean }> = ({ type, x, y, angle, flip }) => {
  const s = type === "thumb" ? 1.2 : 1;
  return (
    <g transform={`translate(${x} ${y}) rotate(${angle}) scale(${(flip ? -1 : 1) * s} ${s})`}>
      {draw(HAND[type], OUT, 5, "o")}
      {draw(HAND[type], SKIN, 0, "f")}
      <path d="M6 -48 Q20 -42 19 -14 Q15 -6 6 -6 Q14 -26 6 -48Z" fill={SKIN_SH} opacity={0.7} />
      <path d="M-17 -44 Q-10 -48 -4 -44" stroke={SKIN_HI} strokeWidth={3} fill="none" strokeLinecap="round" opacity={0.6} />
      {creases(HAND[type])}
    </g>
  );
};

/* ------------------------------------------------------------- arms: rolled sleeves */
type ArmDef = { e: [number, number]; w: [number, number]; hand: HandType; rot?: number };
const SL: [number, number] = [108, 334], SR: [number, number] = [292, 334];
const IDLE_L: ArmDef = { e: [84, 428], w: [94, 514], hand: "relaxed" };
const IDLE_R: ArmDef = { e: [316, 428], w: [306, 514], hand: "relaxed" };
const POSES: Record<Pose, { L: ArmDef; R: ArmDef; brows: Brows; tilt: number }> = {
  idle: { L: IDLE_L, R: IDLE_R, brows: "neutral", tilt: 0 },
  point_up: { L: IDLE_L, R: { e: [354, 302], w: [340, 214], hand: "point", rot: 4 }, brows: "raised", tilt: -2 },
  wave: { L: IDLE_L, R: { e: [360, 314], w: [354, 222], hand: "open", rot: 12 }, brows: "raised", tilt: -3 },
  thumbs_up: { L: IDLE_L, R: { e: [348, 442], w: [308, 352], hand: "thumb", rot: 26 }, brows: "raised", tilt: 2 },
  shrug: { L: { e: [56, 406], w: [34, 338], hand: "open", rot: -55 }, R: { e: [344, 406], w: [366, 338], hand: "open", rot: 55 }, brows: "worried", tilt: 4 },
  explain: { L: IDLE_L, R: { e: [346, 442], w: [302, 376], hand: "open", rot: 24 }, brows: "neutral", tilt: -1 },
  think: { L: IDLE_L, R: { e: [318, 432], w: [240, 300], hand: "fist", rot: -20 }, brows: "focused", tilt: 3 },
  wow: { L: { e: [54, 302], w: [94, 214], hand: "open", rot: -10 }, R: { e: [346, 302], w: [306, 214], hand: "open", rot: 10 }, brows: "raised", tilt: 0 },
  present: { L: { e: [50, 394], w: [8, 354], hand: "open", rot: -75 }, R: IDLE_R, brows: "raised", tilt: -3 },
  peace: { L: IDLE_L, R: { e: [358, 304], w: [344, 218], hand: "peace", rot: 6 }, brows: "neutral", tilt: -2 },
  fist: { L: IDLE_L, R: { e: [354, 294], w: [338, 206], hand: "fist", rot: 0 }, brows: "focused", tilt: -2 },
};

const Arm: React.FC<{ s: [number, number]; def: ArmDef; side: "L" | "R" }> = ({ s, def, side }) => {
  const [ex, ey] = def.e, [wx, wy] = def.w;
  const ang = (Math.atan2(wy - ey, wx - ex) * 180) / Math.PI + 90 + (def.rot ?? 0);
  const upper = `M${s[0]} ${s[1]} L${ex} ${ey}`;
  // rolled cuff sits just past the elbow, on the forearm
  const rx = ex + (wx - ex) * 0.12, ry = ey + (wy - ey) * 0.12;
  const fore = `M${rx} ${ry} L${wx} ${wy}`;
  const cuffAng = (Math.atan2(wy - ey, wx - ex) * 180) / Math.PI;
  const off = side === "L" ? -8 : 8;
  return (
    <g>
      <path d={fore} stroke={OUT} strokeWidth={41} strokeLinecap="round" />
      <path d={fore} stroke={SKIN} strokeWidth={36} strokeLinecap="round" />
      <path d={fore} stroke={SKIN_SH} strokeWidth={10} strokeLinecap="round" transform={`translate(${off} 3)`} opacity={0.85} />
      <path d={`M${s[0]} ${s[1]} L${ex} ${ey} L${rx} ${ry}`} stroke={OUT} strokeWidth={50} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={`M${s[0]} ${s[1]} L${ex} ${ey} L${rx} ${ry}`} stroke={SHIRT} strokeWidth={44} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={upper} stroke={SHIRT_SH} strokeWidth={14} fill="none" strokeLinecap="round" transform={`translate(${off} 4)`} />
      <path d={upper} stroke={SHIRT_HI} strokeWidth={5} fill="none" strokeLinecap="round" transform={`translate(${-off * 1.2} -2)`} opacity={0.8} />
      {/* rolled cuff */}
      <g transform={`translate(${rx} ${ry}) rotate(${cuffAng})`}>
        <rect x={-14} y={-26} width={22} height={52} rx={9} fill={SHIRT_SH} stroke={OUT} strokeWidth={2.5} />
        <line x1={-3} y1={-22} x2={-3} y2={22} stroke={SHIRT} strokeWidth={4} strokeLinecap="round" />
      </g>
      <Hand type={def.hand} x={wx} y={wy} angle={ang} flip={side === "L"} />
    </g>
  );
};

/* ------------------------------------------------------------- face */
const BROW_SHAPES: Record<Brows, [string, string]> = {
  neutral: ["M146 140 Q166 128 190 134 L189 140 Q167 136 148 146Z", "M254 140 Q234 128 210 134 L211 140 Q233 136 252 146Z"],
  raised: ["M146 132 Q166 118 190 126 L189 132 Q167 126 148 138Z", "M254 132 Q234 118 210 126 L211 132 Q233 126 252 138Z"],
  worried: ["M148 140 Q168 134 190 124 L190 131 Q169 140 150 147Z", "M252 140 Q232 134 210 124 L210 131 Q231 140 250 147Z"],
  focused: ["M146 134 Q168 136 190 144 L189 150 Q167 142 148 141Z", "M254 134 Q232 136 210 144 L211 150 Q233 142 252 141Z"],
};

const Eye: React.FC<{ cx: number; blink: number; look: number; flip?: boolean }> = ({ cx, blink, look, flip }) => {
  const cy = 170;
  const f = flip ? -1 : 1;
  const almond = `M${cx - 17 * f} ${cy + 1} Q${cx - 4 * f} ${cy - 11} ${cx + 15 * f} ${cy - 2} Q${cx + 4 * f} ${cy + 8} ${cx - 17 * f} ${cy + 1}Z`;
  if (blink >= 2) {
    return (<g>
      <path d={`M${cx - 17 * f} ${cy + 1} Q${cx} ${cy + 7} ${cx + 15 * f} ${cy - 1}`} stroke={OUT} strokeWidth={3} fill="none" strokeLinecap="round" />
      <path d={`M${cx - 15 * f} ${cy - 4} Q${cx} ${cy - 6} ${cx + 13 * f} ${cy - 5}`} stroke={SKIN_SH} strokeWidth={2} fill="none" opacity={0.8} />
    </g>);
  }
  const id = `kaiEye${cx}`;
  return (
    <g>
      <defs><clipPath id={id}><path d={almond} /></clipPath></defs>
      <path d={almond} fill={SCLERA} />
      <g clipPath={`url(#${id})`}>
        <circle cx={cx + look} cy={cy - 1} r={7.6} fill={IRIS} />
        <circle cx={cx + look} cy={cy - 1} r={7.6} fill="url(#kaiIris)" />
        <circle cx={cx + look} cy={cy - 1} r={3.4} fill="#0D0705" />
        <circle cx={cx + look - 2.6} cy={cy - 4} r={2} fill="#fff" />
        {/* upper lid shadow on the eyeball */}
        <path d={`M${cx - 18} ${cy - 12} L${cx + 18} ${cy - 12} L${cx + 18} ${cy - 6} Q${cx} ${cy - 2} ${cx - 18} ${cy - 6}Z`} fill={SKIN_DEEP} opacity={0.25} />
        {blink === 1 ? <path d={`M${cx - 20} ${cy - 14} L${cx + 20} ${cy - 14} L${cx + 20} ${cy + 1} L${cx - 20} ${cy + 1}Z`} fill={SKIN} /> : null}
      </g>
      {/* upper lid + lash line, lower lid hint, crease */}
      <path d={blink === 1 ? `M${cx - 17 * f} ${cy + 1} Q${cx} ${cy + 2} ${cx + 15 * f} ${cy - 1}` : `M${cx - 17 * f} ${cy + 1} Q${cx - 4 * f} ${cy - 11} ${cx + 15 * f} ${cy - 2}`}
        stroke={OUT} strokeWidth={3.2} fill="none" strokeLinecap="round" />
      <path d={`M${cx - 13 * f} ${cy + 5} Q${cx} ${cy + 8} ${cx + 11 * f} ${cy + 2}`} stroke={SKIN_DEEP} strokeWidth={1.3} fill="none" opacity={0.6} />
      <path d={`M${cx - 14 * f} ${cy - 9} Q${cx - 2 * f} ${cy - 17} ${cx + 13 * f} ${cy - 9}`} stroke={SKIN_DEEP} strokeWidth={1.4} fill="none" opacity={0.55} />
    </g>
  );
};

/* lips: params per viseme */
type MouthSpec = { w: number; h: number; round?: boolean; teethTop?: boolean; teethBot?: boolean; tongue?: boolean; fv?: boolean; smile?: number };
const MOUTHS: Record<Viseme, MouthSpec | null> = {
  rest: null, mbp: null,
  ee: { w: 34, h: 8, teethTop: true, teethBot: true, smile: 3 },
  eh: { w: 30, h: 13, teethTop: true },
  aa: { w: 28, h: 22, teethTop: true, tongue: true },
  oh: { w: 19, h: 18, round: true, tongue: true },
  uw: { w: 12, h: 11, round: true },
  fv: { w: 30, h: 7, fv: true },
  l: { w: 26, h: 16, teethTop: true, tongue: true },
  smile: { w: 36, h: 11, teethTop: true, smile: 5 },
};

const Mouth: React.FC<{ v: Viseme }> = ({ v }) => {
  const cx = 200, cy = 220;
  const spec = MOUTHS[v];
  if (!spec) {
    const press = v === "mbp";
    return (<g>
      <path d={`M${cx - 19} ${cy} Q${cx - 9} ${cy - 6} ${cx - 2} ${cy - 3} Q${cx} ${cy - 5} ${cx + 2} ${cy - 3} Q${cx + 9} ${cy - 6} ${cx + 19} ${cy} Q${cx} ${cy + 1} ${cx - 19} ${cy}Z`} fill={LIP} />
      <path d={`M${cx - 18} ${cy + 1} Q${cx} ${cy + (press ? 7 : 11)} ${cx + 18} ${cy + 1} Q${cx} ${cy + 2} ${cx - 18} ${cy + 1}Z`} fill={LIP_HI} />
      <path d={`M${cx - 20} ${cy + (press ? 0 : -1)} Q${cx} ${cy + (press ? 3 : 4)} ${cx + 20} ${cy + (press ? 0 : -1)}`} stroke={OUT} strokeWidth={2.6} fill="none" strokeLinecap="round" />
      <path d={`M${cx - 6} ${cy + 7} Q${cx} ${cy + 9} ${cx + 6} ${cy + 7}`} stroke="#fff" strokeWidth={1.5} fill="none" opacity={0.25} />
    </g>);
  }
  const { w, h, round, smile = 0 } = spec;
  const hw = w / 2;
  const top = cy - h * 0.35, bot = cy + h * 0.65;
  const open = round
    ? `M${cx - hw} ${cy} Q${cx - hw} ${top} ${cx} ${top} Q${cx + hw} ${top} ${cx + hw} ${cy} Q${cx + hw} ${bot} ${cx} ${bot} Q${cx - hw} ${bot} ${cx - hw} ${cy}Z`
    : `M${cx - hw} ${cy - smile} Q${cx} ${top - 2} ${cx + hw} ${cy - smile} Q${cx + hw * 0.7} ${bot} ${cx} ${bot + 1} Q${cx - hw * 0.7} ${bot} ${cx - hw} ${cy - smile}Z`;
  const id = `kaiMouth${v}`;
  return (
    <g>
      <defs><clipPath id={id}><path d={open} /></clipPath></defs>
      {/* lips ring */}
      <path d={open} fill="none" stroke={LIP} strokeWidth={9} strokeLinejoin="round" />
      <path d={`M${cx - hw - 2} ${cy - smile} Q${cx} ${bot + 7} ${cx + hw + 2} ${cy - smile}`} stroke={LIP_HI} strokeWidth={6} fill="none" strokeLinecap="round" opacity={0.85} />
      <path d={open} fill={MOUTH} />
      <g clipPath={`url(#${id})`}>
        {spec.teethTop || spec.fv ? <rect x={cx - hw} y={top - 4} width={w} height={spec.fv ? h + 2 : 7} rx={2} fill={TEETH} /> : null}
        {spec.teethBot ? <rect x={cx - hw} y={bot - 5} width={w} height={6} rx={2} fill={TEETH} opacity={0.9} /> : null}
        {spec.tongue ? <ellipse cx={cx} cy={bot - 1} rx={w * 0.32} ry={h * 0.28} fill={TONGUE} /> : null}
        {spec.fv ? <path d={`M${cx - hw} ${bot - 1} Q${cx} ${cy + 1} ${cx + hw} ${bot - 1} L${cx + hw} ${bot + 4} L${cx - hw} ${bot + 4}Z`} fill={LIP_HI} /> : null}
      </g>
      <path d={open} fill="none" stroke={OUT} strokeWidth={2.2} strokeLinejoin="round" />
    </g>
  );
};

/* ------------------------------------------------------------- hair (textured crop + fade) */
const HairTop: React.FC = () => {
  const curls: [number, number, number][] = [];
  for (let row = 0; row < 5; row++) {
    const n = 10 - row;
    for (let i = 0; i < n; i++) {
      const span = 116 - row * 14;
      const x = 200 - span / 2 + (i * span) / (n - 1);
      const y = 100 - row * 10 + Math.sin(i * 1.9 + row * 0.7) * 3 - Math.cos(((x - 200) / 60) * 1.4) * 4;
      curls.push([x, y, 10 - row * 0.5]);
    }
  }
  return (
    <g>
      <path d="M140 142 Q134 90 160 66 Q200 40 240 66 Q266 90 260 142 Q252 112 230 106 Q200 98 170 106 Q148 112 140 142Z" fill={HAIR} stroke={OUT} strokeWidth={2.5} />
      {curls.map(([x, y, r], i) => <circle key={"c" + i} cx={x} cy={y} r={r + 2} fill={OUT} />)}
      {curls.map(([x, y, r], i) => <circle key={"f" + i} cx={x} cy={y} r={r} fill={HAIR} />)}
      {curls.map(([x, y, r], i) => (
        <path key={"h" + i} d={`M${x - r * 0.6} ${y - r * 0.1} Q${x - r * 0.2} ${y - r * 0.85} ${x + r * 0.5} ${y - r * 0.45}`} stroke={HAIR_HI} strokeWidth={2} fill="none" strokeLinecap="round" />
      ))}
      <path d="M139 147 Q137 118 150 104 L152 152 Q145 154 139 147Z" fill={HAIR_FADE} opacity={0.75} />
      <path d="M261 147 Q263 118 250 104 L248 152 Q255 154 261 147Z" fill={HAIR_FADE} opacity={0.75} />
      <path d="M152 108 Q200 98 248 108" stroke={OUT} strokeWidth={2} fill="none" opacity={0.5} />
    </g>
  );
};

/* ------------------------------------------------------------- body */
const TORSO = "M54 528 L62 380 Q70 314 148 300 L252 300 Q330 314 338 380 L346 528 Z";

export const Kai: React.FC<{
  pose: Pose; viseme?: Viseme; blink?: 0 | 1 | 2; brows?: Brows;
  headTilt?: number; headNod?: number; breathe?: number; look?: number;
}> = ({ pose, viseme = "rest", blink = 0, brows, headTilt = 0, headNod = 0, breathe = 0, look = 0 }) => {
  const P = POSES[pose];
  const b = brows ?? P.brows;
  const tilt = P.tilt + headTilt;
  return (
    <svg viewBox="0 0 400 520" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <defs>
        <clipPath id="kaiTorso"><path d={TORSO} /></clipPath>
        <radialGradient id="kaiFace" cx="0.42" cy="0.42" r="0.65">
          <stop offset="0" stopColor={SKIN_HI} /><stop offset="0.55" stopColor={SKIN} /><stop offset="1" stopColor={SKIN_SH} />
        </radialGradient>
        <radialGradient id="kaiIris" cx="0.5" cy="0.65" r="0.6">
          <stop offset="0" stopColor="#8A5A30" stopOpacity={0.9} /><stop offset="1" stopColor={IRIS} stopOpacity={0} />
        </radialGradient>
        <linearGradient id="kaiShirt" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor={SHIRT_HI} /><stop offset="0.45" stopColor={SHIRT} /><stop offset="1" stopColor={SHIRT_SH} />
        </linearGradient>
        <linearGradient id="kaiNeck" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={SKIN_DEEP} /><stop offset="0.5" stopColor={SKIN_SH} /><stop offset="1" stopColor={SKIN} />
        </linearGradient>
        <radialGradient id="kaiCup" cx="0.35" cy="0.3" r="0.8">
          <stop offset="0" stopColor="#FF9A52" /><stop offset="0.6" stopColor={PHONE} /><stop offset="1" stopColor={PHONE_SH} />
        </radialGradient>
      </defs>
      <g transform={`translate(0 ${-breathe * 2}) scale(1 ${1 + breathe * 0.006})`} style={{ transformOrigin: "200px 520px" }}>
        {/* torso: open overshirt over a black tee */}
        <path d={TORSO} fill="url(#kaiShirt)" stroke={OUT} strokeWidth={3} strokeLinejoin="round" />
        <g clipPath="url(#kaiTorso)">
          <path d="M162 300 L238 300 L232 530 L168 530Z" fill={TEE} />
          <path d="M170 312 Q200 330 230 312 L228 360 Q200 372 172 360Z" fill={TEE_HI} opacity={0.6} />
          {/* lapels / placket edges */}
          <path d="M150 300 L176 300 L170 400 L160 530 L146 530 Q152 420 150 300Z" fill={SHIRT_SH} stroke={OUT} strokeWidth={2.5} />
          <path d="M250 300 L224 300 L230 400 L240 530 L254 530 Q248 420 250 300Z" fill={SHIRT} stroke={OUT} strokeWidth={2.5} />
          {/* chest pocket + flap */}
          <rect x={92} y={386} width={46} height={50} rx={5} fill={SHIRT_SH} opacity={0.55} stroke={OUT} strokeWidth={1.8} />
          <path d="M90 384 L140 384 L138 398 Q115 404 92 398Z" fill={SHIRT} stroke={OUT} strokeWidth={1.8} />
          <circle cx={115} cy={396} r={2.6} fill={OUT} />
          {/* fold shadows */}
          <path d="M282 318 Q326 330 334 380 L344 528 L296 528 Q306 420 282 318Z" fill={SHIRT_SH} opacity={0.75} />
          <path d="M96 344 Q120 330 148 318 Q120 344 110 380Z" fill={SHIRT_HI} opacity={0.5} />
        </g>

        {/* neck */}
        <path d="M176 232 L176 304 Q200 318 224 304 L224 232Z" fill="url(#kaiNeck)" stroke={OUT} strokeWidth={2.5} />
        <path d="M188 286 Q200 292 212 286" stroke={SKIN_DEEP} strokeWidth={1.5} fill="none" opacity={0.6} />
        {/* tee collar */}
        <path d="M162 300 Q200 324 238 300 Q236 310 200 330 Q164 310 162 300Z" fill={TEE} stroke={OUT} strokeWidth={2.5} />

        {/* signature: headphones resting around the neck */}
        <path d="M166 300 Q156 262 200 254 Q244 262 234 300" stroke={OUT} strokeWidth={12} fill="none" strokeLinecap="round" />
        <path d="M166 300 Q156 262 200 254 Q244 262 234 300" stroke={PHONE_BAND} strokeWidth={7} fill="none" strokeLinecap="round" />
        {[[166, 318, -28], [234, 318, 28]].map(([x, y, r], i) => (
          <g key={i} transform={`translate(${x} ${y}) rotate(${r})`}>
            <ellipse cx={0} cy={0} rx={24} ry={29} fill={PHONE_BAND} stroke={OUT} strokeWidth={2.5} />
            <ellipse cx={i === 0 ? -3 : 3} cy={-1} rx={19} ry={24} fill="url(#kaiCup)" stroke={OUT} strokeWidth={2.5} />
            <ellipse cx={i === 0 ? -7 : 7} cy={-9} rx={7} ry={10} fill="#fff" opacity={0.28} />
            <rect x={-6} y={-36} width={12} height={8} rx={3} fill={PHONE_BAND} stroke={OUT} strokeWidth={2} />
          </g>
        ))}

        {/* head */}
        <g transform={`rotate(${tilt} 200 262) translate(0 ${headNod * 3}) translate(200 252) scale(1.18) translate(-200 -252)`}>
          {/* ears */}
          <g>
            <path d="M140 160 Q124 158 124 178 Q125 198 142 198Z" fill={SKIN} stroke={OUT} strokeWidth={2.5} />
            <path d="M136 168 Q129 176 136 190" stroke={SKIN_DEEP} strokeWidth={2} fill="none" />
            <path d="M260 160 Q276 158 276 178 Q275 198 258 198Z" fill={SKIN_SH} stroke={OUT} strokeWidth={2.5} />
            <path d="M264 168 Q271 176 264 190" stroke={SKIN_DEEP} strokeWidth={2} fill="none" />
          </g>
          {/* face */}
          <path d="M140 150 Q140 92 200 88 Q260 92 260 150 Q262 200 242 226 Q222 250 200 252 Q178 250 158 226 Q138 200 140 150Z"
            fill="url(#kaiFace)" stroke={OUT} strokeWidth={3} />
          {/* cheekbone + jaw shading, stubble */}
          <path d="M250 150 Q262 186 246 216 Q232 240 212 248 Q236 222 242 196 Q248 172 250 150Z" fill={SKIN_SH} opacity={0.75} />
          <path d="M160 198 Q170 206 178 200" stroke={SKIN_SH} strokeWidth={4} fill="none" opacity={0.45} strokeLinecap="round" />
          <path d="M156 214 Q166 238 186 248 Q200 254 214 248 Q234 238 244 214 Q236 236 214 244 Q200 248 186 244 Q164 236 156 214Z" fill={HAIR} opacity={0.22} />
          <path d="M184 206 Q200 202 216 206 Q210 210 200 209 Q190 210 184 206Z" fill={HAIR} opacity={0.18} />
          {/* nose: bridge, tip, nostrils */}
          <path d="M196 170 Q194 186 190 196" stroke={SKIN_SH} strokeWidth={2.4} fill="none" strokeLinecap="round" opacity={0.8} />
          <path d="M188 200 Q193 206 200 205 Q207 206 212 200" stroke={SKIN_DEEP} strokeWidth={2.2} fill="none" strokeLinecap="round" />
          <ellipse cx={192.5} cy={201} rx={3} ry={1.8} fill={SKIN_DEEP} />
          <ellipse cx={207.5} cy={201} rx={3} ry={1.8} fill={SKIN_DEEP} />
          <ellipse cx={200} cy={195} rx={4} ry={2.6} fill={SKIN_HI} opacity={0.7} />
          <HairTop />
          {/* brows */}
          {BROW_SHAPES[b].map((d, i) => <path key={i} d={d} fill={HAIR} />)}
          <Eye cx={170} blink={blink} look={look} />
          <Eye cx={230} blink={blink} look={look} flip />
          <Mouth v={viseme} />
        </g>

        <Arm s={SL} def={P.L} side="L" />
        <Arm s={SR} def={P.R} side="R" />
      </g>
    </svg>
  );
};
