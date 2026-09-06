import React from 'react';
import {fillTextBox, fitText, measureText} from '@remotion/layout-utils';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export type I2CVisualSpec = {kind:'i2c_bus_v1'; fact_refs:string[]; labels:string[]};
export type TechnicalScene = {start_seconds:number; end_seconds:number; scene_index:number; scene_type?:string; visual_type:'kinetic_typography'|'system_diagram'|'timeline'|'comparison_card'|'checklist'; narration:string; on_screen_knowledge:string; information_role:string; narrative_role:string; shot_intent:string; motion:string; transition:string; source_refs:string[]; visual_spec?:I2CVisualSpec};
export type TechnicalExplainerInput = {schema_version:'1.0'; title:string; aspect:'16:9'|'9:16'; fps:30; duration_seconds:number; scenes:TechnicalScene[]};
export const ASPECT_GEOMETRY={'16:9':{titleMaxWidth:1450,sceneWidth:1752,titleMinFont:42,titleMaxFont:58,itemMinFont:24},'9:16':{titleMaxWidth:900,sceneWidth:936,titleMinFont:40,titleMaxFont:54,itemMinFont:22}} as const;
type SceneTextLayout={mainFontSize:number;itemFontSizes:number[];itemBoxWidth:number;maxLines:number;minFontSize:number;maxFontSize:number;columns:number};

const palette={canvas:'#F2F4F7',ink:'#172033',muted:'#647087',panel:'#FFFFFF',line:'#CCD5E1',blue:'#3578D4',teal:'#2A9D8F',amber:'#E29A32'};
const FONT='Microsoft YaHei';
const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
const Box:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{background:palette.panel,border:`2px solid ${palette.line}`,borderRadius:24,padding:28,...style}}>{children}</div>;

const I2CBusDiagram:React.FC<{scene:TechnicalScene;local:number}>=({scene,local})=>{
 const labels=scene.visual_spec?.labels??['SDA','SCL','START','ADDRESS','ACK/NACK','DATA','STOP'];
 const eventLabels=labels.filter((label)=>label!=='SDA'&&label!=='SCL');
 const focus=scene.visual_spec?.fact_refs[0]??'open_drain';
 const reveal=interpolate(local,[0,24],[0,1],clamp);
 const slots=[430,630,830,1030,1230];
 const sdaPath='M 210 205 H 330 V 285 H 410 V 205 H 490 V 285 H 570 V 205 H 650 V 285 H 730 V 205 H 810 V 285 H 890 V 205 H 970 V 285 H 1050 V 205 H 1130 V 285 H 1210 V 205 H 1410';
 const sclPath='M 210 340 H 270 V 400 H 330 V 340 H 390 V 400 H 450 V 340 H 510 V 400 H 570 V 340 H 630 V 400 H 690 V 340 H 750 V 400 H 810 V 340 H 870 V 400 H 930 V 340 H 990 V 400 H 1050 V 340 H 1110 V 400 H 1170 V 340 H 1230 V 400 H 1290 V 340 H 1410';
 return <div data-layout-box="i2c-bus-diagram" style={{width:'100%',opacity:reveal}}>
  <svg data-i2c-waveform="idle-high-start-address-ack-data-stop" viewBox="0 0 1500 560" width="100%" role="img" aria-label="I2C SDA SCL bus timing and open drain diagram">
   <rect x="12" y="12" width="1476" height="496" rx="28" fill={palette.panel} stroke={palette.line} strokeWidth="4"/>
   <text x="70" y="62" fill={palette.muted} fontSize="26" fontWeight="800">I2C BUS TIMING · OPEN-DRAIN + PULL-UP</text>
   <path d="M105 105V180M230 105V180M105 105H230" stroke={palette.amber} strokeWidth="8" fill="none"/>
   <rect x="128" y="78" width="78" height="58" rx="8" fill={palette.panel} stroke={palette.amber} strokeWidth="5"/><text x="146" y="113" fill={palette.ink} fontSize="22" fontWeight="800">R↑</text>
   <text x="78" y="215" fill={palette.ink} fontSize="28" fontWeight="900">SDA</text><text x="78" y="350" fill={palette.ink} fontSize="28" fontWeight="900">SCL</text>
   <text x="260" y="160" fill={palette.muted} fontSize="22" fontWeight="800">idle-high</text>
   {focus==='rise_time'&&<g data-i2c-focus="rise-time-focus"><rect x="1030" y="75" width="390" height="90" rx="16" fill="#F4F8FF" stroke={palette.blue} strokeWidth="3"/><path d="M1060 140 C1120 135 1140 115 1190 105 S1310 95 1380 95" stroke={palette.blue} strokeWidth="6" fill="none"/><path d="M1060 140 C1120 140 1160 137 1210 130 S1320 105 1380 95" stroke={palette.amber} strokeWidth="6" fill="none"/><text x="1070" y="100" fill={palette.ink} fontSize="20" fontWeight="800">R↑C↑：上升沿变慢</text><text x="1070" y="157" fill={palette.muted} fontSize="18">快 / 慢</text></g>}
   {focus==='sink_current'&&<g data-i2c-focus="sink-current-focus"><rect x="1030" y="75" width="390" height="90" rx="16" fill="#FFF8F0" stroke={palette.amber} strokeWidth="3"/><text x="1065" y="105" fill={palette.ink} fontSize="21" fontWeight="800">R↓ → I_sink↑</text><path d="M1080 135h90M1210 135h90" stroke={palette.amber} strokeWidth="6"/><path d="M1160 125v20M1290 125v20" stroke={palette.ink} strokeWidth="5"/><text x="1065" y="157" fill={palette.muted} fontSize="18">阻值过小：灌电流超限</text></g>}
   <path d={sdaPath} stroke={palette.blue} strokeWidth="9" fill="none"/><path d={sclPath} stroke={palette.teal} strokeWidth="9" fill="none"/>
   {eventLabels.map((label,index)=><g key={label}><line x1={slots[index]} y1="410" x2={slots[index]} y2="435" stroke={palette.line} strokeWidth="3"/><text x={slots[index]} y="455" textAnchor="middle" fill={palette.ink} fontSize="22" fontWeight="800">{label}</text></g>)}
  </svg>
 </div>;
};

const Grammar:React.FC<{scene:TechnicalScene;layout:SceneTextLayout;local:number;fps:number}>=({scene,layout,local,fps})=>{
 const reveal=interpolate(local,[0,Math.min(24,fps)],[0,1],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
 const words=scene.on_screen_knowledge.split(/[，。；:：]/).filter(Boolean).slice(0,4);
 if(scene.visual_spec?.kind==='i2c_bus_v1') return <I2CBusDiagram scene={scene} local={local}/>;
 if(scene.visual_type==='kinetic_typography') return <div data-layout-box="knowledge-kinetic" style={{fontSize:layout.mainFontSize,fontWeight:950,lineHeight:1.18,maxWidth:layout.itemBoxWidth,opacity:reveal,translate:`0 ${(1-reveal)*32}px`}}>{scene.on_screen_knowledge}</div>;
 if(scene.visual_type==='system_diagram') return <div style={{display:'grid',gridTemplateColumns:`repeat(${layout.columns},minmax(0,1fr))`,alignItems:'stretch',gap:20,width:'100%'}}>{words.map((w,i)=><Box key={w} style={{fontSize:layout.itemFontSizes[i],fontWeight:900,opacity:interpolate(local,[i*8,i*8+18],[0,1],clamp),minWidth:0}}><span data-layout-box={`system-node-${i}`}>{w}</span></Box>)}</div>;
 if(scene.visual_type==='timeline') return <div style={{display:'grid',gridTemplateColumns:`repeat(${layout.columns},minmax(0,1fr))`,gap:18,width:'100%'}}>{words.map((w,i)=><Box key={w} style={{borderTop:`9px solid ${[palette.blue,palette.teal,palette.amber][i%3]}`,opacity:interpolate(local,[i*9,i*9+18],[0,1],clamp)}}><b style={{fontSize:22}}>0{i+1}</b><div data-layout-box={`timeline-node-${i}`} style={{fontSize:layout.itemFontSizes[i],fontWeight:900,marginTop:24}}>{w}</div></Box>)}</div>;
 if(scene.visual_type==='comparison_card') return <div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:28,width:'100%'}}><Box style={{borderTop:`9px solid ${palette.blue}`,fontSize:34,fontWeight:900}}>条件<br/><span data-layout-box="comparison-condition" style={{fontSize:layout.itemFontSizes[0],color:palette.muted}}>{words[0]??scene.information_role}</span></Box><Box style={{borderTop:`9px solid ${palette.teal}`,fontSize:34,fontWeight:900}}>结果<br/><span data-layout-box="comparison-result" style={{fontSize:layout.itemFontSizes[1]??layout.itemFontSizes[0],color:palette.muted}}>{words.slice(1).join(' · ')||scene.on_screen_knowledge}</span></Box></div>;
 return <div style={{display:'grid',gap:15,width:'100%'}}>{words.map((w,i)=><Box key={w} style={{display:'flex',gap:20,alignItems:'center',opacity:interpolate(local,[i*8,i*8+16],[0,1],clamp)}}><span style={{color:palette.teal,fontSize:34,fontWeight:950}}>✓</span><span data-layout-box={`checklist-item-${i}`} style={{fontSize:layout.itemFontSizes[i],fontWeight:850}}>{w}</span></Box>)}</div>;
};

const fitBox=(text:string,width:number,maxLines:number,minFont:number,maxFont:number)=>{fitText({text,withinWidth:width,fontFamily:FONT,fontWeight:900});for(let fontSize=maxFont;fontSize>=minFont;fontSize--){const measured=measureText({text,fontFamily:FONT,fontSize,fontWeight:900});if(!Number.isFinite(measured.width)||!Number.isFinite(measured.height))throw new Error('layout_measurement_invalid');const box=fillTextBox({maxBoxWidth:width,maxLines});let overflow=false;for(const character of Array.from(text)){if(box.add({text:character,fontFamily:FONT,fontSize,fontWeight:900}).exceedsBox){overflow=true;break;}}if(!overflow)return fontSize;}throw new Error('layout_text_cannot_fit');};
export const calculateTextLayout=(value:TechnicalExplainerInput)=>{const geometry=ASPECT_GEOMETRY[value.aspect],portrait=value.aspect==='9:16',titleFontSize=fitBox(value.title,geometry.titleMaxWidth,2,geometry.titleMinFont,geometry.titleMaxFont);const scenes:SceneTextLayout[]=value.scenes.map(scene=>{const parts=scene.on_screen_knowledge.split(/[，。；;:：]/).filter(Boolean).slice(0,4),items=parts.length?parts:[scene.on_screen_knowledge],count=items.length;let columns=1,itemBoxWidth=Math.min(1200,geometry.sceneWidth),maxLines=3,maxFontSize=portrait?54:68;if(scene.visual_type==='system_diagram'||scene.visual_type==='timeline'){columns=portrait?Math.min(2,count):count;itemBoxWidth=(geometry.sceneWidth-(columns-1)*20)/columns-56;maxFontSize=30;}if(scene.visual_type==='comparison_card'){columns=2;itemBoxWidth=(geometry.sceneWidth-28)/2-56;maxFontSize=27;}if(scene.visual_type==='checklist'){itemBoxWidth=geometry.sceneWidth-96;maxLines=2;maxFontSize=29;}const itemFontSizes=items.map(part=>fitBox(part,itemBoxWidth,maxLines,geometry.itemMinFont,maxFontSize));return {mainFontSize:fitBox(scene.on_screen_knowledge,itemBoxWidth,maxLines,geometry.itemMinFont,maxFontSize),itemFontSizes,itemBoxWidth,maxLines,minFontSize:geometry.itemMinFont,maxFontSize,columns};});return {method:'layout-utils:measureText+fitText+fillTextBox',geometry,titleFontSize,scenes,limits:{title:{maxLines:2,minFontSize:geometry.titleMinFont},knowledge:{maxLines:3,minFontSize:geometry.itemMinFont}}};};
export const validateTechnicalSceneEvidence=(scene:Pick<TechnicalScene,'scene_index'|'scene_type'|'narrative_role'|'information_role'|'source_refs'|'visual_spec'>)=>{
 const role=scene.information_role,refs=scene.source_refs;
 if(!['hook_question','explain_verified_fact','engineering_process_frame'].includes(role)||!Array.isArray(refs)||refs.some(ref=>typeof ref!=='string'||!ref.trim()))throw new Error('technical_explainer_evidence_invalid');
 if(role==='explain_verified_fact'?refs.length===0:refs.length!==0)throw new Error('technical_explainer_evidence_invalid');
 if(role==='hook_question'&&(scene.scene_index!==1||scene.scene_type!=='hook'||scene.narrative_role!=='hook'))throw new Error('technical_explainer_evidence_invalid');
 if((scene.scene_type==='hook'||scene.narrative_role==='hook')&&role!=='hook_question')throw new Error('technical_explainer_evidence_invalid');
 if(scene.visual_spec!==undefined){const spec=scene.visual_spec;if(spec.kind!=='i2c_bus_v1'||!Array.isArray(spec.fact_refs)||spec.fact_refs.length===0||spec.fact_refs.some(ref=>!refs.includes(ref))||!Array.isArray(spec.labels)||JSON.stringify(spec.labels)!==JSON.stringify(['SDA','SCL','START','ADDRESS','ACK/NACK','DATA','STOP']))throw new Error('technical_explainer_visual_spec_invalid');}
};
export const validateTechnicalExplainer=(value:TechnicalExplainerInput)=>{if(value.schema_version!=='1.0'||value.fps!==30||!['16:9','9:16'].includes(value.aspect)||!Array.isArray(value.scenes)||value.scenes.length<5||!value.title.trim()||value.title.length>80)throw new Error('technical_explainer_input_invalid');let end=0;for(const [i,s] of value.scenes.entries()){validateTechnicalSceneEvidence(s);if(s.scene_index!==i+1||s.start_seconds!==end||s.end_seconds<=s.start_seconds||!s.on_screen_knowledge.trim()||s.on_screen_knowledge.length>(value.aspect==='16:9'?120:90))throw new Error('technical_explainer_scene_invalid');end=s.end_seconds;}if(Math.abs(end-value.duration_seconds)>.001)throw new Error('technical_explainer_duration_invalid');calculateTextLayout(value);return value;};

export const TechnicalExplainer:React.FC<TechnicalExplainerInput>=(input)=>{const frame=useCurrentFrame();const {fps}=useVideoConfig();const textLayout=calculateTextLayout(input);const seconds=frame/fps;const index=Math.max(0,input.scenes.findIndex(s=>seconds>=s.start_seconds&&seconds<s.end_seconds));const scene=input.scenes[index]??input.scenes.at(-1)!;const local=Math.max(0,frame-Math.round(scene.start_seconds*fps));const entrance=spring({frame:local,fps,config:{damping:180}});const portrait=input.aspect==='9:16';return <AbsoluteFill style={{boxSizing:'border-box',background:palette.canvas,color:palette.ink,fontFamily:`${FONT}, sans-serif`,padding:portrait?'84px 72px 360px':'58px 84px 210px'}}>
 <div data-layout-box="eyebrow" style={{fontSize:18,fontWeight:900,letterSpacing:2,color:palette.blue}}>TECHNICAL EXPLAINER · VISUAL ONLY</div>
 <div data-layout-box="title" style={{fontSize:textLayout.titleFontSize,fontWeight:950,lineHeight:1.15,maxWidth:textLayout.geometry.titleMaxWidth,marginTop:18}}>{input.title}</div>
 <div style={{height:5,background:palette.line,marginTop:30}}><div style={{height:'100%',width:`${interpolate(seconds,[0,input.duration_seconds],[0,100],clamp)}%`,background:palette.blue}}/></div>
 <div data-layout-box={`scene-${scene.scene_index}-knowledge`} style={{flex:1,display:'flex',alignItems:'center',opacity:entrance,marginTop:38,width:textLayout.geometry.sceneWidth}}><Grammar scene={scene} layout={textLayout.scenes[index]} local={local} fps={fps}/></div>
 </AbsoluteFill>;};
