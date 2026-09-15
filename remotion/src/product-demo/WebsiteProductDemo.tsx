import React from 'react';
import {AbsoluteFill, Composition, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {findSceneIndex, sceneLayout, validateProductInput, type ProductInput} from './website-product-contract.mjs';

const colors = {bg: '#090F1B', panel: '#101E30', ink: '#F7F8FC', secondary: '#B6C5D8', accent: '#A5DDF4', warm: '#F2C778'};
const font = 'Microsoft YaHei, Noto Sans CJK SC, sans-serif';

const HookCover: React.FC<{scene: ProductInput['scenes'][number]; local: number; left: number; contentWidth: number}> = ({scene, local, left, contentWidth}) => {
  const chips = ['找机位', '看天气', '挑时间'];
  return <>
    <div data-layout-box="product-brand" style={{position: 'absolute', left, top: 120, display: 'flex', alignItems: 'baseline', gap: 18}}>
      <b style={{fontSize: 46, letterSpacing: 6}}>逐星</b>
      <span style={{fontSize: 22, color: colors.secondary}}>摄影出发前的地图工作台</span>
    </div>
    <div data-layout-box="product-hook-kicker" style={{position: 'absolute', left, top: 285, color: colors.accent, fontSize: 24, fontWeight: 700, letterSpacing: 3}}>出发前，先做一个决定</div>
    <div data-layout-box="product-headline" style={{position: 'absolute', left, top: 340, width: contentWidth, fontSize: 82, lineHeight: 1.2, fontWeight: 900, letterSpacing: 1, whiteSpace: 'nowrap'}}>{scene.headline}</div>
    <div data-layout-box="product-hook-detail" style={{position: 'absolute', left, top: 470, width: contentWidth, fontSize: 34, color: colors.secondary}}>{scene.detail}</div>
    <div data-layout-box="product-hook-map" style={{position: 'absolute', left, top: 650, width: contentWidth, height: 470, overflow: 'hidden', border: `1px solid ${colors.accent}`, borderRadius: 24, background: 'radial-gradient(circle at 62% 42%, #1e4255 0, #102435 32%, #0c1626 70%)', boxShadow: '0 0 60px rgba(105,205,239,.16)'}}>
      <div style={{position: 'absolute', inset: 0, opacity: .24, backgroundImage: 'linear-gradient(rgba(165,221,244,.5) 1px, transparent 1px), linear-gradient(90deg, rgba(165,221,244,.5) 1px, transparent 1px)', backgroundSize: '58px 58px'}}/>
      <div style={{position: 'absolute', left: '18%', top: '58%', width: '66%', height: 3, background: colors.accent, transform: 'rotate(-18deg)', transformOrigin: 'left center', boxShadow: '0 0 18px rgba(165,221,244,.9)'}}/>
      <div style={{position: 'absolute', left: '68%', top: '34%', width: 22, height: 22, borderRadius: '50%', background: colors.warm, boxShadow: '0 0 0 10px rgba(242,199,120,.16), 0 0 30px rgba(242,199,120,.8)'}}/>
      <div style={{position: 'absolute', left: '15%', top: 28, color: colors.secondary, fontSize: 20, letterSpacing: 2}}>同一张地图工作台</div>
      <div style={{position: 'absolute', left: 42, right: 42, bottom: 34, display: 'flex', gap: 16}}>{chips.map((chip, index) => <div key={chip} style={{flex: 1, padding: '18px 12px', border: `1px solid ${index === 1 ? colors.accent : 'rgba(182,197,216,.5)'}`, borderRadius: 14, color: index === 1 ? colors.ink : colors.secondary, textAlign: 'center', fontSize: 26, fontWeight: 700, opacity: interpolate(local, [8 + index * 6, 18 + index * 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>{chip}</div>)}</div>
    </div>
    <div data-layout-box="product-hook-footer" style={{position: 'absolute', left, top: 1205, width: contentWidth, fontSize: 28, color: colors.secondary}}>先看条件，再决定要不要出发。</div>
  </>;
};

/** Visual-only product promo. Live pages are captured before render; focus rectangles only change presentation, never source bytes. */
export const WebsiteProductDemo: React.FC<ProductInput> = (raw) => {
  const input = validateProductInput(raw), frame = useCurrentFrame();
  const scene = input.scenes[findSceneIndex(input, frame)], local = frame - scene.startFrame;
  const portrait = input.aspect === '9:16', layout = sceneLayout(input.aspect, scene.id, scene.captureViewport), w = portrait ? 1080 : 1920;
  const left = portrait ? 76 : 96, right = portrait ? 160 : 96, contentWidth = w - left - right;
  const fade = interpolate(local, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const preview = input.mode === 'layout_preview', isHook = scene.visualRole === 'hook';
  const focus = scene.focus;
  const focusScale = focus ? interpolate(local, [0, 14], [focus.zoom * 0.96, focus.zoom], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 1;
  const focusImageStyle = focus ? {
    position: 'absolute' as const,
    width: `${100 / focus.width}%`,
    height: `${100 / focus.height}%`,
    left: `${-focus.x / focus.width * 100}%`,
    top: `${-focus.y / focus.height * 100}%`,
    objectFit: 'fill' as const,
    transform: `scale(${focusScale})`,
    transformOrigin: 'center center',
    opacity: fade,
  } : {width: '100%', height: '100%', objectFit: 'contain' as const, opacity: fade};
  return <AbsoluteFill style={{background: colors.bg, color: colors.ink, fontFamily: font}}>
    {isHook ? <HookCover scene={scene} local={local} left={left} contentWidth={contentWidth}/> : <>
      <div data-layout-box="product-brand" style={{position: 'absolute', left, top: portrait ? 120 : 72, display: 'flex', alignItems: 'baseline', gap: 18}}>
        <b style={{fontSize: portrait ? 42 : 38, letterSpacing: 6}}>逐星</b>
        <span style={{fontSize: 22, color: colors.secondary}}>摄影出发前的地图工作台</span>
      </div>
      <div data-layout-box="product-headline" style={{position: 'absolute', left, top: portrait ? 255 : 160, width: contentWidth, fontSize: layout.headlineFontSize, lineHeight: 1.25, fontWeight: 850, whiteSpace: 'pre-wrap', opacity: fade}}>{scene.headline}</div>
      {scene.kind === 'capture' ? <>
        <div data-layout-box="product-capture" data-focus-box={focus ? `${focus.x},${focus.y},${focus.width},${focus.height}` : undefined} style={{position: 'absolute', left, top: layout.captureTop, width: contentWidth, height: layout.captureHeight, border: `1px solid ${colors.secondary}`, borderRadius: 18, background: colors.panel, overflow: 'hidden'}}>
          {scene.asset ? <Img src={staticFile(scene.asset)} style={focusImageStyle}/> : <div style={{padding: 40, fontSize: 30}}>待采集真实页面。不是网站画面。</div>}
          {focus && <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', background: 'linear-gradient(180deg, rgba(9,15,27,.05), transparent 60%, rgba(9,15,27,.22))'}}/>}
          {focus && <div data-layout-box="product-focus-label" style={{position: 'absolute', right: 20, top: 18, padding: '8px 14px', borderRadius: 999, border: `1px solid ${colors.accent}`, color: colors.ink, background: 'rgba(9,15,27,.74)', fontSize: 18, fontWeight: 700}}>重点信息</div>}
        </div>
        <div data-layout-box="product-capture-label" style={{position: 'absolute', left, top: layout.captureLabelTop, width: contentWidth, color: colors.secondary, fontSize: 18, lineHeight: 1.45}}>
          {preview ? '版式预览；无生产素材' : `实机页面 · ${scene.capturedAt.slice(0, 10)} 采集`}
          <br/>{scene.attribution}
        </div>
      </> : <div data-layout-box="product-message" style={{position: 'absolute', left, top: portrait ? 560 : 360, width: contentWidth, opacity: fade}}>
        <div style={{width: 64, height: 4, marginBottom: 48, background: colors.accent}}/>
        <div style={{fontSize: portrait ? 64 : 70, fontWeight: 750, lineHeight: 1.35, whiteSpace: 'pre-wrap'}}>{scene.kind === 'cta' ? scene.headline : '找机位\n看天气\n挑时间'}</div>
        {scene.kind === 'cta' && <div data-layout-box="product-url" style={{fontSize: portrait ? 44 : 56, marginTop: 48, color: colors.accent}}>photo.joviluma.com</div>}
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
