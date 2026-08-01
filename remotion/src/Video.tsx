import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {DESIGN, templateAccent, templateLabel} from './design';
import {durationSeconds, fpsOf, sceneAt, sceneIndexAt, validateInput, type CandidateRenderInput} from './contracts';

const ProtocolVisual: React.FC<{accent: string; active: number}> = ({accent, active}) => (
  <div style={{display: 'flex', gap: 12, marginTop: 54}}>
    {['01', '03', '02', '00', '0A', '79', '84'].map((byte, index) => <div key={byte} style={{padding: '18px 14px', borderRadius: 12, background: index === active ? accent : '#E8EEF7', color: index === active ? DESIGN.colors.surface : DESIGN.colors.ink, fontSize: 25, fontWeight: 800}}>{byte}</div>)}
  </div>
);

const FlowVisual: React.FC<{accent: string; active: number}> = ({accent, active}) => (
  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18, marginTop: 38}}>
    {['任务持有互斥锁', '中断最小通知', '任务完成释放'].map((label, index) => <React.Fragment key={label}><div style={{padding: '16px 28px', borderRadius: DESIGN.radius.chip, background: index === active ? accent : '#F0F3F8', color: index === active ? DESIGN.colors.ink : DESIGN.colors.ink, fontSize: 25, fontWeight: 700}}>{label}</div>{index < 2 && <div style={{fontSize: 28, color: accent}}>↓</div>}</React.Fragment>)}
  </div>
);

const CodeVisual: React.FC<{active: number}> = ({active}) => <pre style={{marginTop: 44, padding: 28, borderRadius: DESIGN.radius.chip, color: '#D7E6FF', background: DESIGN.colors.code, fontSize: 25, lineHeight: 1.45, borderLeft: `8px solid ${active === 1 ? DESIGN.colors.pink : DESIGN.colors.blue}`}}>{'if (watchdog_due) {\n  feed_before_erase();\n  verify_flash_status();\n}'}</pre>;

const CaseVisual: React.FC<{accent: string; active: number}> = ({accent, active}) => <div style={{marginTop: 44, padding: 28, borderRadius: DESIGN.radius.chip, background: '#FFF6F3', border: `2px solid ${accent}`}}><div style={{fontSize: 24, fontWeight: 800, color: accent}}>工程告警 {String(active + 1).padStart(2, '0')}</div><div style={{fontSize: 30, lineHeight: 1.45, marginTop: 12}}>先确认手册边界，再记录时间预算，最后选择受控恢复路径。</div></div>;

export const CandidateVideo: React.FC<CandidateRenderInput> = (rawInput) => {
  const input = validateInput(rawInput);
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fpsOf(input);
  const totalDuration = durationSeconds(input);
  const scene = sceneAt(input, seconds);
  const sceneIndex = sceneIndexAt(input, seconds);
  const caption = input.captions.find((item) => seconds >= item.start && seconds < item.end);
  const accent = templateAccent(input.template);
  const localStart = input.schema_version === '2.0' ? input.scenes[sceneIndex].start_seconds : sceneIndex * totalDuration / input.scenes.length;
  const localFrame = Math.max(0, frame - Math.round(localStart * fps));
  const entrance = interpolate(localFrame, [0, 14], [28, 0], {extrapolateRight: 'clamp'});
  const cardOpacity = spring({frame: localFrame, fps, config: {damping: 200}});
  const mascotStart = Math.min(2, Math.max(0, totalDuration - 8));
  const mascotEnd = Math.min(mascotStart + 6, Math.max(mascotStart, totalDuration - 2));
  const mascotVisible = seconds >= mascotStart && seconds < mascotEnd;
  const conclusionVisible = seconds >= totalDuration - Math.min(4, totalDuration / 3);
  const scanX = (frame * 9) % 1240 - 160;
  const scanY = (frame * 13) % 2080 - 80;

  return <AbsoluteFill style={{backgroundColor: DESIGN.colors.mist, color: DESIGN.colors.ink, fontFamily: DESIGN.font}}>
    <Audio src={staticFile(input.audio.asset)} />
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none'}}><div style={{position: 'absolute', top: 0, bottom: 0, left: scanX, width: 88, background: `linear-gradient(90deg, transparent, ${accent}22, transparent)`}} /><div style={{position: 'absolute', left: 0, right: 0, top: scanY, height: 72, background: `linear-gradient(180deg, transparent, ${accent}40, transparent)`}} /></div>
    <div style={{position: 'absolute', top: DESIGN.safe.top, left: DESIGN.safe.left, right: DESIGN.safe.right}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div style={{fontSize: 26, fontWeight: 800, color: accent, letterSpacing: 2}}>{templateLabel(input.template)}</div>
        <div style={{fontSize: 22, fontWeight: 700, color: DESIGN.colors.ink}}>{String(sceneIndex + 1).padStart(2, '0')} / {String(input.scenes.length).padStart(2, '0')}</div>
      </div>
      <div style={{fontSize: 58, fontWeight: 800, lineHeight: 1.22, marginTop: 24}}>{input.title}</div>
    </div>
    <div style={{position: 'absolute', left: DESIGN.safe.left, right: DESIGN.safe.right, top: 408, height: 6, borderRadius: 4, background: DESIGN.colors.muted}}><div style={{height: '100%', width: `${Math.min(100, (seconds / totalDuration) * 100)}%`, borderRadius: 4, background: accent}} /></div>
    <div style={{position: 'absolute', top: 510, left: DESIGN.safe.left, right: DESIGN.safe.right, bottom: 430, borderRadius: DESIGN.radius.panel, backgroundImage: `linear-gradient(110deg, ${DESIGN.colors.surface} 0%, ${DESIGN.colors.surface} 38%, ${accent}20 50%, ${DESIGN.colors.surface} 62%, ${DESIGN.colors.surface} 100%)`, backgroundSize: '220% 100%', backgroundPosition: `${(frame * 0.9) % 220}% 0`, padding: 48, boxShadow: '0 18px 48px rgba(23,32,51,0.12)', opacity: cardOpacity, transform: `translateY(${entrance}px)`}}>
      <div style={{fontSize: 22, fontWeight: 800, letterSpacing: 2, color: accent}}>关键步骤 {String(sceneIndex + 1).padStart(2, '0')}</div>
      <div style={{fontSize: 44, fontWeight: 800, color: accent, marginTop: 14}}>{scene.heading}</div>
      <div style={{fontSize: 34, lineHeight: 1.55, marginTop: 26}}>{scene.body}</div>
      {input.template === 'protocol-frame' && <ProtocolVisual accent={accent} active={sceneIndex} />}
      {input.template === 'flow-diagram' && <FlowVisual accent={accent} active={sceneIndex} />}
      {input.template === 'code-explainer' && <CodeVisual active={sceneIndex} />}
      {input.template === 'engineering-case' && <CaseVisual accent={accent} active={sceneIndex} />}
    </div>
    {mascotVisible && <Img src={staticFile(input.mascot.asset)} style={{position: 'absolute', width: 152, height: 152, objectFit: 'contain', right: 64, top: 320, transform: `rotate(${Math.sin(frame / 12) * 3}deg)`}} />}
    {conclusionVisible && <div style={{position: 'absolute', left: DESIGN.safe.left, right: DESIGN.safe.right, bottom: 250, padding: '18px 24px', borderRadius: DESIGN.radius.chip, background: '#FFFFFF', border: `2px solid ${accent}`, fontSize: 26, fontWeight: 800, color: accent}}>工程结论：先确认边界，再执行下一步。</div>}
    {caption && <div style={{position: 'absolute', left: DESIGN.safe.left, right: DESIGN.safe.right, bottom: 90, minHeight: 120, display: 'flex', justifyContent: 'center', alignItems: 'center', textAlign: 'center', whiteSpace: 'pre-line', padding: '16px 28px', borderRadius: DESIGN.radius.caption, background: 'rgba(23,32,51,0.90)', color: DESIGN.colors.surface, fontSize: 34, fontWeight: 700, lineHeight: 1.35}}>{caption.text}</div>}
  </AbsoluteFill>;
};
