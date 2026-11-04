import React from "react";

/**
 * Nova — an ORIGINAL presenter puppet for the dark-explainer styles.
 * Cel-shaded vector character built from swappable layers, mirroring how pro explainer
 * mascots are animated (Character-Animator-style): arm-pose library × mouth visemes ×
 * blinks × brows, plus head drift/breathing. Never clone a real creator's mascot.
 *
 * viewBox 0 0 400 520 (waist-up). Arms/hands may overflow the box (overflow: visible).
 */

export type Pose =
  | "idle" | "point_up" | "wave" | "thumbs_up" | "shrug" | "explain"
  | "think" | "wow" | "present" | "peace" | "fist";
export type Viseme = "rest" | "mbp" | "ee" | "eh" | "aa" | "oh" | "uw" | "fv" | "l" | "smile";

/** Rhubarb Lip Sync shapes (Hanna-Barbera set) -> Nova visemes. */
export const RHUBARB_TO_VISEME: Record<string, Viseme> = {
  A: "mbp", B: "ee", C: "eh", D: "aa", E: "oh", F: "uw", G: "fv", H: "l", X: "rest",
};
export type Brows = "neutral" | "raised" | "worried" | "focused";

const OUT = "#17141C";
const SKIN = "#F2C6A2", SKIN_SH = "#D99D7C", BLUSH = "#EC9486";
const HAIR = "#2E211C", HAIR_SH = "#1D1411", HAIR_HI = "#4E3A31";
const NAVY = "#25324D", NAVY_SH = "#19223A", NAVY_HI = "#34446A";
const STRIPE = "#E8762C", STRIPE_SH = "#C45E1E";
const STRING = "#D9DDE4";

/* ---------------------------------------------------------------- hands */
type Prim =
  | { k: "cap"; x1: number; y1: number; x2: number; y2: number; w: number }
  | { k: "rr"; x: number; y: number; w: number; h: number; r: number };

const finger = (x: number, y1: number, y2: number, w = 11, x2 = x): Prim => ({ k: "cap", x1: x, y1, x2, y2, w });
const PALM: Prim = { k: "rr", x: -21, y: -50, w: 42, h: 46, r: 15 };
const KNUCKLES: Prim[] = [-14, -5, 4, 13].map((x) => finger(x, -50, -56, 11));

type HandType = "open" | "relaxed" | "point" | "fist" | "thumb" | "peace";
const HAND: Record<HandType, Prim[]> = {
  open: [PALM, finger(-15, -48, -78, 11, -19), finger(-5, -50, -86), finger(5, -50, -84), finger(15, -48, -74, 11, 19),
    { k: "cap", x1: -18, y1: -20, x2: -36, y2: -44, w: 12 }],
  relaxed: [PALM, finger(-13, -48, -74), finger(-4, -50, -80), finger(5, -50, -78), finger(14, -48, -70),
    { k: "cap", x1: -18, y1: -22, x2: -28, y2: -44, w: 12 }],
  point: [PALM, ...KNUCKLES.slice(1), finger(-12, -50, -94, 11), { k: "cap", x1: -16, y1: -24, x2: 4, y2: -36, w: 12 }],
  fist: [PALM, ...KNUCKLES, { k: "cap", x1: -18, y1: -26, x2: 6, y2: -38, w: 12 }],
  thumb: [{ k: "rr", x: -24, y: -44, w: 48, h: 40, r: 15 }, { k: "cap", x1: -12, y1: -42, x2: -12, y2: -76, w: 13 },
    ...[-30, -20, -10].map((y) => ({ k: "cap" as const, x1: 18, y1: y, x2: 26, y2: y, w: 10 }))],
  peace: [PALM, finger(5, -50, -58), finger(14, -48, -56), finger(-14, -50, -90, 11, -24), finger(-3, -50, -92, 11, 4),
    { k: "cap", x1: -16, y1: -24, x2: 6, y2: -36, w: 12 }],
};

const drawPrims = (prims: Prim[], fill: string, grow: number, key: string) =>
  prims.map((p, i) =>
    p.k === "cap" ? (
      <line key={key + i} x1={p.x1} y1={p.y1} x2={p.x2} y2={p.y2} stroke={fill} strokeWidth={p.w + grow} strokeLinecap="round" />
    ) : (
      <rect key={key + i} x={p.x - grow / 2} y={p.y - grow / 2} width={p.w + grow} height={p.h + grow} rx={p.r + grow / 2} fill={fill} />
    )
  );

const Hand: React.FC<{ type: HandType; x: number; y: number; angle: number; flip?: boolean }> = ({ type, x, y, angle, flip }) => (
  <g transform={`translate(${x} ${y}) rotate(${angle}) scale(${(flip ? -1 : 1) * (type === "thumb" ? 1.2 : 1)} ${type === "thumb" ? 1.2 : 1})`}>
    {drawPrims(HAND[type], OUT, 6, "o")}
    {drawPrims(HAND[type], SKIN, 0, "f")}
    {/* palm shading */}
    <path d="M8 -46 Q20 -40 18 -14 Q14 -6 6 -6 Q14 -24 8 -46Z" fill={SKIN_SH} opacity={0.55} />
  </g>
);

/* ---------------------------------------------------------------- arms */
type ArmDef = { e: [number, number]; w: [number, number]; hand: HandType; rot?: number };
const SHOULDER_L: [number, number] = [112, 330];
const SHOULDER_R: [number, number] = [288, 330];

const IDLE_L: ArmDef = { e: [86, 425], w: [96, 512], hand: "relaxed", rot: 0 };
const IDLE_R: ArmDef = { e: [314, 425], w: [304, 512], hand: "relaxed", rot: 0 };

const POSES: Record<Pose, { L: ArmDef; R: ArmDef; brows: Brows; tilt: number }> = {
  idle: { L: IDLE_L, R: IDLE_R, brows: "neutral", tilt: 0 },
  point_up: { L: IDLE_L, R: { e: [352, 300], w: [338, 214], hand: "point", rot: 4 }, brows: "raised", tilt: -2 },
  wave: { L: IDLE_L, R: { e: [358, 312], w: [352, 222], hand: "open", rot: 12 }, brows: "raised", tilt: -3 },
  thumbs_up: { L: IDLE_L, R: { e: [346, 440], w: [306, 352], hand: "thumb", rot: 26 }, brows: "raised", tilt: 2 },
  shrug: { L: { e: [58, 404], w: [36, 336], hand: "open", rot: -55 }, R: { e: [342, 404], w: [364, 336], hand: "open", rot: 55 },
    brows: "worried", tilt: 4 },
  explain: { L: IDLE_L, R: { e: [344, 440], w: [300, 376], hand: "open", rot: 24 }, brows: "neutral", tilt: -1 },
  think: { L: IDLE_L, R: { e: [316, 430], w: [240, 300], hand: "fist", rot: -20 }, brows: "focused", tilt: 3 },
  wow: { L: { e: [56, 300], w: [96, 214], hand: "open", rot: -10 }, R: { e: [344, 300], w: [304, 214], hand: "open", rot: 10 },
    brows: "raised", tilt: 0 },
  present: { L: { e: [52, 392], w: [10, 352], hand: "open", rot: -75 }, R: IDLE_R, brows: "raised", tilt: -3 },
  peace: { L: IDLE_L, R: { e: [356, 302], w: [342, 218], hand: "peace", rot: 6 }, brows: "neutral", tilt: -2 },
  fist: { L: IDLE_L, R: { e: [352, 292], w: [336, 206], hand: "fist", rot: 0 }, brows: "focused", tilt: -2 },
};

const Arm: React.FC<{ s: [number, number]; def: ArmDef; side: "L" | "R" }> = ({ s, def, side }) => {
  const [ex, ey] = def.e, [wx, wy] = def.w;
  const ang = (Math.atan2(wy - ey, wx - ex) * 180) / Math.PI + 90 + (def.rot ?? 0);
  const d = `M${s[0]} ${s[1]} L${ex} ${ey} L${wx} ${wy}`;
  return (
    <g>
      <path d={d} stroke={OUT} strokeWidth={50} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d={d} stroke={NAVY} strokeWidth={44} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      {/* sleeve shading on the outer edge */}
      <path d={d} stroke={NAVY_SH} strokeWidth={14} fill="none" strokeLinecap="round" strokeLinejoin="round"
        transform={`translate(${side === "L" ? -9 : 9} 4)`} opacity={0.9} />
      {/* cuff */}
      <circle cx={wx} cy={wy} r={22} fill={NAVY_SH} stroke={OUT} strokeWidth={3} />
      <Hand type={def.hand} x={wx} y={wy} angle={ang} flip={side === "L"} />
    </g>
  );
};

/* ---------------------------------------------------------------- face parts */
const BROWS: Record<Brows, [string, string]> = {
  neutral: ["M146 136 Q168 128 188 134", "M212 134 Q232 128 254 136"],
  raised: ["M146 128 Q168 116 188 124", "M212 124 Q232 116 254 128"],
  worried: ["M148 132 Q168 130 188 122", "M212 122 Q232 130 252 132"],
  focused: ["M148 130 Q170 134 188 140", "M212 140 Q230 134 252 130"],
};

const Eye: React.FC<{ cx: number; blink: number; look: number }> = ({ cx, blink, look }) => {
  const cy = 178;
  if (blink >= 2) return <path d={`M${cx - 10} ${cy} Q${cx} ${cy + 6} ${cx + 10} ${cy}`} stroke={OUT} strokeWidth={3.5} fill="none" strokeLinecap="round" />;
  return (
    <g>
      <ellipse cx={cx + look} cy={cy} rx={7.5} ry={blink === 1 ? 4 : 9.5} fill="#24170F" />
      {blink === 0 ? <circle cx={cx + look - 2.5} cy={cy - 3.5} r={2.6} fill="#fff" /> : null}
      <path d={`M${cx - 11} ${cy - (blink === 1 ? 3 : 9)} Q${cx} ${cy - (blink === 1 ? 7 : 14)} ${cx + 11} ${cy - (blink === 1 ? 3 : 9)}`}
        stroke={OUT} strokeWidth={3} fill="none" strokeLinecap="round" />
    </g>
  );
};

const MOUTH_INNER = "#5B1D22", TONGUE = "#D7676B";
const Mouth: React.FC<{ v: Viseme }> = ({ v }) => {
  const cx = 200, cy = 228;
  switch (v) {
    case "mbp":
      return <path d={`M${cx - 15} ${cy} Q${cx} ${cy + 3} ${cx + 15} ${cy}`} stroke={OUT} strokeWidth={4} fill="none" strokeLinecap="round" />;
    case "ee":
      return (<g>
        <path d={`M${cx - 20} ${cy - 3} Q${cx} ${cy - 6} ${cx + 20} ${cy - 3} Q${cx + 16} ${cy + 11} ${cx} ${cy + 12} Q${cx - 16} ${cy + 11} ${cx - 20} ${cy - 3}Z`} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />
        <path d={`M${cx - 16} ${cy - 3} Q${cx} ${cy - 5} ${cx + 16} ${cy - 3} L${cx + 14} ${cy + 2} Q${cx} ${cy + 1} ${cx - 14} ${cy + 2}Z`} fill="#fff" />
      </g>);
    case "aa":
      return (<g>
        <path d={`M${cx - 15} ${cy - 5} Q${cx} ${cy - 8} ${cx + 15} ${cy - 5} Q${cx + 14} ${cy + 18} ${cx} ${cy + 21} Q${cx - 14} ${cy + 18} ${cx - 15} ${cy - 5}Z`} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />
        <path d={`M${cx - 12} ${cy - 5} Q${cx} ${cy - 7} ${cx + 12} ${cy - 5} L${cx + 11} ${cy - 1} Q${cx} ${cy - 2} ${cx - 11} ${cy - 1}Z`} fill="#fff" />
        <ellipse cx={cx} cy={cy + 14} rx={9} ry={5} fill={TONGUE} />
      </g>);
    case "oh":
      return (<g>
        <ellipse cx={cx} cy={cy + 4} rx={11} ry={13} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />
        <ellipse cx={cx} cy={cy + 11} rx={6} ry={3.5} fill={TONGUE} />
      </g>);
    case "eh":
      return (<g>
        <path d={`M${cx - 18} ${cy - 3} Q${cx} ${cy - 6} ${cx + 18} ${cy - 3} Q${cx + 15} ${cy + 13} ${cx} ${cy + 14} Q${cx - 15} ${cy + 13} ${cx - 18} ${cy - 3}Z`} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />
        <path d={`M${cx - 14} ${cy - 3} Q${cx} ${cy - 5} ${cx + 14} ${cy - 3} L${cx + 12} ${cy + 1} Q${cx} ${cy} ${cx - 12} ${cy + 1}Z`} fill="#fff" />
        <ellipse cx={cx} cy={cy + 9} rx={7} ry={3.5} fill={TONGUE} />
      </g>);
    case "fv":
      return (<g>
        <path d={`M${cx - 17} ${cy - 2} Q${cx} ${cy - 5} ${cx + 17} ${cy - 2} Q${cx + 13} ${cy + 7} ${cx} ${cy + 8} Q${cx - 13} ${cy + 7} ${cx - 17} ${cy - 2}Z`} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />
        <path d={`M${cx - 13} ${cy - 2} Q${cx} ${cy - 4} ${cx + 13} ${cy - 2} L${cx + 12} ${cy + 3} Q${cx} ${cy + 2} ${cx - 12} ${cy + 3}Z`} fill="#fff" />
        <path d={`M${cx - 15} ${cy + 5} Q${cx} ${cy + 1} ${cx + 15} ${cy + 5}`} stroke={OUT} strokeWidth={3} fill="none" strokeLinecap="round" />
      </g>);
    case "l":
      return (<g>
        <path d={`M${cx - 16} ${cy - 4} Q${cx} ${cy - 7} ${cx + 16} ${cy - 4} Q${cx + 14} ${cy + 15} ${cx} ${cy + 16} Q${cx - 14} ${cy + 15} ${cx - 16} ${cy - 4}Z`} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />
        <path d={`M${cx - 12} ${cy - 4} Q${cx} ${cy - 6} ${cx + 12} ${cy - 4} L${cx + 11} ${cy} Q${cx} ${cy - 1} ${cx - 11} ${cy}Z`} fill="#fff" />
        <path d={`M${cx - 7} ${cy + 12} Q${cx} ${cy + 1} ${cx + 7} ${cy + 12}Z`} fill={TONGUE} />
      </g>);
    case "uw":
      return <ellipse cx={cx} cy={cy + 2} rx={7} ry={8} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />;
    case "smile":
      return (<g>
        <path d={`M${cx - 22} ${cy - 4} Q${cx} ${cy - 2} ${cx + 22} ${cy - 4} Q${cx + 14} ${cy + 16} ${cx} ${cy + 17} Q${cx - 14} ${cy + 16} ${cx - 22} ${cy - 4}Z`} fill={MOUTH_INNER} stroke={OUT} strokeWidth={3} />
        <path d={`M${cx - 18} ${cy - 3} Q${cx} ${cy - 1} ${cx + 18} ${cy - 3} L${cx + 15} ${cy + 3} Q${cx} ${cy + 4} ${cx - 15} ${cy + 3}Z`} fill="#fff" />
      </g>);
    default: // rest: closed gentle smile
      return <path d={`M${cx - 16} ${cy - 2} Q${cx} ${cy + 8} ${cx + 16} ${cy - 2}`} stroke={OUT} strokeWidth={4} fill="none" strokeLinecap="round" />;
  }
};

/* ---------------------------------------------------------------- hair */
const CURLS_BACK: [number, number, number][] = [
  [128, 150, 26], [140, 118, 28], [165, 96, 30], [200, 86, 32], [236, 96, 30], [260, 118, 28], [272, 150, 26],
  [122, 182, 20], [278, 182, 20],
];
const CURLS_FRONT: [number, number, number][] = [
  [150, 112, 22], [176, 100, 22], [204, 98, 23], [230, 104, 22], [252, 118, 20], [138, 134, 16], [262, 138, 15],
];
const Hair: React.FC<{ front?: boolean }> = ({ front }) => {
  const set = front ? CURLS_FRONT : CURLS_BACK;
  return (
    <g>
      {set.map(([x, y, r], i) => <circle key={"o" + i} cx={x} cy={y} r={r + 3} fill={OUT} />)}
      {set.map(([x, y, r], i) => <circle key={"f" + i} cx={x} cy={y} r={r} fill={HAIR} />)}
      {set.map(([x, y, r], i) => <circle key={"s" + i} cx={x + r * 0.25} cy={y + r * 0.3} r={r * 0.6} fill={HAIR_SH} />)}
      {set.map(([x, y, r], i) => (
        <path key={"h" + i} d={`M${x - r * 0.55} ${y - r * 0.2} Q${x - r * 0.3} ${y - r * 0.7} ${x + r * 0.2} ${y - r * 0.65}`}
          stroke={HAIR_HI} strokeWidth={3} fill="none" strokeLinecap="round" />
      ))}
    </g>
  );
};

/* ---------------------------------------------------------------- body */
const TORSO = "M58 528 L66 372 Q74 306 150 292 L250 292 Q326 306 334 372 L342 528 Z";

export const Nova: React.FC<{
  pose: Pose; viseme?: Viseme; blink?: 0 | 1 | 2; brows?: Brows;
  headTilt?: number; headNod?: number; breathe?: number; look?: number;
}> = ({ pose, viseme = "rest", blink = 0, brows, headTilt = 0, headNod = 0, breathe = 0, look = 0 }) => {
  const P = POSES[pose];
  const b = brows ?? P.brows;
  const tilt = P.tilt + headTilt;
  return (
    <svg viewBox="0 0 400 520" style={{ width: "100%", height: "100%", overflow: "visible" }}>
      <defs>
        <clipPath id="torsoClip"><path d={TORSO} /></clipPath>
      </defs>
      <g transform={`translate(0 ${-breathe * 2}) scale(1 ${1 + breathe * 0.006})`} style={{ transformOrigin: "200px 520px" }}>
        {/* torso */}
        <path d={TORSO} fill={NAVY} stroke={OUT} strokeWidth={3.5} strokeLinejoin="round" />
        <g clipPath="url(#torsoClip)">
          <path d="M262 292 Q330 306 336 372 L346 528 L282 528 Q300 420 262 292Z" fill={NAVY_SH} />
          <path d="M96 330 Q110 304 150 296 Q118 318 112 360Z" fill={NAVY_HI} opacity={0.7} />
          <rect x={40} y={392} width={320} height={26} fill={STRIPE} />
          <rect x={40} y={412} width={320} height={6} fill={STRIPE_SH} />
          <path d="M282 392 L360 392 L360 418 L290 418Z" fill={STRIPE_SH} opacity={0.6} />
        </g>
        {/* neck */}
        <path d="M178 238 L178 296 Q200 310 222 296 L222 238Z" fill={SKIN_SH} stroke={OUT} strokeWidth={3} />
        {/* hood collar */}
        <path d="M134 300 Q150 280 178 286 Q200 316 222 286 Q250 280 266 300 Q238 340 200 342 Q162 340 134 300Z"
          fill={NAVY_SH} stroke={OUT} strokeWidth={3} strokeLinejoin="round" />
        {/* drawstrings */}
        {[[186, 330, 180, 384], [214, 330, 220, 384]].map(([x1, y1, x2, y2], i) => (
          <g key={i}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={OUT} strokeWidth={7} strokeLinecap="round" />
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={STRING} strokeWidth={4} strokeLinecap="round" />
            <rect x={x2 - 4} y={y2 - 2} width={8} height={14} rx={3} fill="#9AA0AA" stroke={OUT} strokeWidth={2} />
          </g>
        ))}

        {/* head */}
        <g transform={`rotate(${tilt} 200 270) translate(0 ${headNod * 3})`}>
          <Hair />
          <ellipse cx={130} cy={180} rx={13} ry={19} fill={SKIN} stroke={OUT} strokeWidth={3} />
          <ellipse cx={270} cy={180} rx={13} ry={19} fill={SKIN_SH} stroke={OUT} strokeWidth={3} />
          <path d="M130 165 Q130 96 200 92 Q270 96 270 165 Q270 214 240 241 Q221 257 200 258 Q179 257 160 241 Q130 214 130 165Z"
            fill={SKIN} stroke={OUT} strokeWidth={3.5} />
          <path d="M252 150 Q272 172 262 206 Q250 238 216 254 Q242 226 248 196 Q252 172 252 150Z" fill={SKIN_SH} opacity={0.8} />
          <ellipse cx={160} cy={214} rx={13} ry={7} fill={BLUSH} opacity={0.38} />
          <ellipse cx={240} cy={214} rx={13} ry={7} fill={BLUSH} opacity={0.38} />
          <path d="M201 186 Q208 202 198 208" stroke={SKIN_SH} strokeWidth={3.5} fill="none" strokeLinecap="round" />
          <Hair front />
          {/* brows */}
          {BROWS[b].map((d, i) => <path key={i} d={d} stroke={HAIR_SH} strokeWidth={6.5} fill="none" strokeLinecap="round" />)}
          {/* eyes behind lenses */}
          <Eye cx={170} blink={blink} look={look} />
          <Eye cx={230} blink={blink} look={look} />
          {/* glasses */}
          <path d="M144 172 L132 168 M256 172 L268 168" stroke={OUT} strokeWidth={4} strokeLinecap="round" />
          {[170, 230].map((cx) => (
            <g key={cx}>
              <circle cx={cx} cy={178} r={27} fill="rgba(224,163,62,0.20)" stroke={OUT} strokeWidth={5} />
              <circle cx={cx} cy={178} r={27} fill="none" stroke="#3A3440" strokeWidth={2} />
              <path d={`M${cx - 16} ${165} Q${cx - 6} ${156} ${cx + 6} ${158}`} stroke="#fff" strokeWidth={3.5} fill="none" strokeLinecap="round" opacity={0.75} />
            </g>
          ))}
          <path d="M197 176 Q200 170 203 176" stroke={OUT} strokeWidth={4} fill="none" strokeLinecap="round" />
          <Mouth v={viseme} />
        </g>

        {/* arms in front */}
        <Arm s={SHOULDER_L} def={P.L} side="L" />
        <Arm s={SHOULDER_R} def={P.R} side="R" />
      </g>
    </svg>
  );
};
