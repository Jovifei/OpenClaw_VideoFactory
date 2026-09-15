/** Existing measured SAMI timeline + reviewed real captures -> visual props.
 * Not a renderer, scheduler, Job database, voice generator or formal acceptance gate.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {sceneFrameRanges,validateProductInput,isHash} from '../../remotion/src/product-demo/website-product-contract.mjs';
const exec=promisify(execFile);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const fail=code=>{throw new Error(`product_input:${code}`);};
export async function readJson(file){return JSON.parse(await fs.readFile(file,'utf8'));}
async function safeLocal(root,relative){
  if(typeof relative!=='string'||!relative||relative.includes('\\')||relative.includes(':')||relative.startsWith('/')||
      relative.split('/').some(x=>!x||x==='.'||x==='..'))fail('relative_path');
  const base=path.resolve(root),target=path.resolve(base,relative);let cursor=base;
  // Reject symlinks AND their ancestors; never follow a runtime junction outside the approved root.
  for(let p=base;;p=path.dirname(p)){if((await fs.lstat(p)).isSymbolicLink())fail('symlink');if(path.dirname(p)===p)break;}
  for(const part of relative.split('/')){cursor=path.join(cursor,part);if((await fs.lstat(cursor)).isSymbolicLink())fail('symlink');}
  if(!target.startsWith(base+path.sep)||!(await fs.stat(target)).isFile())fail('file_missing');return target;
}
export async function probeImage(filename){
  await exec('ffmpeg',['-nostdin','-v','error','-xerror','-i',filename,'-map','0:v:0','-f','null','-'],{timeout:30000,shell:false});
  const {stdout}=await exec('ffprobe',['-v','error','-show_streams','-of','json',filename],{timeout:30000,shell:false});
  const {streams}=JSON.parse(stdout),s=streams?.[0];
  if(streams?.length!==1||s.codec_name!=='png'||s.width<600||s.height<600)fail('image_resolution_or_type');
  return {width:s.width,height:s.height};
}
export async function buildInput(o){
  const [script,story,timing,manifest,review]=await Promise.all([o.script,o.story,o.timing,o.captures,o.review].map(readJson));
  const scriptHash=sha(await fs.readFile(o.script)),timingHash=sha(await fs.readFile(o.timing));
  const manifestHash=sha(await fs.readFile(o.captures)),reviewHash=sha(await fs.readFile(o.review));
  if(story.schema_version!=='1.0'||!Array.isArray(story.shots)||!Array.isArray(script.beats)||
      story.script_id!==script.script_id||story.shots.length!==script.beats.length)fail('story_script_binding');
  if(timing.status!=='timing_manifest_ready'||timing.script?.sha256!==scriptHash||timing.timing?.fps!==30||
      timing.timing?.authority!=='local_jianying_sami_audio_files'||timing.voice?.requested_backend!=='sami'||
      !Array.isArray(timing.voice?.used_backends)||!timing.voice.used_backends.length||timing.voice.used_backends.length!==script.beats.length||timing.voice.used_backends.some(x=>String(x).toLowerCase()!=='sami'))fail('measured_sami_binding');
  if(manifest.status!=='captured_unreviewed'||manifest.site_origin!=='https://photo.joviluma.com'||!Array.isArray(manifest.captures))fail('capture_manifest');
  if(review.schema_version!=='1.0'||review.capture_manifest_sha256!==manifestHash||
      review.review_kind!=='local_agent_asset_review'||review.status!=='suitable_for_candidate'||
      typeof review.reviewer!=='string'||!review.reviewer.trim()||!Array.isArray(review.captures))fail('asset_review_required');
  if(!/^[A-Za-z0-9_-]{3,64}$/.test(o.assetGroup))fail('asset_group');
  const {totalFrames,ranges}=sceneFrameRanges(timing.segments,timing.visual_duration_seconds);
  if(timing.segments.length!==script.beats.length)fail('timing_beat_count');
  const captures=new Map(manifest.captures.map(x=>[x.id,x])),reviews=new Map(review.captures.map(x=>[x.id,x]));
  if(captures.size!==manifest.captures.length||reviews.size!==review.captures.length)fail('duplicate_capture');
  const assets=[],scenes=[]; let previousVoiceEnd=0;
  for(const [i,shot] of story.shots.entries()){
    const beat=script.beats[i],seg=timing.segments[i];
    if(beat.id!==shot.id||!beat.narration||!beat.subtitle||
        seg.narration_sha256!==sha(Buffer.from(beat.narration,'utf8'))||
        seg.subtitle_sha256!==sha(Buffer.from(beat.subtitle,'utf8'))||seg.subsegments)fail('narration_binding');
    if(!Number.isSafeInteger(seg.start_microseconds)||!Number.isSafeInteger(seg.end_microseconds)||
        seg.start_microseconds<previousVoiceEnd||seg.start_microseconds!==seg.scene_start_microseconds||
        seg.end_microseconds<=seg.start_microseconds||seg.end_microseconds>seg.scene_end_microseconds)fail('voice_range');
    previousVoiceEnd=seg.end_microseconds;
    if(!isHash(seg.audio_sha256))fail('audio_hash');
    const audio=await safeLocal(o.audioRoot,seg.audio_relative_path);
    if(sha(await fs.readFile(audio))!==seg.audio_sha256)fail('audio_hash_mismatch');
    if(!Number.isSafeInteger(seg.duration_microseconds)||seg.duration_microseconds!==seg.end_microseconds-seg.start_microseconds)fail('audio_duration_contract');
    const {stdout: audioProbe}=await exec('ffprobe',['-v','error','-show_streams','-show_format','-of','json',audio],{timeout:30000,shell:false});
    const probe=JSON.parse(audioProbe);
    const audioSeconds=Number(probe.format?.duration);
    if(probe.streams?.length!==1||probe.streams[0].codec_type!=='audio'||!Number.isFinite(audioSeconds)||
        Math.abs(audioSeconds*1e6-seg.duration_microseconds)>33334)fail('measured_audio_duration_mismatch');
    await exec('ffmpeg',['-nostdin','-v','error','-xerror','-i',audio,'-map','0:a:0','-f','null','-'],{timeout:30000,shell:false});
    // Still reuse factory final preview validator for mux/subtitle synchronization; this is not that gate.
    const scene={id:shot.id,kind:shot.kind,...ranges[i],headline:shot.headline,detail:shot.detail,badge:shot.badge,
      visualRole:shot.visual_role??shot.visualRole,focus:shot.focus??null,asset:null,assetSha256:null,capturedAt:'',attribution:''};
    if(shot.kind==='capture'){
      const capture=captures.get(shot.capture_id),check=reviews.get(shot.capture_id);
      if(!capture||capture.method!=='live_browser_no_mock'||capture.mocked!==false||capture.status!=='captured_unreviewed'||
          !check||check.sha256!==capture.sha256||check.content_verified!==true||check.rights_checked!==true||
          check.attribution_preserved!==true||check.no_private_data!==true||!check.notes?.trim())fail('capture_not_reviewed');
      if(!Array.isArray(shot.claim_ids)||shot.claim_ids.some(x=>!check.claim_ids?.includes(x)))fail('claim_capture_binding');
      const u=new URL(capture.source_url);if(u.origin!=='https://photo.joviluma.com')fail('capture_origin');
      const file=await safeLocal(o.captureRoot,capture.filename),bytes=await fs.readFile(file);
      if(sha(bytes)!==capture.sha256)fail('capture_hash_mismatch');
      await probeImage(file);
      scene.asset=`runtime/${o.assetGroup}/${shot.capture_id}.png`;scene.assetSha256=capture.sha256;
      scene.capturedAt=capture.captured_at;scene.attribution=check.attribution_text;
      scene.captureViewport=capture.viewport||null;scene.captureDeviceScaleFactor=capture.device_scale_factor||null;
      assets.push({relative:scene.asset,bytes});
    }
    scenes.push(scene);
  }
  const totalUs=Math.round(timing.visual_duration_seconds*1e6),coverage=previousVoiceEnd/totalUs;
  if(coverage<0.75||coverage>1||!Number.isFinite(timing.voice.coverage_ratio)||Math.abs(timing.voice.coverage_ratio-coverage)>1e-6)fail('voice_coverage');
  const props={schema_version:'1.0',mode:'production_candidate',fps:30,aspect:o.aspect,brand:'逐星',website:'photo.joviluma.com',
    totalFrames,scriptSha256:scriptHash,timingSha256:timingHash,captureManifestSha256:manifestHash,captureReviewSha256:reviewHash,scenes};
  validateProductInput(props,{requireProduction:true});
  // No writes until all source, timing, rights and image checks pass. New, non-junction runtime group only.
  const publicRoot=path.resolve(o.publicRoot);await fs.mkdir(publicRoot,{recursive:true});
  for(let p=publicRoot;;p=path.dirname(p)){if((await fs.lstat(p)).isSymbolicLink())fail('public_root_symlink');if(path.dirname(p)===p)break;}
  const runtime=path.join(publicRoot,'runtime');await fs.mkdir(runtime,{recursive:true});
  if((await fs.lstat(runtime)).isSymbolicLink())fail('public_runtime_symlink');
  const group=path.join(runtime,o.assetGroup);await fs.mkdir(group,{recursive:false});
  for(const a of assets){const destination=path.join(publicRoot,...a.relative.split('/'));
    try{await fs.writeFile(destination,a.bytes,{flag:'wx'});}catch(e){if(e.code!=='EEXIST')throw e;
      if(sha(await fs.readFile(destination))!==sha(a.bytes))fail('conflicting_asset');}}
  await fs.writeFile(o.out,JSON.stringify(props,null,2)+'\n',{flag:'wx'});
  return props;
}
const cliFlags=['--script','--story','--timing','--captures','--review','--audio-root','--capture-root','--public-root','--asset-group','--aspect','--out'];
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const a={};const argv=process.argv.slice(2);
  for(let i=0;i<argv.length;i+=2){if(!cliFlags.includes(argv[i])||!argv[i+1]||argv[i+1].startsWith('--')||a[argv[i]])fail('arguments');a[argv[i]]=argv[i+1];}
  if(cliFlags.some(k=>!a[k]))fail('arguments');
  buildInput({script:a['--script'],story:a['--story'],timing:a['--timing'],captures:a['--captures'],review:a['--review'],
    audioRoot:a['--audio-root'],captureRoot:a['--capture-root'],publicRoot:a['--public-root'],assetGroup:a['--asset-group'],
    aspect:a['--aspect'],out:a['--out']}).then(r=>console.log(JSON.stringify({status:'visual_input_prepared_not_rendered',frames:r.totalFrames})))
    .catch(e=>{console.error(e.message);process.exitCode=1;});
}
