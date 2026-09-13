import React from 'react';
import {AbsoluteFill, Composition, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {findSceneIndex, sceneLayout, validateProductInput, type ProductInput} from './website-product-contract.mjs';

// Proposed promo palette, not a claim about the currently deployed website CSS.
const colors = {bg: '#090F1B', panel: '#101E30', ink: '#F7F8FC', secondary: '#B6C5D8', accent: '#A5DDF4'};
const font = 'Microsoft YaHei, Noto Sans CJK SC, sans-serif';

/** Visual-only screenshot presentation. Never loads the live website at render time.
 * Use the existing factory audio/subtitle/mux and review-derivation path afterwards.
 * Images remain contain-fit: no cropping of third-party map attributions.
 */
export const WebsiteProductDemo: React.FC<ProductInput> = (raw) => {
  const input = validateProductInput(raw), frame = useCurrentFrame();
  const scene = input.scenes[findSceneIndex(input, frame)], local = frame - scene.startFrame;
  const portrait = input.aspect === '9:16', layout = sceneLayout(input.aspect, scene.id, scene.captureViewport), w = portrait ? 1080 : 1920;
  const left = portrait ? 76 : 96, right = portrait ? 160 : 96, contentWidth = w-left-right;
  const fade = interpolate(local, [0, 9], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const preview = input.mode === 'layout_preview';
  return <AbsoluteFill style={{background: colors.bg, color: colors.ink, fontFamily: font}}>
    <div data-layout-box="product-brand" style={{position: 'absolute', left, top: portrait ? 154 : 72,
      display: 'flex', alignItems: 'baseline', gap: 20}}>
      <b style={{fontSize: portrait ? 44 : 38, letterSpacing: 6}}>逐星</b>
      <span style={{fontSize: 22, color: colors.secondary}}>摄影出发前的地图工作台</span>
    </div>
    <div data-layout-box="product-headline" style={{position: 'absolute', left, top: portrait ? 270 : 160,
      width: contentWidth, fontSize: layout.headlineFontSize, lineHeight: 1.3, fontWeight: 800,
      whiteSpace: 'pre-wrap', opacity: fade}}>{scene.headline}</div>
    {scene.kind === 'capture' ? <>
      <div data-layout-box="product-capture" style={{position: 'absolute', left, top: layout.captureTop,
        width: contentWidth, height: layout.captureHeight, border: `1px solid ${colors.secondary}`,
        borderRadius: 16, background: colors.panel, overflow: 'hidden'}}>
        {scene.asset ? <Img src={staticFile(scene.asset)} style={{width: '100%', height: '100%', objectFit: 'contain', opacity: fade}}/>
          : <div style={{padding: 40, fontSize: 30}}>待采集真实页面。不是网站画面。</div>}
      </div>
      <div data-layout-box="product-capture-label" style={{position: 'absolute', left, top: layout.captureLabelTop,
        width: contentWidth, color: colors.secondary, fontSize: 20, lineHeight: 1.5}}>
        {preview ? '版式预览；无生产素材' : `页面截图演示 · ${scene.capturedAt.slice(0,10)} 采集`}
        <br/>{scene.attribution}
      </div>
    </> : <div data-layout-box="product-message" style={{position: 'absolute', left, top: portrait ? 580 : 360,
      width: contentWidth, opacity: fade}}>
      <div style={{width: 64, height: 4, marginBottom: 48, background: colors.accent}}/>
      <div style={{fontSize: portrait ? 62 : 70, fontWeight: 700, lineHeight: 1.45, whiteSpace: 'pre-wrap'}}>
        {scene.kind === 'cta' ? '先看一眼，再出发。' : '找机位\n看天气\n挑时间'}
      </div>
      {scene.kind === 'cta' && <div data-layout-box="product-url" style={{fontSize: portrait ? 44 : 56,
        marginTop: 48, color: colors.accent}}>photo.joviluma.com</div>}
    </div>}
    <div data-layout-box="product-detail" style={{position: 'absolute', left, width: contentWidth,
      top: layout.detailTop, fontSize: portrait ? 30 : 26, color: colors.secondary, lineHeight: 1.55}}>
      <strong style={{color: colors.accent}}>{scene.badge}</strong><br/>{scene.detail}
    </div>
    <div data-layout-box="product-disclaimer" style={{position: 'absolute', left, top: portrait ? 1810 : 1004,
      width: contentWidth, fontSize: portrait ? 24 : 20, color: colors.secondary}}>
      规划参考，出发前复核现场天气、道路与安全。
    </div>
    {preview && <div style={{position:'absolute',left:40,right:40,top:'48%',padding:30,
      background:'#481629',textAlign:'center',fontSize:40,fontWeight:800}}>LAYOUT PREVIEW · 非宣传成片</div>}
    {/* y=1640..1760 portrait / y=918..986 landscape reserved for ONE subtitle track. */}
  </AbsoluteFill>;
};

export const productPreview: ProductInput = {
  schema_version: '1.0', mode: 'layout_preview', fps: 30, aspect: '9:16',
  brand: '逐星', website: 'photo.joviluma.com', totalFrames: 1200,
  scriptSha256: '', timingSha256: '', captureManifestSha256: '', captureReviewSha256: '',
  scenes: ['title','capture','capture','capture','cta'].map((kind, i) => ({
    id: `shot${i+1}`, kind: kind as 'title'|'capture'|'cta', startFrame: i*240, endFrame: (i+1)*240,
    headline: ['别等到了山顶，才开始看天气','同一个地图工作台','看逐小时天气','挑合适的时间','规划下一次拍摄'][i],
    detail: '当前仅用于模板检查；正式渲染须提供真实截图与实测时序。', badge: '版式预览',
    asset: null, assetSha256: null, capturedAt: '', attribution: '',
  })),
};
export const WebsiteProductDemoRegistration: React.FC = () => <Composition
  id="WebsiteProductDemo" component={WebsiteProductDemo} durationInFrames={1200}
  fps={30} width={1080} height={1920} defaultProps={productPreview}
  calculateMetadata={({props}) => {
    const value = validateProductInput(props);
    return {durationInFrames:value.totalFrames, fps:30,
      width:value.aspect === '9:16' ? 1080 : 1920, height:value.aspect === '9:16' ? 1920 : 1080};
  }}/>
