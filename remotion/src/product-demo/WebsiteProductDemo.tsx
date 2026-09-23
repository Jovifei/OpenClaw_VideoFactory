import React from 'react';
import {AbsoluteFill, Composition, Easing, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {findSceneIndex, sceneLayout, validateProductInput, type ProductInput} from './website-product-contract.mjs';

const colors = {bg: '#090F1B', panel: '#101E30', ink: '#F7F8FC', secondary: '#B6C5D8', accent: '#A5DDF4', warm: '#F2C778'};
const font = 'Microsoft YaHei, Noto Sans CJK SC, sans-serif';

const cameraFor = (scene: ProductInput['scenes'][number], frame: number) => {
  const cues = scene.voiceCues ?? [];
  const activeIndex = cues.findIndex(cue => cue.startFrame <= frame && frame < cue.endFrame);
  const completedIndex = cues.reduce((last, cue, index) => cue.endFrame <= frame ? index : last, -1);
  const current = activeIndex >= 0 ? cues[activeIndex] : null;
  const target = current ?? (completedIndex >= 0 ? cues[completedIndex] : null);
  const previous = current && activeIndex > 0 ? cues[activeIndex - 1] : null;
  const progress = current ? interpolate(frame, [current.startFrame, current.endFrame], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic),
  }) : 1;
  const base = {panX: 0, panY: 0, zoom: scene.focus?.zoom ?? 1, targetX: 0.5, targetY: 0.5};
  const from = previous ?? base;
  const to = target ?? base;
  const markerOpacity = current ? interpolate(frame,
    [current.startFrame, current.startFrame + 5, current.endFrame - 6, current.endFrame - 1], [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0;
  return {
    transform: `translate(${interpolate(progress, [0, 1], [from.panX, to.panX])}px, ${interpolate(progress, [0, 1], [from.panY, to.panY])}px) scale(${interpolate(progress, [0, 1], [from.zoom, to.zoom])})`,
    label: current?.label ?? '',
    labelOpacity: current ? interpolate(frame, [current.startFrame, Math.min(current.startFrame + 5, current.endFrame)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0,
    markerX: interpolate(progress, [0, 1], [from.targetX, to.targetX]),
    markerY: interpolate(progress, [0, 1], [from.targetY, to.targetY]),
    markerOpacity,
    markerScale: interpolate(progress, [0, 1], [0.72, 1.06]),
  };
};

const focusImageStyle = (scene: ProductInput['scenes'][number]) => {
  const focus = scene.focus;
  if (!focus) return {position: 'absolute' as const, inset: 0, width: '100%', height: '100%', objectFit: 'cover' as const};
  return {position: 'absolute' as const, width: `${100 / focus.width}%`, height: `${100 / focus.height}%`,
    left: `${-focus.x / focus.width * 100}%`, top: `${-focus.y / focus.height * 100}%`, objectFit: 'fill' as const};
};

const MotionLabel: React.FC<{label: string; opacity: number}> = ({label, opacity}) => label ? <div data-layout-box="product-motion-label" style={{position: 'absolute', left: 22, top: 20, padding: '12px 20px', borderRadius: 999,
  color: colors.ink, background: 'rgba(9,15,27,.88)', border: `1px solid ${colors.accent}`, fontSize: 24, fontWeight: 800,
  opacity, transform: `translateY(${(1 - opacity) * 8}px)`}}>{label}</div> : null;

const FocusReticle: React.FC<{x: number; y: number; opacity: number; scale: number}> = ({x, y, opacity, scale}) => <div data-layout-box="product-reticle" style={{position: 'absolute', left: `${x * 100}%`, top: `${y * 100}%`, width: 68, height: 68,
  borderRadius: '50%', border: `3px solid ${colors.accent}`, boxShadow: '0 0 0 10px rgba(165,221,244,.14), 0 0 28px rgba(165,221,244,.75)',
  transform: `translate(-50%,-50%) scale(${scale})`, opacity, pointerEvents: 'none'}}><div style={{position: 'absolute', width: 10, height: 10, borderRadius: '50%', background: colors.warm, left: 26, top: 26}}/></div>;

const HookCover: React.FC<{scene: ProductInput['scenes'][number]; local: number; left: number; contentWidth: number; camera: ReturnType<typeof cameraFor>; preview: boolean}> = ({scene, local, left, contentWidth, camera, preview}) => {
  const reveal = interpolate(local, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <>
    <div data-layout-box="product-brand" style={{position: 'absolute', left, top: 105, display: 'flex', alignItems: 'baseline', gap: 18, opacity: reveal}}>
      <b style={{fontSize: 46, letterSpacing: 6}}>逐星</b><span style={{fontSize: 22, color: colors.secondary}}>摄影出发前的地图工作台</span>
    </div>
    <div data-layout-box="product-hook-kicker" style={{position: 'absolute', left, top: 265, color: colors.accent, fontSize: 24, fontWeight: 750, letterSpacing: 3, opacity: reveal}}>拍摄出发前 · 先把条件看清</div>
    <div data-layout-box="product-headline" style={{position: 'absolute', left, top: 325, width: contentWidth, fontSize: 80, lineHeight: 1.2, fontWeight: 900, letterSpacing: 1, whiteSpace: 'nowrap', opacity: reveal}}>{scene.headline}</div>
    <div data-layout-box="product-hook-detail" style={{position: 'absolute', left, top: 435, width: contentWidth, fontSize: 31, color: colors.secondary, opacity: reveal}}>{scene.detail}</div>
    <div data-layout-box="product-hook-badge" style={{position: 'absolute', left, top: 480, color: colors.accent, fontSize: 20, fontWeight: 700, opacity: reveal}}>{scene.badge}</div>
    <div data-layout-box="product-hook-map" style={{position: 'absolute', left, top: 525, width: contentWidth, height: 580, overflow: 'hidden', border: `1px solid ${colors.accent}`, borderRadius: 24, background: colors.panel, boxShadow: '0 18px 70px rgba(0,0,0,.42)'}}>
      <div style={{position: 'absolute', inset: 0, transform: camera.transform, transformOrigin: 'center center'}}>
        {scene.asset ? <Img src={staticFile(scene.asset)} style={focusImageStyle(scene)}/> : <div style={{width: '100%', height: '100%', background: 'radial-gradient(circle at 62% 42%, #1e4255 0, #102435 32%, #0c1626 70%)'}}/>}
      </div>
      <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', background: 'linear-gradient(180deg, rgba(9,15,27,.12), transparent 34%, transparent 78%, rgba(9,15,27,.42))'}}/>
      {!preview && <FocusReticle x={camera.markerX} y={camera.markerY} opacity={camera.markerOpacity} scale={camera.markerScale}/>}
      {!preview && <MotionLabel label={camera.label} opacity={camera.labelOpacity}/>}
    </div>
    {!preview && <div data-layout-box="product-attribution" style={{position: 'absolute', left, top: 1117, width: contentWidth, color: colors.secondary, fontSize: 16}}>{scene.attribution}</div>}
    <div data-layout-box="product-hook-footer" style={{position: 'absolute', left, top: 1180, width: contentWidth, fontSize: 28, color: colors.secondary}}>地点 · 夜空 · 云海条件，一屏展开</div>
  </>;
};

/** Visual-only product promo. Live pages are captured before render; focus rectangles only change presentation, never source bytes. */
export const WebsiteProductDemo: React.FC<ProductInput> = (raw) => {
  const input = validateProductInput(raw), frame = useCurrentFrame();
  const scene = input.scenes[findSceneIndex(input, frame)], local = frame - scene.startFrame;
  const portrait = input.aspect === '9:16', layout = sceneLayout(input.aspect, scene.id, scene.captureViewport), w = portrait ? 1080 : 1920;
  const left = portrait ? 76 : 96, right = portrait ? 76 : 96, contentWidth = w - left - right;
  const fade = interpolate(local, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const preview = input.mode === 'layout_preview', isHook = scene.visualRole === 'hook';
  const camera = cameraFor(scene, frame);
  const focus = scene.focus;
  return <AbsoluteFill style={{background: colors.bg, color: colors.ink, fontFamily: font}}>
    {isHook ? <HookCover scene={scene} local={local} left={left} contentWidth={contentWidth} camera={camera} preview={preview}/> : <>
      <div data-layout-box="product-brand" style={{position: 'absolute', left, top: portrait ? 120 : 72, display: 'flex', alignItems: 'baseline', gap: 18}}>
        <b style={{fontSize: portrait ? 42 : 38, letterSpacing: 6}}>逐星</b>
        <span style={{fontSize: 22, color: colors.secondary}}>摄影出发前的地图工作台</span>
      </div>
      <div data-layout-box="product-headline" style={{position: 'absolute', left, top: portrait ? 255 : 160, width: contentWidth, fontSize: layout.headlineFontSize, lineHeight: 1.25, fontWeight: 850, whiteSpace: 'pre-wrap', opacity: fade}}>{scene.headline}</div>
      {scene.kind === 'capture' ? <>
        <div data-layout-box="product-capture" data-focus-box={focus ? `${focus.x},${focus.y},${focus.width},${focus.height}` : undefined} style={{position: 'absolute', left, top: layout.captureTop, width: contentWidth, height: layout.captureHeight, border: `1px solid ${colors.secondary}`, borderRadius: 18, background: colors.panel, overflow: 'hidden'}}>
          <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
            <div style={{position: 'absolute', inset: 0, transform: camera.transform, transformOrigin: 'center center', opacity: fade}}>
              {scene.asset ? <Img src={staticFile(scene.asset)} style={focusImageStyle(scene)}/> : <div style={{padding: 40, fontSize: 30}}>待采集真实页面。不是网站画面。</div>}
            </div>
          </div>
          {focus && <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', background: 'linear-gradient(180deg, rgba(9,15,27,.05), transparent 60%, rgba(9,15,27,.22))'}}/>}
          {!preview && <FocusReticle x={camera.markerX} y={camera.markerY} opacity={camera.markerOpacity} scale={camera.markerScale}/>}
          {!preview && <MotionLabel label={camera.label} opacity={camera.labelOpacity}/>}
        </div>
        {!preview && <div data-layout-box="product-attribution" style={{position: 'absolute', left, top: layout.captureLabelTop, width: contentWidth, color: colors.secondary, fontSize: 16, lineHeight: 1.35}}>{scene.attribution}</div>}
      </> : <div data-layout-box="product-message" style={{position: 'absolute', left, top: portrait ? 560 : 360, width: contentWidth, opacity: fade,
        transform: scene.kind === 'cta' ? camera.transform : undefined, transformOrigin: 'left center'}}>
        <div style={{width: 64, height: 4, marginBottom: 48, background: colors.accent}}/>
        {scene.kind === 'cta' ? <>
          <div style={{fontSize: portrait ? 48 : 46, fontWeight: 750, color: colors.accent, minHeight: 68, opacity: camera.labelOpacity}}>{camera.label}</div>
          <div style={{fontSize: portrait ? 72 : 70, fontWeight: 850, lineHeight: 1.22, whiteSpace: 'pre-wrap'}}>{scene.headline}</div>
          <div data-layout-box="product-url" style={{fontSize: portrait ? 44 : 56, marginTop: 48, color: colors.accent}}>photo.joviluma.com</div>
        </> : <div style={{fontSize: portrait ? 64 : 70, fontWeight: 750, lineHeight: 1.35, whiteSpace: 'pre-wrap'}}>找机位\n看天气\n挑时间</div>}
      </div>}
      <div data-layout-box="product-detail" style={{position: 'absolute', left, width: contentWidth, top: layout.detailTop, fontSize: portrait ? 30 : 26, color: colors.secondary, lineHeight: 1.5}}><strong style={{color: colors.accent}}>{scene.badge}</strong><br/>{scene.detail}</div>
      <div data-layout-box="product-disclaimer" style={{position: 'absolute', left, top: portrait ? 1810 : 1004, width: contentWidth, fontSize: portrait ? 22 : 20, color: colors.secondary}}>规划参考，出发前复核现场天气、道路与安全。</div>
    </>}
    {preview && <div style={{position: 'absolute', left: 40, right: 40, top: '48%', padding: 30, background: '#481629', textAlign: 'center', fontSize: 40, fontWeight: 800}}>LAYOUT PREVIEW · 非宣传成片</div>}
    {/* Portrait subtitles occupy y=1640..1760 and remain the only timed subtitle layer. */}
  </AbsoluteFill>;
};

export const productPreview: ProductInput = {
  schema_version: '1.0', mode: 'layout_preview', fps: 30, aspect: '9:16', totalFrames: 1200,
  brand: '逐星', website: 'photo.joviluma.com', scriptSha256: '', timingSha256: '', captureManifestSha256: '', captureReviewSha256: '',
  scenes: ['title', 'capture', 'capture', 'capture', 'cta'].map((kind, i) => ({
    id: `shot${i + 1}`, kind: kind as 'title' | 'capture' | 'cta', startFrame: i * 240, endFrame: (i + 1) * 240,
    headline: ['别等到了山顶，才开始看天气', '同一个地图工作台', '看逐小时天气', '挑合适的时间', '规划下一次拍摄'][i],
    detail: '当前仅用于模板检查；正式渲染须提供真实截图与实测时序。', badge: '版式预览', asset: null, assetSha256: null, capturedAt: '', attribution: '', focus: null,
  })),
};

export const WebsiteProductDemoRegistration: React.FC = () => <Composition id="WebsiteProductDemo" component={WebsiteProductDemo} durationInFrames={1200} fps={30} width={1080} height={1920} defaultProps={productPreview} calculateMetadata={({props}) => {
  const value = validateProductInput(props);
  return {durationInFrames: value.totalFrames, fps: 30, width: value.aspect === '9:16' ? 1080 : 1920, height: value.aspect === '9:16' ? 1920 : 1080};
}}/>;
