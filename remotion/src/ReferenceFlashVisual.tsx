import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type FlashVisualScene = {
  start_seconds: number;
  end_seconds: number;
  heading: string;
  visual_kind: 'window' | 'sequence' | 'budget' | 'recovery' | 'checklist';
};

export type FlashVisualInput = {
  schema_version: '1.0';
  title: string;
  duration_seconds: number;
  fps: 30;
  scenes: FlashVisualScene[];
};

// Clean-room style tokens derived from the public reference: warm neutral
// canvas, black typography, white information cards, and three accent roles.
// No source frame, logo, caption, or creator identity is imported.
const COLORS = {
  ink: '#15151B',
  slate: '#5E606A',
  muted: '#9A9AA1',
  canvas: '#F6F1E8',
  panel: '#FFFDF9',
  line: '#DAD3C8',
  mint: '#72C9A9',
  orange: '#E99B4B',
  purple: '#8876C7',
  red: '#C75D55',
} as const;

const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

const Badge: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = COLORS.ink}) => (
  <div style={{
    display: 'inline-flex',
    alignItems: 'center',
    padding: '9px 16px',
    border: `2px solid ${color}`,
    borderRadius: 999,
    color,
    fontSize: 18,
    fontWeight: 900,
    letterSpacing: 1.6,
    lineHeight: 1,
    background: `${color}0D`,
  }}>{children}</div>
);

const Card: React.FC<{children: React.ReactNode; color?: string; style?: React.CSSProperties}> = ({children, color = COLORS.line, style}) => (
  <div style={{
    background: COLORS.panel,
    border: `2px solid ${COLORS.line}`,
    borderTop: `8px solid ${color}`,
    borderRadius: 22,
    boxShadow: '0 16px 36px rgba(55,44,27,0.09)',
    ...style,
  }}>{children}</div>
);

const Arrow: React.FC<{color?: string}> = ({color = COLORS.ink}) => (
  <div style={{width: 74, height: 3, background: color, position: 'relative', flexShrink: 0}}>
    <div style={{
      position: 'absolute',
      right: -2,
      top: -7,
      width: 0,
      height: 0,
      borderTop: '9px solid transparent',
      borderBottom: '9px solid transparent',
      borderLeft: `15px solid ${color}`,
    }} />
  </div>
);

const WindowDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const pulse = interpolate((frame % (2 * fps)) / fps, [0, 1, 2], [0.97, 1.04, 0.97], clamp);
  return <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 28, marginTop: 54}}>
    <Card color={COLORS.mint} style={{width: 510, height: 248, padding: 28}}>
      <div style={{fontSize: 19, letterSpacing: 2.4, fontWeight: 900, color: COLORS.muted}}>FLASH CONTROLLER</div>
      <div style={{display: 'flex', alignItems: 'center', gap: 22, marginTop: 27}}>
        <div style={{width: 114, height: 114, borderRadius: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', border: `4px solid ${COLORS.mint}`, background: `${COLORS.mint}18`, color: COLORS.ink, fontSize: 25, fontWeight: 900}}>ERASE</div>
        <div style={{fontSize: 25, lineHeight: 1.35, color: COLORS.ink, fontWeight: 900}}>忙状态可观察<br /><span style={{fontSize: 20, color: COLORS.slate}}>不要把它当成黑盒</span></div>
      </div>
    </Card>
    <Arrow color={COLORS.ink} />
    <Card color={COLORS.orange} style={{width: 510, height: 248, padding: 28}}>
      <div style={{fontSize: 19, letterSpacing: 2.4, fontWeight: 900, color: COLORS.muted}}>IWDG SERVICE WINDOW</div>
      <div style={{display: 'flex', alignItems: 'center', gap: 26, marginTop: 21}}>
        <div style={{width: 118, height: 118, borderRadius: '50%', border: `11px solid ${COLORS.orange}`, borderRightColor: COLORS.line, transform: `scale(${pulse})`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: COLORS.orange, fontSize: 27, fontWeight: 900}}>T<sub>win</sub></div>
        <div style={{fontSize: 25, lineHeight: 1.35, color: COLORS.ink, fontWeight: 900}}>独立时钟倒计时<br /><span style={{fontSize: 20, color: COLORS.slate}}>窗口必须可计算</span></div>
      </div>
    </Card>
  </div>;
};

const SequenceDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const active = Math.min(3, Math.floor((frame / fps) % 4));
  const items = [
    ['01', '解锁并发起', COLORS.mint],
    ['02', '等待忙状态', COLORS.purple],
    ['03', '检查错误', COLORS.orange],
    ['04', '确认完成', COLORS.mint],
  ] as const;
  return <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, marginTop: 60}}>
    {items.map(([number, label, color], index) => <React.Fragment key={label}>
      <Card color={index === active ? color : COLORS.line} style={{width: 268, height: 174, padding: 22, opacity: index <= active ? 1 : 0.48, transform: `translateY(${index === active ? -10 : 0}px)`}}>
        <div style={{fontSize: 31, color: index <= active ? color : COLORS.muted, fontWeight: 900}}>{number}</div>
        <div style={{fontSize: 23, color: COLORS.ink, fontWeight: 900, marginTop: 24, whiteSpace: 'nowrap'}}>{label}</div>
      </Card>
      {index < items.length - 1 && <Arrow color={index < active ? COLORS.mint : COLORS.line} />}
    </React.Fragment>)}
  </div>;
};

const BudgetDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const progress = interpolate(frame % (4 * fps), [0, 2 * fps, 4 * fps], [0, 1, 0], clamp);
  const marker = 230 + progress * 1120;
  return <div style={{width: 1370, margin: '60px auto 0'}}>
    <div style={{display: 'flex', alignItems: 'baseline', justifyContent: 'space-between'}}>
      <div style={{fontSize: 31, fontWeight: 900, color: COLORS.ink}}>最坏擦除时间 = 服务窗口预算</div>
      <div style={{fontSize: 24, color: COLORS.slate, fontWeight: 900}}>T<sub>erase,max</sub> ≤ T<sub>service</sub></div>
    </div>
    <div style={{height: 42, marginTop: 30, borderRadius: 21, background: COLORS.line, overflow: 'hidden', position: 'relative'}}>
      <div style={{height: '100%', width: '48%', background: COLORS.mint}} />
      <div style={{position: 'absolute', left: '48%', top: 0, bottom: 0, width: '34%', background: COLORS.orange}} />
      <div style={{position: 'absolute', left: '82%', top: 0, bottom: 0, width: '18%', background: `${COLORS.red}D0`}} />
    </div>
    <div style={{display: 'flex', justifyContent: 'space-between', marginTop: 14, color: COLORS.slate, fontSize: 20, fontWeight: 900}}>
      <span>擦除执行</span><span>服务余量</span><span>复位风险</span>
    </div>
    <div style={{position: 'relative', height: 100, marginTop: 32, borderTop: `2px dashed ${COLORS.line}`}}>
      <div style={{position: 'absolute', left: marker, top: -12, width: 4, height: 82, background: COLORS.purple, boxShadow: `0 0 0 8px ${COLORS.purple}20`}} />
      <div style={{position: 'absolute', left: marker - 62, top: 74, color: COLORS.purple, fontSize: 20, fontWeight: 900, whiteSpace: 'nowrap'}}>先测量，再定窗口</div>
    </div>
  </div>;
};

const RecoveryDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const active = Math.min(2, Math.floor((frame / fps) % 3));
  const nodes = [
    ['正常完成', COLORS.mint],
    ['记录错误', COLORS.orange],
    ['受控恢复', COLORS.purple],
  ] as const;
  return <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 26, marginTop: 62}}>
    {nodes.map(([label, color], index) => <React.Fragment key={label}>
      <Card color={index === active ? color : COLORS.line} style={{width: 320, height: 178, padding: 26, opacity: index <= active ? 1 : 0.48, transform: `scale(${index === active ? 1.03 : 1})`}}>
        <div style={{width: 21, height: 21, borderRadius: '50%', background: index <= active ? color : COLORS.line, boxShadow: index <= active ? `0 0 0 7px ${color}20` : 'none'}} />
        <div style={{fontSize: 26, color: COLORS.ink, fontWeight: 900, marginTop: 28}}>{label}</div>
      </Card>
      {index < nodes.length - 1 && <Arrow color={index < active ? COLORS.purple : COLORS.line} />}
    </React.Fragment>)}
  </div>;
};

const ChecklistDiagram: React.FC<{frame: number; fps: number}> = ({frame, fps}) => {
  const items = ['按手册发起', '观察忙状态', '检查错误', '留出可算窗口'];
  const accents = [COLORS.mint, COLORS.purple, COLORS.orange, COLORS.mint];
  const active = Math.min(items.length - 1, Math.floor((frame / fps) % items.length));
  return <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 18, width: 1370, margin: '62px auto 0'}}>
    {items.map((label, index) => <Card key={label} color={index === active ? accents[index] : COLORS.line} style={{height: 178, padding: 25, opacity: index <= active ? 1 : 0.52}}>
      <div style={{fontSize: 40, color: index <= active ? accents[index] : COLORS.muted, fontWeight: 900}}>0{index + 1}</div>
      <div style={{fontSize: 23, color: COLORS.ink, fontWeight: 900, marginTop: 24, whiteSpace: 'nowrap'}}>{label}</div>
    </Card>)}
  </div>;
};

const Diagram: React.FC<{kind: FlashVisualScene['visual_kind']; frame: number; fps: number}> = ({kind, frame, fps}) => {
  if (kind === 'window') return <WindowDiagram frame={frame} fps={fps} />;
  if (kind === 'sequence') return <SequenceDiagram frame={frame} fps={fps} />;
  if (kind === 'budget') return <BudgetDiagram frame={frame} fps={fps} />;
  if (kind === 'recovery') return <RecoveryDiagram frame={frame} fps={fps} />;
  return <ChecklistDiagram frame={frame} fps={fps} />;
};

const ACT_LABELS = [
  'ACT 01 / WINDOW LOGIC',
  'ACT 02 / OBSERVABLE STATES',
  'ACT 03 / TIME BUDGET',
  'ACT 04 / RECOVERY PATH',
  'ACT 05 / ENGINEERING CHECKLIST',
];

export const ReferenceFlashVisual: React.FC<FlashVisualInput> = (input) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;
  const currentIndex = Math.max(0, input.scenes.findIndex((scene) => seconds >= scene.start_seconds && seconds < scene.end_seconds));
  const scene = input.scenes[currentIndex] ?? input.scenes[input.scenes.length - 1];
  const localFrame = Math.max(0, frame - Math.round(scene.start_seconds * fps));
  const entrance = interpolate(localFrame, [0, 22], [28, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)});
  const opacity = spring({frame: localFrame, fps, config: {damping: 200}});
  const progress = interpolate(seconds, [0, input.duration_seconds], [0, 100], clamp);
  const actColor = [COLORS.mint, COLORS.purple, COLORS.orange, COLORS.purple, COLORS.mint][currentIndex] ?? COLORS.mint;

  return <AbsoluteFill style={{background: COLORS.canvas, color: COLORS.ink, fontFamily: 'Microsoft YaHei, Microsoft JhengHei, sans-serif'}}>
    <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(circle at 86% 12%, rgba(114,201,169,0.12), transparent 26%), radial-gradient(circle at 5% 92%, rgba(136,118,199,0.10), transparent 24%)'}} />
    <div style={{position: 'absolute', left: 82, right: 82, top: 46, display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
      <Badge color={COLORS.ink}>HARDWARE NOTES · ORIGINAL</Badge>
      <Badge color={actColor}>{ACT_LABELS[currentIndex] ?? ACT_LABELS[0]}</Badge>
    </div>
    <div style={{position: 'absolute', left: 82, right: 82, top: 135, display: 'flex', alignItems: 'end', justifyContent: 'space-between'}}>
      <div>
        <div style={{fontSize: 22, color: actColor, fontWeight: 900, letterSpacing: 2.8}}>FLASH × IWDG</div>
        <div style={{fontSize: 61, lineHeight: 1.12, fontWeight: 950, marginTop: 13, maxWidth: 1420}}>{input.title}</div>
      </div>
      <div style={{fontSize: 23, color: COLORS.slate, fontWeight: 900, letterSpacing: 1}}>{String(currentIndex + 1).padStart(2, '0')} / {String(input.scenes.length).padStart(2, '0')}</div>
    </div>
    <div style={{position: 'absolute', left: 82, right: 82, top: 318, height: 6, borderRadius: 4, background: COLORS.line}}>
      <div style={{height: '100%', width: `${progress}%`, borderRadius: 4, background: actColor}} />
    </div>
    <div style={{position: 'absolute', left: 82, right: 82, top: 385, bottom: 74, opacity, transform: `translateY(${entrance}px)`}}>
      <div style={{fontSize: 24, color: COLORS.slate, fontWeight: 900, letterSpacing: 0.8}}>{scene.heading}</div>
      <Diagram kind={scene.visual_kind} frame={localFrame} fps={fps} />
    </div>
    <div style={{position: 'absolute', left: 82, right: 82, bottom: 29, display: 'flex', justifyContent: 'space-between', color: COLORS.muted, fontSize: 16, fontWeight: 800, letterSpacing: 0.5}}>
      <span>原创技术图 · 画面无烧录字幕</span>
      <span>Jianying 原生字幕后置 · mascot_mode=off</span>
    </div>
  </AbsoluteFill>;
};
