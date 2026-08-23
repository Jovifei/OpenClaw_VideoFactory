import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type RcHighPassScene = {
  start_seconds: number;
  end_seconds: number;
  heading: string;
  visual_kind: 'hook' | 'topology' | 'bode' | 'phasor' | 'summary';
  timing_segment_index?: number;
};

export type RcHighPassVisualInput = {
  schema_version: '1.0';
  title: string;
  duration_seconds: number;
  fps: 30;
  scenes: RcHighPassScene[];
  layout_contract_version: '1.0';
};

const THEME = {
  canvas: '#F2F1EE',
  panel: '#FFFFFF',
  ink: '#1F2228',
  muted: '#6D7179',
  mint: '#54C989',
  orange: '#E89A44',
  violet: '#7668C6',
  rule: '#D9D7D2',
  soft: '#E9E8E4',
} as const;

const SAFE = {left: 72, right: 72, top: 68, bottom: 180};
const WIDTH = 1080;
const CONTENT_WIDTH = WIDTH - SAFE.left - SAFE.right;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

type BoundedTextProps = {
  id: string;
  children: React.ReactNode;
  size: number;
  color?: string;
  weight?: number;
  maxWidth?: number;
  lines?: number;
  lineHeight?: number;
  style?: React.CSSProperties;
};

const BoundedText: React.FC<BoundedTextProps> = ({
  id,
  children,
  size,
  color = THEME.ink,
  weight = 800,
  maxWidth = CONTENT_WIDTH,
  lines = 2,
  lineHeight = 1.18,
  style,
}) => {
  const boundedStyle = {
    display: '-webkit-box',
    WebkitBoxOrient: 'vertical',
    WebkitLineClamp: lines,
    overflow: 'hidden',
    overflowWrap: 'break-word',
  } as React.CSSProperties;
  return (
    <div
      data-layout-box={id}
      data-layout-lines={lines}
      style={{
        maxWidth,
        maxHeight: size * lineHeight * lines,
        fontSize: size,
        lineHeight,
        fontWeight: weight,
        color,
        ...boundedStyle,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const Badge: React.FC<{id: string; children: React.ReactNode; color?: string}> = ({id, children, color = THEME.ink}) => (
  <div
    data-layout-box={id}
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      alignSelf: 'flex-start',
      maxWidth: CONTENT_WIDTH,
      minHeight: 42,
      padding: '8px 18px',
      boxSizing: 'border-box',
      borderRadius: 999,
      background: `${color}16`,
      color,
      fontSize: 21,
      fontWeight: 900,
      letterSpacing: 1.1,
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
    }}
  >
    {children}
  </div>
);

const Card: React.FC<{children: React.ReactNode; accent?: string; style?: React.CSSProperties}> = ({children, accent = THEME.rule, style}) => (
  <div
    style={{
      background: THEME.panel,
      border: `2px solid ${THEME.rule}`,
      borderTop: `8px solid ${accent}`,
      borderRadius: 24,
      boxShadow: '0 16px 36px rgba(46,43,36,0.08)',
      boxSizing: 'border-box',
      overflow: 'hidden',
      ...style,
    }}
  >
    {children}
  </div>
);

const Arrow: React.FC<{x1: number; x2: number; y: number; color?: string}> = ({x1, x2, y, color = THEME.ink}) => (
  <g>
    <line x1={x1} y1={y} x2={x2 - 18} y2={y} stroke={color} strokeWidth={5} strokeLinecap="round" />
    <path d={`M ${x2 - 26} ${y - 11} L ${x2} ${y} L ${x2 - 26} ${y + 11}`} fill="none" stroke={color} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" />
  </g>
);

const HookDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const pulse = interpolate((frame % (2 * fps)) / fps, [0, 1, 2], [0.98, 1.04, 0.98], clamp);
  return (
    <Card accent={THEME.mint} style={{height: 1040, padding: 34}}>
      <BoundedText id="hook-card-label" size={22} color={THEME.muted} weight={900} lines={1}>WHY HIGH-PASS?</BoundedText>
      <BoundedText id="hook-card-title" size={35} weight={900} lines={2} maxWidth={800} style={{marginTop: 22}}>变化通过，稳态被挡住</BoundedText>
      <svg viewBox="0 0 860 620" width="100%" height="620" role="img" aria-label="RC high pass hook diagram" style={{marginTop: 36, overflow: 'visible'}}>
        <circle cx="122" cy="280" r="24" fill={THEME.panel} stroke={THEME.ink} strokeWidth="6" />
        <text data-layout-box="hook-vin" x="74" y="350" fill={THEME.ink} fontSize="26" fontWeight="800">Vin</text>
        <line x1="146" y1="280" x2="278" y2="280" stroke={THEME.ink} strokeWidth="8" strokeLinecap="round" />
        <line x1="304" y1="194" x2="304" y2="366" stroke={THEME.mint} strokeWidth="10" strokeLinecap="round" />
        <line x1="350" y1="194" x2="350" y2="366" stroke={THEME.mint} strokeWidth="10" strokeLinecap="round" />
        <line x1="278" y1="280" x2="304" y2="280" stroke={THEME.ink} strokeWidth="8" />
        <line x1="350" y1="280" x2="540" y2="280" stroke={THEME.ink} strokeWidth="8" />
        <line x1="540" y1="280" x2="540" y2="410" stroke={THEME.ink} strokeWidth="8" />
        <rect x="490" y="410" width="100" height="122" rx="18" fill={THEME.panel} stroke={THEME.orange} strokeWidth="8" transform={`scale(${pulse}) translate(${540 * (1 - pulse) / pulse}, ${470 * (1 - pulse) / pulse})`} />
        <text data-layout-box="hook-r" x="530" y="485" fill={THEME.orange} fontSize="32" fontWeight="900">R</text>
        <line x1="540" y1="532" x2="540" y2="574" stroke={THEME.ink} strokeWidth="8" />
        <path d="M 490 574 H 590 M 505 588 H 575 M 522 602 H 558" stroke={THEME.ink} strokeWidth="7" strokeLinecap="round" />
        <circle cx="738" cy="280" r="24" fill={THEME.panel} stroke={THEME.ink} strokeWidth="6" />
        <line x1="540" y1="280" x2="714" y2="280" stroke={THEME.ink} strokeWidth="8" strokeLinecap="round" />
        <text data-layout-box="hook-vout" x="694" y="350" fill={THEME.ink} fontSize="26" fontWeight="800">Vout</text>
        <path d="M 155 110 C 215 45, 275 175, 335 110 S 455 175, 515 110 S 635 175, 695 110" fill="none" stroke={THEME.mint} strokeWidth="9" strokeLinecap="round" opacity="0.9" />
        <path d="M 155 150 C 215 85, 275 215, 335 150 S 455 215, 515 150 S 635 215, 695 150" fill="none" stroke={THEME.orange} strokeWidth="7" strokeLinecap="round" opacity="0.55" />
        <text data-layout-box="hook-low-high" x="166" y="86" fill={THEME.muted} fontSize="22" fontWeight="800">低频：容抗大</text>
        <text data-layout-box="hook-fast" x="580" y="86" fill={THEME.mint} fontSize="22" fontWeight="900">快速变化：通过</text>
      </svg>
      <div style={{display: 'flex', gap: 16, marginTop: 16}}>
        <Card accent={THEME.orange} style={{flex: 1, height: 178, padding: 22}}>
          <BoundedText id="hook-steady-label" size={18} color={THEME.muted} lines={1}>STEADY STATE</BoundedText>
          <BoundedText id="hook-steady" size={28} weight={900} lines={2} style={{marginTop: 18}}>直流被挡住</BoundedText>
        </Card>
        <Card accent={THEME.mint} style={{flex: 1, height: 178, padding: 22}}>
          <BoundedText id="hook-change-label" size={18} color={THEME.muted} lines={1}>CHANGE</BoundedText>
          <BoundedText id="hook-change" size={28} weight={900} lines={2} style={{marginTop: 18}}>变化被保留</BoundedText>
        </Card>
      </div>
    </Card>
  );
};

const TopologyDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const reveal = interpolate(frame, [0, 45], [0, 1], clamp);
  return (
    <Card accent={THEME.violet} style={{height: 1120, padding: 34}}>
      <BoundedText id="topology-label" size={22} color={THEME.muted} weight={900} lines={1}>TOPOLOGY & SIGNAL PATH</BoundedText>
      <BoundedText id="topology-title" size={34} weight={900} lines={2} maxWidth={800} style={{marginTop: 20}}>串联电容，分压取输出</BoundedText>
      <svg viewBox="0 0 860 660" width="100%" height="660" role="img" aria-label="RC high pass topology" style={{marginTop: 30}}>
        <line x1="70" y1="300" x2="245" y2="300" stroke={THEME.ink} strokeWidth="8" strokeLinecap="round" />
        <circle cx="70" cy="300" r="22" fill={THEME.panel} stroke={THEME.ink} strokeWidth="6" />
        <text data-layout-box="topology-vin" x="46" y="365" fill={THEME.ink} fontSize="26" fontWeight="900">Vin</text>
        <line x1="270" y1="215" x2="270" y2="385" stroke={THEME.mint} strokeWidth="10" strokeLinecap="round" />
        <line x1="316" y1="215" x2="316" y2="385" stroke={THEME.mint} strokeWidth="10" strokeLinecap="round" />
        <line x1="245" y1="300" x2="270" y2="300" stroke={THEME.ink} strokeWidth="8" />
        <line x1="316" y1="300" x2="535" y2="300" stroke={THEME.ink} strokeWidth="8" />
        <text data-layout-box="topology-c" x="270" y="180" fill={THEME.mint} fontSize="32" fontWeight="900">C</text>
        <line x1="535" y1="300" x2="535" y2="430" stroke={THEME.ink} strokeWidth="8" />
        <rect x="485" y="430" width="100" height="120" rx="18" fill={THEME.panel} stroke={THEME.orange} strokeWidth="8" />
        <text data-layout-box="topology-r" x="525" y="507" fill={THEME.orange} fontSize="32" fontWeight="900">R</text>
        <line x1="535" y1="550" x2="535" y2="598" stroke={THEME.ink} strokeWidth="8" />
        <path d="M 485 598 H 585 M 500 612 H 570 M 518 626 H 552" stroke={THEME.ink} strokeWidth="7" strokeLinecap="round" />
        <circle cx="765" cy="300" r="22" fill={THEME.panel} stroke={THEME.ink} strokeWidth="6" />
        <line x1="535" y1="300" x2="743" y2="300" stroke={THEME.ink} strokeWidth="8" strokeLinecap="round" />
        <text data-layout-box="topology-vout" x="710" y="365" fill={THEME.ink} fontSize="26" fontWeight="900">Vout</text>
        <Arrow x1={110} x2={220} y={160} color={THEME.mint} />
        <text data-layout-box="topology-low" x="110" y="110" fill={THEME.muted} fontSize="22" fontWeight="800">低频：XC 大</text>
        <Arrow x1={600} x2={750} y={160} color={THEME.orange} />
        <text data-layout-box="topology-high" x="560" y="110" fill={THEME.orange} fontSize="22" fontWeight="900">高频：XC 小</text>
        <path d="M 120 470 C 195 410, 260 530, 335 470 S 475 530, 550 470 S 690 530, 760 470" fill="none" stroke={THEME.mint} strokeWidth="8" strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - reveal} pathLength={1} />
        <text data-layout-box="topology-wave" x="138" y="545" fill={THEME.muted} fontSize="21" fontWeight="800">输出逐渐跟随输入</text>
      </svg>
      <div style={{display: 'flex', gap: 18}}>
        <Card accent={THEME.orange} style={{flex: 1, height: 170, padding: 22}}>
          <BoundedText id="topology-frequency" size={22} color={THEME.muted} lines={1}>LOW FREQUENCY</BoundedText>
          <BoundedText id="topology-frequency-copy" size={26} lines={2} style={{marginTop: 16}}>电容像高阻</BoundedText>
        </Card>
        <Card accent={THEME.mint} style={{flex: 1, height: 170, padding: 22}}>
          <BoundedText id="topology-frequency-high" size={22} color={THEME.muted} lines={1}>HIGH FREQUENCY</BoundedText>
          <BoundedText id="topology-frequency-high-copy" size={26} lines={2} style={{marginTop: 16}}>电容像低阻</BoundedText>
        </Card>
      </div>
    </Card>
  );
};

const makeCurve = (phase = false): string => {
  const points: string[] = [];
  for (let i = 0; i <= 80; i += 1) {
    const x = 92 + (i / 80) * 700;
    const logRatio = -1 + (i / 80) * 2;
    const ratio = 10 ** logRatio;
    const value = phase ? Math.atan(1 / ratio) * (180 / Math.PI) : 20 * Math.log10(ratio / Math.sqrt(1 + ratio * ratio));
    const y = phase ? 520 - ((value / 90) * 330) : 390 - (((value + 20) / 20) * 300);
    points.push(`${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`);
  }
  return points.join(' ');
};

const BodeDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const reveal = interpolate(frame, [0, 54], [1, 0], clamp);
  const pulse = 1 + Math.sin(frame / fps) * 0.04;
  return (
    <Card accent={THEME.orange} style={{height: 1180, padding: 30}}>
      <BoundedText id="bode-label" size={22} color={THEME.muted} weight={900} lines={1}>CUTOFF & PHASE LEAD</BoundedText>
      <BoundedText id="bode-title" size={34} weight={900} lines={2} maxWidth={800} style={{marginTop: 20}}>fc 是幅度和相位的分水岭</BoundedText>
      <svg viewBox="0 0 860 780" width="100%" height="780" role="img" aria-label="Bode magnitude and phase curves" style={{marginTop: 26}}>
        <rect x="58" y="34" width="744" height="680" rx="24" fill={THEME.panel} stroke={THEME.rule} strokeWidth="3" />
        {[120, 205, 290, 375, 460, 545, 630].map((y) => <line key={y} x1="118" y1={y} x2="754" y2={y} stroke={THEME.soft} strokeWidth="3" />)}
        <line x1="118" y1="76" x2="118" y2="660" stroke={THEME.rule} strokeWidth="4" />
        <line x1="118" y1="660" x2="754" y2="660" stroke={THEME.rule} strokeWidth="4" />
        <path d={makeCurve(false)} fill="none" stroke={THEME.mint} strokeWidth="9" strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={reveal} />
        <path d={makeCurve(true)} fill="none" stroke={THEME.orange} strokeWidth="9" strokeLinecap="round" pathLength={1} strokeDasharray="1" strokeDashoffset={reveal} />
        <line x1="436" y1="72" x2="436" y2="660" stroke={THEME.violet} strokeWidth="5" strokeDasharray="12 10" />
        <circle cx="436" cy="275" r={15 * pulse} fill={THEME.mint} />
        <circle cx="436" cy="445" r={15 * pulse} fill={THEME.orange} />
        <text data-layout-box="bode-0db" x="70" y="112" fill={THEME.muted} fontSize="20" fontWeight="800">0 dB</text>
        <text data-layout-box="bode-3db" x="70" y="285" fill={THEME.muted} fontSize="20" fontWeight="800">-3 dB</text>
        <text data-layout-box="bode-phase-90" x="65" y="210" fill={THEME.orange} fontSize="20" fontWeight="900">+90°</text>
        <text data-layout-box="bode-phase-45" x="65" y="375" fill={THEME.orange} fontSize="20" fontWeight="900">+45°</text>
        <text data-layout-box="bode-phase-0" x="72" y="540" fill={THEME.orange} fontSize="20" fontWeight="900">0°</text>
        <text data-layout-box="bode-fc" x="398" y="700" fill={THEME.violet} fontSize="22" fontWeight="900">fc</text>
        <text data-layout-box="bode-low" x="124" y="700" fill={THEME.muted} fontSize="19" fontWeight="800">0.1 fc</text>
        <text data-layout-box="bode-high" x="704" y="700" fill={THEME.muted} fontSize="19" fontWeight="800">10 fc</text>
        <text data-layout-box="bode-green" x="566" y="170" fill={THEME.mint} fontSize="20" fontWeight="900">幅频</text>
        <text data-layout-box="bode-orange" x="566" y="205" fill={THEME.orange} fontSize="20" fontWeight="900">相频</text>
      </svg>
      <div style={{display: 'flex', gap: 14}}>
        <Card accent={THEME.mint} style={{flex: 1, height: 164, padding: 20}}>
          <BoundedText id="bode-gain-copy" size={23} lines={2}>fc 处约 -3 dB</BoundedText>
        </Card>
        <Card accent={THEME.orange} style={{flex: 1, height: 164, padding: 20}}>
          <BoundedText id="bode-phase-copy" size={23} lines={2}>fc 处约 +45°</BoundedText>
        </Card>
      </div>
    </Card>
  );
};

const PhasorDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const angle = interpolate((frame % (3 * fps)) / fps, [0, 3], [0.25, 0.78], clamp);
  const waveShift = Math.sin(frame / fps) * 14;
  return (
    <Card accent={THEME.violet} style={{height: 1120, padding: 30}}>
      <BoundedText id="phasor-label" size={22} color={THEME.muted} weight={900} lines={1}>PHASOR & TIME CONSTANT</BoundedText>
      <BoundedText id="phasor-title" size={34} weight={900} lines={2} maxWidth={820} style={{marginTop: 20}}>相位超前，就是时间位移</BoundedText>
      <svg viewBox="0 0 860 680" width="100%" height="680" role="img" aria-label="phasor and waveform diagram" style={{marginTop: 30}}>
        <circle cx="250" cy="300" r="150" fill="none" stroke={THEME.rule} strokeWidth="4" />
        <line x1="90" y1="300" x2="410" y2="300" stroke={THEME.rule} strokeWidth="3" />
        <line x1="250" y1="140" x2="250" y2="460" stroke={THEME.rule} strokeWidth="3" />
        <line x1="250" y1="300" x2={250 + 140 * Math.cos(angle)} y2={300 - 140 * Math.sin(angle)} stroke={THEME.orange} strokeWidth="10" strokeLinecap="round" />
        <circle cx={250 + 140 * Math.cos(angle)} cy={300 - 140 * Math.sin(angle)} r="13" fill={THEME.orange} />
        <text data-layout-box="phasor-vin" x="270" y="332" fill={THEME.muted} fontSize="22" fontWeight="800">Vin</text>
        <text data-layout-box="phasor-vout" x="282" y="175" fill={THEME.orange} fontSize="22" fontWeight="900">Vout 超前</text>
        <text data-layout-box="phasor-angle" x="300" y="280" fill={THEME.orange} fontSize="20" fontWeight="900">+45°</text>
        <rect x="470" y="110" width="310" height="382" rx="22" fill={THEME.soft} />
        <line x1="500" y1="300" x2="750" y2="300" stroke={THEME.rule} strokeWidth="3" />
        <path d={`M 500 300 C 540 ${250 + waveShift}, 580 ${350 + waveShift}, 620 300 S 700 ${250 + waveShift}, 750 300`} fill="none" stroke={THEME.muted} strokeWidth="6" strokeDasharray="12 9" />
        <path d={`M 500 300 C 540 ${250 - waveShift}, 580 ${350 - waveShift}, 620 300 S 700 ${250 - waveShift}, 750 300`} fill="none" stroke={THEME.mint} strokeWidth="8" />
        <text data-layout-box="phasor-input" x="504" y="170" fill={THEME.muted} fontSize="19" fontWeight="800">输入 Vin</text>
        <text data-layout-box="phasor-output" x="632" y="170" fill={THEME.mint} fontSize="19" fontWeight="900">输出 Vout</text>
        <text data-layout-box="phasor-shift" x="510" y="440" fill={THEME.orange} fontSize="19" fontWeight="900">波峰左移：相位超前</text>
        <line x1="120" y1="570" x2="740" y2="570" stroke={THEME.violet} strokeWidth="8" strokeLinecap="round" />
        <circle cx={120 + ((frame % (4 * fps)) / (4 * fps)) * 620} cy="570" r="16" fill={THEME.violet} />
        <text data-layout-box="phasor-tau" x="120" y="630" fill={THEME.violet} fontSize="26" fontWeight="900">τ = RC：时间尺度</text>
      </svg>
      <div style={{display: 'flex', gap: 14}}>
        <Card accent={THEME.violet} style={{flex: 1, height: 160, padding: 20}}>
          <BoundedText id="phasor-transient" size={22} lines={2}>瞬态先变化</BoundedText>
        </Card>
        <Card accent={THEME.orange} style={{flex: 1, height: 160, padding: 20}}>
          <BoundedText id="phasor-boundary" size={22} lines={2}>边缘频率最值得看</BoundedText>
        </Card>
      </div>
    </Card>
  );
};

const SummaryDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const active = Math.min(2, Math.floor((frame / fps) % 3));
  const items = [
    ['分水岭', 'fc = 1/(2πRC)', THEME.mint],
    ['超前角', 'fc 处约 +45°', THEME.orange],
    ['时间尺度', 'τ = RC', THEME.violet],
  ] as const;
  return (
    <Card accent={THEME.mint} style={{height: 1120, padding: 30}}>
      <BoundedText id="summary-label" size={22} color={THEME.muted} weight={900} lines={1}>MASTER MATRIX & NEXT PREVIEW</BoundedText>
      <BoundedText id="summary-title" size={34} weight={900} lines={2} maxWidth={840} style={{marginTop: 20}}>三个轴，掌握动态滤波</BoundedText>
      <div style={{display: 'flex', gap: 14, marginTop: 42}}>
        {items.map(([label, value, color], index) => (
          <Card key={label} accent={index === active ? color : THEME.rule} style={{flex: 1, height: 360, padding: 20, transform: `translateY(${index === active ? -10 : 0}px)`}}>
            <BoundedText id={`summary-label-${index}`} size={19} color={color} lines={1}>{label}</BoundedText>
            <BoundedText id={`summary-value-${index}`} size={25} weight={900} lines={2} style={{marginTop: 36}}>{value}</BoundedText>
            <BoundedText id={`summary-copy-${index}`} size={19} color={THEME.muted} lines={3} style={{marginTop: 32}}>{index === 0 ? '截止频率决定分水岭' : index === 1 ? '相位告诉你时间位移' : 'RC 决定变化速度'}</BoundedText>
          </Card>
        ))}
      </div>
      <Card accent={THEME.violet} style={{height: 450, marginTop: 28, padding: 24}}>
        <BoundedText id="next-label" size={20} color={THEME.violet} lines={1}>NEXT EPISODE</BoundedText>
        <BoundedText id="next-title" size={28} weight={900} lines={2} maxWidth={780} style={{marginTop: 22}}>RL 与 LC：把相位直觉带到更高阶网络</BoundedText>
        <svg viewBox="0 0 760 190" width="100%" height="190" style={{marginTop: 24}}>
          <path d="M 70 110 H 230 C 260 50, 290 50, 320 110 C 350 170, 380 170, 410 110 C 440 50, 470 50, 500 110 H 690" fill="none" stroke={THEME.violet} strokeWidth="9" strokeLinecap="round" />
          <text data-layout-box="next-l" x="350" y="56" fill={THEME.violet} fontSize="30" fontWeight="900">L</text>
        </svg>
        <BoundedText id="next-copy" size={21} color={THEME.muted} lines={2}>先看拓扑，再看频率响应，最后验证边界。</BoundedText>
      </Card>
    </Card>
  );
};

const SceneDiagram: React.FC<{kind: RcHighPassScene['visual_kind']; frame: number; fps: number}> = ({kind, frame, fps}) => {
  if (kind === 'hook') return <HookDiagram frame={frame} fps={fps} />;
  if (kind === 'topology') return <TopologyDiagram frame={frame} fps={fps} />;
  if (kind === 'bode') return <BodeDiagram frame={frame} fps={fps} />;
  if (kind === 'phasor') return <PhasorDiagram frame={frame} fps={fps} />;
  return <SummaryDiagram frame={frame} fps={fps} />;
};

const ACT_LABELS = ['ACT 01 / WHY HIGH-PASS', 'ACT 02 / TOPOLOGY', 'ACT 03 / CUTOFF & PHASE', 'ACT 04 / PHASOR & TIME', 'ACT 05 / SUMMARY'];

export const ReferenceRcHighPassVisual: React.FC<RcHighPassVisualInput> = (input) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;
  const currentIndex = Math.max(0, input.scenes.findIndex((scene) => seconds >= scene.start_seconds && seconds < scene.end_seconds));
  const scene = input.scenes[currentIndex] ?? input.scenes[input.scenes.length - 1];
  const localFrame = Math.max(0, frame - Math.round(scene.start_seconds * fps));
  const sceneDurationFrames = Math.max(1, Math.round((scene.end_seconds - scene.start_seconds) * fps));
  const entrance = interpolate(localFrame, [0, 24], [28, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)});
  const entranceOpacity = spring({frame: localFrame, fps, config: {damping: 200}});
  const exitOpacity = interpolate(localFrame, [Math.max(0, sceneDurationFrames - 15), sceneDurationFrames], [1, 0.9], clamp);
  const opacity = entranceOpacity * exitOpacity;
  const progress = interpolate(seconds, [0, input.duration_seconds], [0, 100], clamp);
  const accent = [THEME.mint, THEME.violet, THEME.orange, THEME.violet, THEME.mint][currentIndex] ?? THEME.mint;

  return (
    <AbsoluteFill style={{background: THEME.canvas, color: THEME.ink, fontFamily: 'Microsoft YaHei UI, Microsoft YaHei, sans-serif', overflow: 'hidden'}} data-layout-contract="rc-highpass-1.0">
      <div style={{position: 'absolute', inset: 0, background: `radial-gradient(circle at 92% 9%, ${THEME.mint}18, transparent 24%), radial-gradient(circle at 7% 89%, ${THEME.violet}12, transparent 22%)`}} />
      <div style={{position: 'absolute', left: SAFE.left, right: SAFE.right, top: SAFE.top, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12}}>
        <Badge id="header-brand">HARDCORE CIRCUITS · ORIGINAL</Badge>
        <Badge id="header-act" color={accent}>{ACT_LABELS[currentIndex] ?? ACT_LABELS[0]}</Badge>
      </div>
      <div style={{position: 'absolute', left: SAFE.left, right: SAFE.right, top: 142}}>
        <BoundedText id="main-title" size={54} weight={950} maxWidth={CONTENT_WIDTH} lines={2} lineHeight={1.15}>{input.title}</BoundedText>
        <BoundedText id="scene-heading" size={27} color={THEME.muted} weight={800} maxWidth={CONTENT_WIDTH} lines={2} lineHeight={1.2} style={{marginTop: 18}}>{scene.heading}</BoundedText>
      </div>
      <div style={{position: 'absolute', left: SAFE.left, right: SAFE.right, top: 316, height: 8, borderRadius: 4, background: THEME.rule}}>
        <div style={{height: '100%', width: `${progress}%`, borderRadius: 4, background: accent}} />
      </div>
      <div style={{position: 'absolute', left: SAFE.left, right: SAFE.right, top: 370, bottom: SAFE.bottom + 18, opacity, transform: `translateY(${entrance}px)`, overflow: 'hidden'}}>
        <SceneDiagram kind={scene.visual_kind} frame={localFrame} fps={fps} />
      </div>
      <div style={{position: 'absolute', left: SAFE.left, right: SAFE.right, bottom: 56, display: 'flex', justifyContent: 'space-between', color: THEME.muted, fontSize: 16, fontWeight: 800}} data-layout-box="footer-meta">
        <span>原创电路图 · 画面无烧录字幕</span>
        <span>Jianying 原生字幕后置 · mascot_mode=off</span>
      </div>
    </AbsoluteFill>
  );
};
