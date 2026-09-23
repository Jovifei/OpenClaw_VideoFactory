import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {assertAbsent, extractReviewArtifacts, planReviewFrames, prepareReviewTargets} from './lib/phase1_review_artifacts.mjs';
import {validateProductInput} from '../remotion/src/product-demo/website-product-contract.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TECHNICAL_FLAGS = ['--script', '--scene-plan', '--timing-manifest', '--aspect', '--output', '--report', '--stills-dir', '--clips-dir'];
const PRODUCT_FLAGS = ['--product-input', '--timing-manifest', '--aspect', '--output', '--report', '--stills-dir', '--clips-dir'];
const FLAGS = [...new Set([...TECHNICAL_FLAGS, ...PRODUCT_FLAGS])];
const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'];
const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const execute = promisify(execFile);

export function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 2) {
    if (!FLAGS.includes(argv[i]) || out[argv[i]] || !argv[i + 1] || argv[i + 1].startsWith('--')) throw Error('arguments_invalid');
    out[argv[i]] = argv[i + 1];
  }
  const product = Boolean(out['--product-input']);
  const allowed = product ? PRODUCT_FLAGS : TECHNICAL_FLAGS;
  if (Object.keys(out).some((key) => !allowed.includes(key)) || allowed.some((key) => !out[key])) throw Error('arguments_required');
  return out;
}

async function chrome() {
  for (const value of CHROME) {
    try {if ((await fs.stat(value)).isFile()) return value;} catch {}
  }
  throw Error('approved_chrome_missing');
}

function eDrive(value) {
  const resolved = path.resolve(value);
  if (!/^E:[\\/]/i.test(resolved)) throw Error('output_must_use_e_drive');
  return resolved;
}

async function renderMediaOnce({compositionId, inputProps, output, aspect}) {
  const rawOutput = `${output}.raw.mp4`;
  await assertAbsent(rawOutput);

  // Keep the pinned local Remotion/TypeScript setup and approved browser policy.
  // Lazy loading lets offline contract tests run without installing Remotion.
  const req = createRequire(path.join(ROOT, 'remotion', 'package.json'));
  const {bundle} = req('@remotion/bundler');
  const {renderMedia, selectComposition} = req('@remotion/renderer');
  const ts = req.resolve('typescript');
  req(ts);
  req.cache[ts].exports = req('typescript-remotion');
  const browserExecutable = await chrome();
  const serveUrl = await bundle({entryPoint: path.join(ROOT, 'remotion', 'src', 'index.ts')});
  const composition = await selectComposition({serveUrl, id: compositionId, inputProps, browserExecutable});
  const durationInFrames = Number.isInteger(inputProps.totalFrames)
    ? inputProps.totalFrames
    : Math.round(inputProps.duration_seconds * 30);
  const landscape = aspect === '16:9';
  const width = landscape ? 1920 : 1080;
  const height = landscape ? 1080 : 1920;
  if (composition.durationInFrames !== durationInFrames || composition.fps !== 30 ||
      composition.width !== width || composition.height !== height) throw Error('composition_contract_mismatch');

  // Exactly one Chromium render. Stills/clips below are derivatives of this MP4,
  // not separately rendered versions that could diverge from the reviewed master.
  await renderMedia({composition, serveUrl, inputProps, outputLocation: rawOutput, browserExecutable,
    codec: 'h264', concurrency: 1, logLevel: 'warn', muted: true, overwrite: false});
  await execute('ffmpeg', ['-n', '-nostdin', '-v', 'error', '-i', rawOutput, '-map', '0:v:0', '-c:v', 'copy', '-an', '-sn', '-dn', output],
    {timeout: 300000, windowsHide: true, shell: false});
  await fs.rm(rawOutput); // only this attempt's temporary intermediate, after validation
  return {durationInFrames, width, height, serveUrl};
}

/** Preserve the existing scene/source-role contracts before any render starts. */
export function buildVisualProps(script, plan, timing, aspect) {
  if (script.schema_version !== '1.0' || plan.schema_version !== '1.0' || timing.schema_version !== '1.0' ||
      !['16:9', '9:16'].includes(aspect) || Object.keys(plan).sort().join(',') !== 'scenes,schema_version,script_id' ||
      plan.script_id !== script.script_id || !Array.isArray(plan.scenes) || !Array.isArray(timing.segments) ||
      plan.scenes.length !== timing.segments.length) throw Error('visual_input_invalid');
  if (!String(script.title || '').trim() || String(script.title).length > 80) throw Error('layout_text_overflow_preflight');
  let end = 0;
  const scenes = plan.scenes.map((scene, i) => {
    const segment = timing.segments[i];
    const start = Number(segment.scene_start_microseconds) / 1e6;
    const finish = Number(segment.scene_end_microseconds) / 1e6;
    if (segment.index !== i + 1 || scene.scene_index !== i + 1 || start !== end || finish <= start) throw Error('scene_boundaries_not_contiguous');
    const role = scene.information_role, refs = scene.source_refs;
    if (!['hook_question', 'explain_verified_fact', 'engineering_process_frame'].includes(role) ||
        !Array.isArray(refs) || refs.some((ref) => typeof ref !== 'string' || !ref.trim())) throw Error('scene_evidence_invalid');
    if (role === 'explain_verified_fact' ? refs.length === 0 : refs.length !== 0) throw Error('scene_evidence_invalid');
    if (role === 'hook_question' && (i !== 0 || scene.scene_type !== 'hook' || scene.narrative_role !== 'hook')) throw Error('scene_evidence_invalid');
    if ((scene.scene_type === 'hook' || scene.narrative_role === 'hook') && role !== 'hook_question') throw Error('scene_evidence_invalid');
    if (!String(scene.on_screen_knowledge || '').trim() || String(scene.on_screen_knowledge).length > (aspect === '16:9' ? 120 : 90)) throw Error('layout_text_overflow_preflight');
    end = finish;
    return {...scene, start_seconds: start, end_seconds: finish};
  });
  if (!Number.isFinite(timing.visual_duration_seconds) || Math.abs(end - timing.visual_duration_seconds) > .000001) throw Error('visual_duration_mismatch');
  planReviewFrames(timing.segments, Math.round(end * 30));
  return {schema_version: '1.0', title: String(script.title), aspect, fps: 30, duration_seconds: end, scenes};
}

export async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  if (args['--product-input']) return renderProduct(args);
  const scriptPath = path.resolve(args['--script']), planPath = path.resolve(args['--scene-plan']);
  const timingPath = path.resolve(args['--timing-manifest']), aspect = args['--aspect'];
  const output = eDrive(args['--output']), report = eDrive(args['--report']);
  const stills = eDrive(args['--stills-dir']), clips = eDrive(args['--clips-dir']);
  const scriptBytes = await fs.readFile(scriptPath), planBytes = await fs.readFile(planPath), timingBytes = await fs.readFile(timingPath);
  const script = JSON.parse(scriptBytes), plan = JSON.parse(planBytes), timing = JSON.parse(timingBytes);
  if (timing.script?.sha256 !== sha(scriptBytes)) throw Error('script_hash_mismatch');
  if (timing.scene_plan?.sha256 !== sha(planBytes)) throw Error('scene_plan_hash_mismatch');
  const inputProps = buildVisualProps(script, plan, timing, aspect);
  await prepareReviewTargets({output, report, stills, clips, inputs: [scriptPath, planPath, timingPath]});
  const rendered = await renderMediaOnce({compositionId: 'TechnicalExplainer', inputProps, output, aspect});
  const {durationInFrames, width, height} = rendered;
  const derived = await extractReviewArtifacts({output, report, stills, clips, segments: timing.segments,
    durationInFrames, width, height, scenes: inputProps.scenes});
  const landscape = aspect === '16:9';
  const value = {
    schema_version: '1.0', status: 'passed', renderer: 'remotion', composition: 'TechnicalExplainer',
    input: {script_filename: path.basename(scriptPath), script_sha256: sha(scriptBytes),
      scene_plan_filename: path.basename(planPath), scene_plan_sha256: sha(planBytes),
      timing_manifest_filename: path.basename(timingPath), timing_manifest_sha256: sha(timingBytes)},
    visual: {filename: path.relative(path.dirname(report), output).replaceAll('\\', '/'), sha256: derived.source_sha256,
      width, height, fps: 30, duration_seconds: inputProps.duration_seconds, audio_present: false,
      burned_in_subtitles: false, scene_timing: derived.entries},
    review_derivation: {method: 'ffmpeg_from_visual_master_v1', remotion_render_calls: 1,
      source_visual_sha256: derived.source_sha256, decoded_master_frames: derived.media.frames,
      clip_encoding: 'libx264_crf18_review_only', frame_intervals: 'half_open'},
    layout_contract: {version: '1.0', aspect,
      safe_area: landscape ? {left: 84, right: 84, top: 58, bottom: 210} : {left: 72, right: 72, top: 84, bottom: 360},
      subtitle_reserve: landscape ? {top: 870, height: 150} : {top: 1560, height: 240},
      text_policy: 'bounded_natural_wrap', overflow_policy: 'fail_closed', theme_token: 'technical_neutral',
      background_is_theme_driven: true, pink_global_background: false, data_layout_box: true,
      validation_method: '@remotion/layout-utils@4.0.500:measureText+fitText+fillTextBox',
      limits: {title: {max_lines: 2, min_font_size: landscape ? 42 : 40}, knowledge: {max_lines: 3, min_font_size: landscape ? 24 : 22}}},
    mascot: {mode: 'off', present: false}, outputs_on_e_drive: true,
  };
  await fs.writeFile(report, JSON.stringify(value, null, 2) + '\n', {flag: 'wx', encoding: 'utf8'});
  console.log(JSON.stringify(value));
  return value;
}

async function renderProduct(args) {
  const productInputPath = path.resolve(args['--product-input']);
  const timingPath = path.resolve(args['--timing-manifest']);
  const aspect = args['--aspect'];
  const output = eDrive(args['--output']);
  const report = eDrive(args['--report']);
  const stills = eDrive(args['--stills-dir']);
  const clips = eDrive(args['--clips-dir']);
  const productBytes = await fs.readFile(productInputPath);
  const timingBytes = await fs.readFile(timingPath);
  const inputProps = validateProductInput(JSON.parse(productBytes), {requireProduction: true});
  const timing = JSON.parse(timingBytes);
  if (inputProps.aspect !== aspect || sha(timingBytes) !== inputProps.timingSha256 ||
      timing.status !== 'timing_manifest_ready' || !Array.isArray(timing.segments) ||
      timing.segments.length !== inputProps.scenes.length ||
      Math.round(Number(timing.visual_duration_seconds) * 30) !== inputProps.totalFrames) {
    throw Error('product_timing_contract_invalid');
  }
  await prepareReviewTargets({output, report, stills, clips, inputs: [productInputPath, timingPath]});
  const rendered = await renderMediaOnce({compositionId: 'WebsiteProductDemo', inputProps, output, aspect});
  const reviewScenes = inputProps.scenes.map((scene, index) => ({...scene, scene_index: index + 1, visual_type: `website_${scene.kind}`}));
  const focusSceneCount = inputProps.scenes.filter(scene => scene.focus).length;
  const derived = await extractReviewArtifacts({output, report, stills, clips, segments: timing.segments,
    durationInFrames: rendered.durationInFrames, width: rendered.width, height: rendered.height, scenes: reviewScenes});
  const value = {
    schema_version: '1.0', status: 'passed', content_kind: 'website_product_promo',
    renderer: 'remotion', composition: 'WebsiteProductDemo',
    input: {product_input_filename: path.basename(productInputPath), product_input_sha256: sha(productBytes),
      timing_manifest_filename: path.basename(timingPath), timing_manifest_sha256: sha(timingBytes),
      capture_manifest_sha256: inputProps.captureManifestSha256, capture_review_sha256: inputProps.captureReviewSha256},
    visual: {filename: path.relative(path.dirname(report), output).replaceAll('\\', '/'), sha256: derived.source_sha256,
      width: rendered.width, height: rendered.height, fps: 30, duration_seconds: inputProps.totalFrames / 30,
      audio_present: false, burned_in_subtitles: false, scene_timing: derived.entries},
    review_derivation: {method: 'ffmpeg_from_visual_master_v1', remotion_render_calls: 1,
      source_visual_sha256: derived.source_sha256, decoded_master_frames: derived.media.frames,
      clip_encoding: 'libx264_crf18_review_only', frame_intervals: 'half_open'},
    layout_contract: {version: 'website_product_demo_v1', aspect,
      safe_area: aspect === '16:9' ? {left: 96, right: 96, top: 72, bottom: 72} : {left: 76, right: 76, top: 154, bottom: 135},
      subtitle_reserve: aspect === '16:9' ? {top: 918, height: 68} : {top: 1640, height: 120},
       screenshot_fit: focusSceneCount ? 'focus_crop' : 'contain', focus_scene_count: focusSceneCount, attribution_preserved: true},
    mascot: {mode: 'off', present: false},
    human_review_required: true, automatic_export: false, outputs_on_e_drive: true,
  };
  await fs.writeFile(report, JSON.stringify(value, null, 2) + '\n', {flag: 'wx', encoding: 'utf8'});
  console.log(JSON.stringify(value));
  return value;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {console.error(error instanceof Error ? error.message : 'render_failed'); process.exitCode = 1;});
}
