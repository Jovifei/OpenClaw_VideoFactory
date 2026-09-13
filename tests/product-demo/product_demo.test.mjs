import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {validateProductInput,sceneFrameRanges,findSceneIndex,isSafeAsset} from '../../remotion/src/product-demo/website-product-contract.mjs';
import {safeUrl,validatePlan,waitForVisibleText} from '../../scripts/product-demo/capture_product_pages.mjs';
import {buildInput} from '../../scripts/product-demo/build_product_input.mjs';
const exec=promisify(execFile),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const base=()=>({schema_version:'1.0',mode:'production_candidate',fps:30,aspect:'9:16',brand:'逐星',website:'photo.joviluma.com',totalFrames:900,
 scriptSha256:'a'.repeat(64),timingSha256:'b'.repeat(64),captureManifestSha256:'c'.repeat(64),captureReviewSha256:'d'.repeat(64),
 scenes:Array.from({length:5},(_,i)=>({id:`s${i+1}`,kind:i===0?'title':i===4?'cta':'capture',startFrame:i*180,endFrame:(i+1)*180,
 headline:'测试标题',detail:'测试，不是正式网站素材。',badge:'测试',asset:i>0&&i<4?`runtime/test/shot${i}.png`:null,
 assetSha256:i>0&&i<4?'e'.repeat(64):null,capturedAt:'2026-09-13T07:00:00Z',attribution:'test attribution'}))});
test('valid dual aspect contract, last frame is last scene',()=>{
 for(const aspect of ['9:16','16:9']){const p=base();p.aspect=aspect;assert.equal(validateProductInput(p,{requireProduction:true}),p);assert.equal(findSceneIndex(p,899),4);}
});
test('preview cannot pass production assertion',()=>{const p=base();p.mode='layout_preview';assert.throws(()=>validateProductInput(p,{requireProduction:true}),/preview_not_production/);});
for(const invalid of ['https://example.com/a.png','../secret.png','C:/s.png','runtime/../s.png','runtime/a/../s.png','runtime/a/x.svg','runtime/a/x.png?secret=x'])
 test(`path rejects ${invalid}`,()=>assert.equal(isSafeAsset(invalid),false));
test('unique scenes required',()=>{const p=base();p.scenes[2].id=p.scenes[1].id;assert.throws(()=>validateProductInput(p),/scene_shape/);});
test('gaps and overlap reject',()=>{for(const delta of [-1,1]){const p=base();p.scenes[2].startFrame+=delta;assert.throws(()=>validateProductInput(p),/scene_shape/);}});
test('CTA must remain at least four seconds',()=>{const p=base();p.scenes[3].endFrame=800;p.scenes[4].startFrame=800;assert.throws(()=>validateProductInput(p),/cta_hold/);});
test('oversized copy rejects',()=>{const p=base();p.scenes[1].headline='字'.repeat(25);assert.throws(()=>validateProductInput(p),/text_budget/);});
test('production capture requires hash and attribution',()=>{const p=base();p.scenes[1].attribution='';assert.throws(()=>validateProductInput(p),/capture_binding/);});
test('frame 15 remains first scene at 0.501s boundary',()=>{
 const ends=[501000,10000000,18000000,25000000,30000000];
 const segments=ends.map((end,i)=>({index:i+1,scene_start_microseconds:i?ends[i-1]:0,scene_end_microseconds:end}));
 const r=sceneFrameRanges(segments,30);assert.equal(r.ranges[0].endFrame,16);assert.equal(r.ranges[1].startFrame,16);
 assert.equal(r.ranges.reduce((sum,x)=>sum+x.endFrame-x.startFrame,0),900);
});
for(const bad of [NaN,Infinity,'6000000',true,-1,0.1])test(`invalid timing ${bad}`,()=>{
 const segments=Array.from({length:5},(_,i)=>({index:i+1,scene_start_microseconds:i*6000000,scene_end_microseconds:(i+1)*6000000}));
 segments[0].scene_end_microseconds=bad;assert.throws(()=>sceneFrameRanges(segments,30));
});
const plan=()=>({schema_version:'1.0',site_origin:'https://photo.joviluma.com',selector_status:'confirmed_against_live_page',viewport:{width:600,height:900},device_scale_factor:2,
 shots:[{id:'home',url:'/',ready_selectors:['.map-stage'],required_text:['逐星'],require_map_tiles:true,actions:[]}]});
test('capture plan fails before inspecting browser unless selectors confirmed',()=>{const p=plan();p.selector_status='needs_local_verification';assert.throws(()=>validatePlan(p),/plan_not_confirmed/);});
test('capture only exact public site paths',()=>{assert.equal(safeUrl('/sites'),'https://photo.joviluma.com/sites');for(const u of ['https://evil.test','http://photo.joviluma.com/','/healthz','/?token=private','https://photo.joviluma.com@evil.test/'])assert.throws(()=>safeUrl(u));});
test('capture preserves the canonical dark-sky panel state',()=>{assert.equal(safeUrl('/?view=light-pollution&panel=sites'),'https://photo.joviluma.com/?view=light-pollution&panel=sites');});
test('required text matching accepts a visible duplicate after a hidden one',async()=>{
 const page={getByText:()=>({count:async()=>2,nth:index=>({isVisible:async()=>index===1})})};
 await waitForVisibleText(page,'景迈山翁基');
});
test('required text errors identify the missing text',async()=>{
 const page={getByText:()=>({count:async()=>0})};
 await assert.rejects(waitForVisibleText(page,'缺失文案'),/required_text_missing:缺失文案/);
});
test('capture plan has explicit readiness',()=>{const p=plan();assert.equal(validatePlan(p),p);p.shots[0].ready_selectors=[];assert.throws(()=>validatePlan(p),/readiness/);});
test('no arbitrary code actions',()=>{const p=plan();p.shots[0].actions=[{type:'evaluate',selector:'body',value:'fetch(...)'}];assert.throws(()=>validatePlan(p),/action/);});
async function fixture(t){
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'product-demo-test-'));
 t.after(()=>fs.rm(root,{recursive:true,force:true}));
 const capturesRoot=path.join(root,'captures'),audioRoot=path.join(root,'audio');
 await fs.mkdir(capturesRoot);await fs.mkdir(audioRoot);
 const png=path.join(capturesRoot,'screen.png'),audio=path.join(audioRoot,'audio.wav');
 await exec('ffmpeg',['-nostdin','-v','error','-f','lavfi','-i','color=c=navy:s=800x800','-frames:v','1','-threads','1',png]);
 await exec('ffmpeg',['-nostdin','-v','error','-f','lavfi','-i','sine=frequency=440:duration=5.9','-c:a','pcm_s16le',audio]);
 const pngHash=sha(await fs.readFile(png)),audioHash=sha(await fs.readFile(audio));
 const script={schema_version:'1.0',script_id:'promo_test',beats:Array.from({length:5},(_,i)=>({id:`s${i+1}`,narration:`测试旁白${i+1}`,subtitle:`测试字幕${i+1}`}))};
 const story={schema_version:'1.0',script_id:'promo_test',shots:script.beats.map((b,i)=>({id:b.id,kind:i===0?'title':i===4?'cta':'capture',capture_id:'screen',headline:'测试标题',detail:'TEST ONLY',badge:'测试',claim_ids:['test_claim']}))};
 const write=async(name,v)=>{const p=path.join(root,name);await fs.writeFile(p,JSON.stringify(v));return p;};
 const scriptFile=await write('script.json',script);
 const timing={schema_version:'1.0',status:'timing_manifest_ready',script:{sha256:sha(await fs.readFile(scriptFile))},timing:{fps:30,authority:'local_jianying_sami_audio_files'},visual_duration_seconds:30,
 voice:{requested_backend:'sami',used_backends:Array(5).fill('sami'),coverage_ratio:29.9/30},
 segments:script.beats.map((b,i)=>({index:i+1,scene_start_microseconds:i*6000000,scene_end_microseconds:(i+1)*6000000,start_microseconds:i*6000000,end_microseconds:i*6000000+5900000,duration_microseconds:5900000,
 narration_sha256:sha(Buffer.from(b.narration)),subtitle_sha256:sha(Buffer.from(b.subtitle)),audio_relative_path:'audio.wav',audio_sha256:audioHash}))};
 // Deliberate unit-test fixture, not a claim of real website or SAMI capture.
 const manifest={schema_version:'1.0',status:'captured_unreviewed',site_origin:'https://photo.joviluma.com',captures:[{id:'screen',filename:'screen.png',sha256:pngHash,source_url:'https://photo.joviluma.com/',captured_at:'2026-09-13T07:00:00Z',status:'captured_unreviewed',method:'live_browser_no_mock',mocked:false}]};
 const capturesFile=await write('captures.json',manifest);
 const review={schema_version:'1.0',review_kind:'local_agent_asset_review',status:'suitable_for_candidate',reviewer:'TEST FIXTURE',capture_manifest_sha256:sha(await fs.readFile(capturesFile)),captures:[{id:'screen',sha256:pngHash,content_verified:true,rights_checked:true,attribution_preserved:true,no_private_data:true,notes:'unit test fixture only',claim_ids:['test_claim'],attribution_text:'TEST ONLY'}]};
 return {script:scriptFile,story:await write('story.json',story),timing:await write('timing.json',timing),captures:capturesFile,review:await write('review.json',review),
  audioRoot,captureRoot:capturesRoot,publicRoot:path.join(root,'public'),assetGroup:'test_attempt',aspect:'9:16',out:path.join(root,'props.json')};
}
async function edit(file,callback){const v=JSON.parse(await fs.readFile(file,'utf8'));callback(v);await fs.writeFile(file,JSON.stringify(v));}
test('build input decodes actual PNG/audio and stages SHA-bound captures',async t=>{const o=await fixture(t);const v=await buildInput(o);assert.equal(v.totalFrames,900);assert.equal(v.mode,'production_candidate');const copied=await fs.readFile(path.join(o.publicRoot,'runtime/test_attempt/screen.png'));assert.equal(sha(copied),v.scenes[1].assetSha256);});
test('source file edit invalidates measured timing',async t=>{const o=await fixture(t);await fs.appendFile(o.script,' ');await assert.rejects(buildInput(o),/measured_sami_binding/);});
test('unreviewed capture cannot be promoted',async t=>{const o=await fixture(t);await edit(o.review,v=>{v.status='pending';});await assert.rejects(buildInput(o),/asset_review_required/);});
test('missing claim binding rejects',async t=>{const o=await fixture(t);await edit(o.review,v=>{v.captures[0].claim_ids=[];});await assert.rejects(buildInput(o),/claim_capture_binding/);});
test('asset bytes tampering rejects',async t=>{const o=await fixture(t);await fs.appendFile(path.join(o.captureRoot,'screen.png'),'changed');await assert.rejects(buildInput(o),/capture_hash_mismatch/);});
test('incorrect measured audio duration rejects',async t=>{const o=await fixture(t);await edit(o.timing,v=>{v.segments[0].end_microseconds=5000000;v.segments[0].duration_microseconds=5000000;});await assert.rejects(buildInput(o),/measured_audio_duration/);});
test('existing runtime group is never overwritten',async t=>{const o=await fixture(t);await buildInput(o);await assert.rejects(buildInput(o),e=>e.code==='EEXIST');});
test('capture source contains no mocks or API fulfill',async()=>{const source=await fs.readFile(new URL('../../scripts/product-demo/capture_product_pages.mjs',import.meta.url),'utf8');assert.doesNotMatch(source,/route\.fulfill|installOpenMeteoMock|installNextApiMock/);});
