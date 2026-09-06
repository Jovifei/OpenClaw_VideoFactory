import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {planReviewFrames, prepareReviewTargets, extractReviewArtifacts, probeVisual, fileSha256} from '../../scripts/lib/phase1_review_artifacts.mjs';

const exec = promisify(execFile);
const segments = (...ends) => ends.map((end, i) => ({index: i + 1,
  scene_start_microseconds: i ? ends[i - 1] : 0, scene_end_microseconds: end}));
const targets = (root) => ({output: path.join(root, 'visual_master.mp4'), report: path.join(root, 'render_report.json'),
  stills: path.join(root, 'stills'), clips: path.join(root, 'clips')});
async function temporary(t) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'phase1 review 中文 '));
  t.after(() => fs.rm(root, {recursive: true, force: true}));
  return root;
}

test('fractional boundary never puts previous-scene frame in next review clip', () => {
  const ranges = planReviewFrames(segments(501000, 1000000), 30);
  assert.deepEqual(ranges.map(r => [r.start_frame, r.end_frame_exclusive]), [[0,16],[16,30]]);
  assert.equal(ranges[0].midpoint_frame, 7);
  assert.equal(ranges[1].midpoint_frame, 22);
});
test('integer-second ranges cover composition exactly once', () => {
  assert.deepEqual(planReviewFrames(segments(1000000, 2000000), 60).map(r=>r.frame_count), [30,30]);
});
test('last end obeys rounded composition duration', () => {
  const ranges = planReviewFrames(segments(501000, 1020000), 31);
  assert.equal(ranges.at(-1).end_frame_exclusive, 31);
  assert.equal(ranges.reduce((n,r)=>n+r.frame_count,0),31);
});
test('range membership agrees with component for thousands of boundary cases', () => {
  for (let boundary=100001; boundary<1900000; boundary+=1999) {
    const ranges=planReviewFrames(segments(boundary,2000000),60);
    for (let frame=0;frame<60;frame++) {
      const expected=frame/30>=boundary/1000000?1:0;
      assert.ok(frame>=ranges[expected].start_frame && frame<ranges[expected].end_frame_exclusive);
    }
  }
});
for (const [name, mutate] of [
  ['gap', s=>{s[1].scene_start_microseconds++;}],
  ['overlap',s=>{s[1].scene_start_microseconds--;}],
  ['NaN',s=>{s[0].scene_end_microseconds=NaN;}],
  ['Infinity',s=>{s[0].scene_end_microseconds=Infinity;}],
  ['string',s=>{s[0].scene_end_microseconds='501000';}],
  ['boolean',s=>{s[0].scene_start_microseconds=false;}],
  ['negative',s=>{s[0].scene_start_microseconds=-1;}],
  ['submicrosecond',s=>{s[0].scene_end_microseconds=.5;}],
  ['wrong index',s=>{s[1].index=1;}],
]) test(`reject ${name} timing`,()=>{const s=segments(501000,1000000);mutate(s);assert.throws(()=>planReviewFrames(s,30),/review_timing_invalid/);});
test('reject zero-frame scenes and total mismatch',()=>{
  assert.throws(()=>planReviewFrames(segments(1,2,1000000),30),/no_frames/);
  assert.throws(()=>planReviewFrames(segments(1000000),31),/duration_mismatch/);
});
test('reject non-30fps, empty and overlong plans',()=>{
  assert.throws(()=>planReviewFrames(segments(1000000),24,24),/frame_plan_invalid/);
  assert.throws(()=>planReviewFrames([],30),/frame_plan_invalid/);
  assert.throws(()=>planReviewFrames(Array(101).fill({}),30),/frame_plan_invalid/);
});
test('fresh targets support spaces and Chinese without shell',async t=>{
  const paths=targets(await temporary(t)); await prepareReviewTargets(paths);
  assert.deepEqual(await fs.readdir(paths.stills),[]);
});
test('existing master and report are never overwritten',async t=>{
  const paths=targets(await temporary(t)); await fs.writeFile(paths.output,'approved');
  await assert.rejects(prepareReviewTargets(paths),/already_exists/);
  assert.equal(await fs.readFile(paths.output,'utf8'),'approved');
  await fs.unlink(paths.output);await fs.writeFile(paths.report,'old report');
  await assert.rejects(prepareReviewTargets(paths),/already_exists/);
});
test('refuse stale, escaping, overlapping and input-as-output paths',async t=>{
  const root=await temporary(t),p=targets(root);
  await prepareReviewTargets(p);await fs.writeFile(path.join(p.stills,'stale.png'),'old');
  await assert.rejects(prepareReviewTargets(p),/not_empty/);
  await assert.rejects(prepareReviewTargets({...p,clips:path.dirname(root)}),/paths_invalid/);
  await assert.rejects(prepareReviewTargets({...p,clips:p.stills}),/paths_invalid/);
  await assert.rejects(prepareReviewTargets({...p,inputs:[p.output]}),/target_is_input/);
});
test('refuse symlink artifact directories',async t=>{
  const root=await temporary(t),p=targets(root);await fs.mkdir(p.clips);
  try {await fs.symlink(p.clips,p.stills,'junction');}
  catch(error) {if(error.code==='EPERM') {t.skip('symlink privilege unavailable');return;}throw error;}
  await assert.rejects(prepareReviewTargets(p),/symlink_forbidden/);
});

async function createMaster(output,{audio=false,frames=60}={}) {
  const args=['-nostdin','-v','error','-n','-f','lavfi','-i','testsrc2=size=160x90:rate=30:duration=2'];
  if(audio)args.push('-f','lavfi','-i','sine=frequency=440:duration=2');
  args.push('-map','0:v:0');if(audio)args.push('-map','1:a:0','-c:a','aac');else args.push('-an');
  args.push('-frames:v',String(frames),'-c:v','libx264','-threads','1','-pix_fmt','yuv420p',output);
  await exec('ffmpeg',args,{timeout:30000});
}
test('real FFmpeg extracts master-bound frames and clips; source is unchanged',async t=>{
  const root=await temporary(t),p=targets(root);await prepareReviewTargets(p);await createMaster(p.output);
  const before=await fileSha256(p.output);
  const result=await extractReviewArtifacts({...p,segments:segments(501000,1111000,2000000),durationInFrames:60,width:160,height:90,
    scenes:[1,2,3].map(scene_index=>({scene_index,visual_type:'timeline'}))});
  assert.equal(result.source_sha256,before);assert.equal(await fileSha256(p.output),before);
  assert.deepEqual(result.entries.map(e=>e.clip.frame_count),[16,18,26]);
  for(const entry of result.entries) {
    assert.equal(entry.source_visual_sha256,before);
    assert.equal(entry.still.sha256,await fileSha256(path.join(root,entry.still.filename)));
    const raw=['-v','error','-i',p.output,'-vf',`select=eq(n\\,${entry.still.frame})`,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'];
    const a=await exec('ffmpeg',raw,{encoding:'buffer',maxBuffer:1000000});
    const b=await exec('ffmpeg',['-v','error','-i',path.join(root,entry.still.filename),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],{encoding:'buffer',maxBuffer:1000000});
    assert.deepEqual(a.stdout,b.stdout,'PNG pixels are from the actual master frame');
  }
  await assert.rejects(fs.stat(p.report),{code:'ENOENT'}); // extraction never approves a job
  await assert.rejects(extractReviewArtifacts({...p,segments:segments(2000000),durationInFrames:60,scenes:[{scene_index:1}]}),/not_empty/);
});
test('real probe rejects unexpected audio, wrong frame count and corruption',async t=>{
  const root=await temporary(t),a=path.join(root,'audio.mp4'),b=path.join(root,'silent.mp4');
  await createMaster(a,{audio:true});await assert.rejects(probeVisual(a),/stream_invalid/);
  await createMaster(b);await assert.rejects(probeVisual(b,{frames:59}),/frames_mismatch/);
  await fs.writeFile(path.join(root,'bad.mp4'),'not a video');
  await assert.rejects(probeVisual(path.join(root,'bad.mp4')),/command_failed/);
});

test('renderer import requires no Remotion install and keeps input-role checks',async()=>{
  const {buildVisualProps}=await import('../../scripts/render_phase1_topic_visual.mjs');
  const script={schema_version:'1.0',script_id:'script',title:'边界测试'};
  const plan={schema_version:'1.0',script_id:'script',scenes:[1,2].map(scene_index=>({scene_index,
    scene_type:'explain',narrative_role:'explain',information_role:'explain_verified_fact',source_refs:['f1'],on_screen_knowledge:'已核验事实'}))};
  const timing={schema_version:'1.0',segments:segments(501000,1000000),visual_duration_seconds:1};
  for(const aspect of ['16:9','9:16'])assert.equal(buildVisualProps(script,plan,timing,aspect).aspect,aspect);
  plan.scenes[0].source_refs=[];assert.throws(()=>buildVisualProps(script,plan,timing,'16:9'),/scene_evidence_invalid/);
  plan.scenes[0].source_refs=['f1'];timing.segments[0].scene_end_microseconds='501000';
  assert.throws(()=>buildVisualProps(script,plan,timing,'16:9'),/review_timing_invalid/);
});
test('entrypoint contains one renderMedia call and no renderStill call',async()=>{
  const text=await fs.readFile(new URL('../../scripts/render_phase1_topic_visual.mjs',import.meta.url),'utf8');
  assert.equal((text.match(/await renderMedia\(/g)||[]).length,1);
  assert.doesNotMatch(text,/renderStill\(/);
  assert.match(text,/await extractReviewArtifacts\(/);
  assert.match(text,/flag: 'wx'/);
});
test('command parser rejects missing, unknown and duplicate flags',async()=>{
  const {parseArgs}=await import('../../scripts/render_phase1_topic_visual.mjs');
  assert.throws(()=>parseArgs([]),/required/);
  assert.throws(()=>parseArgs(['--shell','x']),/invalid/);
  assert.throws(()=>parseArgs(['--aspect','16:9','--aspect','9:16']),/invalid/);
});
test('short master fails before emitting review derivatives or a success report',async t=>{
  const root=await temporary(t),p=targets(root);await prepareReviewTargets(p);await createMaster(p.output,{frames:30});
  await assert.rejects(extractReviewArtifacts({...p,segments:segments(1000000,2000000),durationInFrames:60,
    scenes:[{scene_index:1},{scene_index:2}]}),/frames_mismatch/);
  assert.deepEqual(await fs.readdir(p.stills),[]);assert.deepEqual(await fs.readdir(p.clips),[]);
  await assert.rejects(fs.stat(p.report),{code:'ENOENT'});
});
