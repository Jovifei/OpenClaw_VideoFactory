import React from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export type TechnicalScene = {start_seconds:number; end_seconds:number; scene_index:number; visual_type:'kinetic_typography'|'system_diagram'|'timeline'|'comparison_card'|'checklist'; narration:string; on_screen_knowledge:string; information_role:string; narrative_role:string; shot_intent:string; motion:string; transition:string; source_refs:string[]};
export type TechnicalExplainerInput = {schema_version:'1.0'; title:string; aspect:'16:9'|'9:16'; fps:30; duration_seconds:number; scenes:TechnicalScene[]};

const palette={canvas:'#F2F4F7',ink:'#172033',muted:'#647087',panel:'#FFFFFF',line:'#CCD5E1',blue:'#3578D4',teal:'#2A9D8F',amber:'#E29A32'};
const clamp={extrapolateLeft:'clamp' as const,extrapolateRight:'clamp' as const};
const Box:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{background:palette.panel,border:`2px solid ${palette.line}`,borderRadius:24,padding:28,...style}}>{children}</div>;

const Grammar:React.FC<{scene:TechnicalScene;local:number;fps:number}>=({scene,local,fps})=>{
 const reveal=interpolate(local,[0,Math.min(24,fps)],[0,1],{...clamp,easing:Easing.bezier(.16,1,.3,1)});
 const words=scene.on_screen_knowledge.split(/[，。；:：]/).filter(Boolean).slice(0,4);
 if(scene.visual_type==='kinetic_typography') return <div style={{fontSize:68,fontWeight:950,lineHeight:1.18,maxWidth:1200,opacity:reveal,translate:`0 ${(1-reveal)*32}px`}}>{scene.on_screen_knowledge}</div>;
 if(scene.visual_type==='system_diagram') return <div style={{display:'flex',alignItems:'center',gap:24}}>{words.map((w,i)=><React.Fragment key={w}><Box style={{fontSize:30,fontWeight:900,opacity:interpolate(local,[i*8,i*8+18],[0,1],clamp)}}>{w}</Box>{i<words.length-1&&<div style={{width:70,height:4,background:palette.blue}}/>}</React.Fragment>)}</div>;
 if(scene.visual_type==='timeline') return <div style={{display:'grid',gridTemplateColumns:`repeat(${Math.max(1,words.length)},1fr)`,gap:18,width:'100%'}}>{words.map((w,i)=><Box key={w} style={{borderTop:`9px solid ${[palette.blue,palette.teal,palette.amber][i%3]}`,opacity:interpolate(local,[i*9,i*9+18],[0,1],clamp)}}><b style={{fontSize:22}}>0{i+1}</b><div style={{fontSize:27,fontWeight:900,marginTop:24}}>{w}</div></Box>)}</div>;
 if(scene.visual_type==='comparison_card') return <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:28,width:'100%'}}><Box style={{borderTop:`9px solid ${palette.blue}`,fontSize:34,fontWeight:900}}>条件<br/><span style={{fontSize:27,color:palette.muted}}>{words[0]??scene.information_role}</span></Box><Box style={{borderTop:`9px solid ${palette.teal}`,fontSize:34,fontWeight:900}}>结果<br/><span style={{fontSize:27,color:palette.muted}}>{words.slice(1).join(' · ')||scene.on_screen_knowledge}</span></Box></div>;
 return <div style={{display:'grid',gap:15,width:'100%'}}>{words.map((w,i)=><Box key={w} style={{display:'flex',gap:20,alignItems:'center',opacity:interpolate(local,[i*8,i*8+16],[0,1],clamp)}}><span style={{color:palette.teal,fontSize:34,fontWeight:950}}>✓</span><span style={{fontSize:29,fontWeight:850}}>{w}</span></Box>)}</div>;
};

export const validateTechnicalExplainer=(value:TechnicalExplainerInput)=>{if(value.schema_version!=='1.0'||value.fps!==30||!['16:9','9:16'].includes(value.aspect)||!Array.isArray(value.scenes)||value.scenes.length<5)throw new Error('technical_explainer_input_invalid');let end=0;for(const [i,s] of value.scenes.entries()){if(s.scene_index!==i+1||s.start_seconds!==end||s.end_seconds<=s.start_seconds||!s.on_screen_knowledge.trim()||!s.source_refs.length)throw new Error('technical_explainer_scene_invalid');end=s.end_seconds;}if(Math.abs(end-value.duration_seconds)>.001)throw new Error('technical_explainer_duration_invalid');return value;};

export const TechnicalExplainer:React.FC<TechnicalExplainerInput>=(input)=>{const frame=useCurrentFrame();const {fps}=useVideoConfig();const seconds=frame/fps;const index=Math.max(0,input.scenes.findIndex(s=>seconds>=s.start_seconds&&seconds<s.end_seconds));const scene=input.scenes[index]??input.scenes.at(-1)!;const local=Math.max(0,frame-Math.round(scene.start_seconds*fps));const entrance=spring({frame:local,fps,config:{damping:180}});const portrait=input.aspect==='9:16';return <AbsoluteFill style={{background:palette.canvas,color:palette.ink,fontFamily:'Microsoft YaHei, sans-serif',padding:portrait?'84px 72px 360px':'58px 84px 210px'}}>
 <div style={{fontSize:18,fontWeight:900,letterSpacing:2,color:palette.blue}}>TECHNICAL EXPLAINER · VISUAL ONLY</div>
 <div data-layout-box="title" style={{fontSize:portrait?54:58,fontWeight:950,lineHeight:1.15,maxWidth:portrait?900:1450,marginTop:18}}>{input.title}</div>
 <div style={{height:5,background:palette.line,marginTop:30}}><div style={{height:'100%',width:`${interpolate(seconds,[0,input.duration_seconds],[0,100],clamp)}%`,background:palette.blue}}/></div>
 <div data-layout-box={`scene-${scene.scene_index}-knowledge`} style={{flex:1,display:'flex',alignItems:'center',opacity:entrance,marginTop:38}}><Grammar scene={scene} local={local} fps={fps}/></div>
 <div style={{fontSize:17,color:palette.muted,display:'flex',justifyContent:'space-between'}}><span>{scene.information_role} · {scene.narrative_role}</span><span>{scene.scene_index}/{input.scenes.length} · mascot absent · native-caption reserve</span></div>
 </AbsoluteFill>;};
