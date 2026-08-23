import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const remotionRequire = createRequire(path.join(ROOT, 'remotion', 'package.json'));
const {bundle} = remotionRequire('@remotion/bundler');
const {renderMedia, renderStill, selectComposition} = remotionRequire('@remotion/renderer');
const primaryTypescript = remotionRequire.resolve('typescript');
remotionRequire(primaryTypescript);
remotionRequire.cache[primaryTypescript].exports = remotionRequire('typescript-remotion');
const execFileAsync = promisify(execFile);
const APPROVED_CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
];

const sha256 = (buffer) => crypto.createHash('sha256').update(buffer).digest('hex');

function parseArgs(argv) {
  const values = {};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!['--script', '--storyboard', '--output', '--report', '--timing'].includes(key) || values[key]) throw new Error('arguments_invalid');
    const value = argv[++i];
    if (!value || value.startsWith('--')) throw new Error('arguments_invalid');
    values[key] = value;
  }
  for (const key of ['--script', '--storyboard', '--output', '--report', '--timing']) {
    if (!values[key]) throw new Error('arguments_required');
  }
  return values;
}

async function approvedChrome() {
  for (const candidate of APPROVED_CHROME) {
    try {
      const stat = await fs.stat(candidate);
      if (stat.isFile()) return candidate;
    } catch {
      // Try the next approved installation.
    }
  }
  throw new Error('approved_chrome_missing');
}

function buildInput(script, storyboard, timing) {
  if (!script || !Array.isArray(script.beats) || script.beats.length !== 5) throw new Error('script_must_have_five_beats');
  if (!storyboard || storyboard.aspect_ratio !== '9:16' || storyboard.canvas?.width !== 1080 || storyboard.canvas?.height !== 1920) throw new Error('storyboard_canvas_invalid');
  if (!timing || timing.schema_version !== '1.0' || !Array.isArray(timing.segments) || timing.segments.length !== 5) throw new Error('timing_manifest_invalid');
  const durationSeconds = Number(timing.visual_duration_seconds);
  if (!Number.isFinite(durationSeconds) || durationSeconds < 25 || durationSeconds > 120) throw new Error('timing_visual_duration_invalid');
  const kinds = ['hook', 'topology', 'bode', 'phasor', 'summary'];
  return {
    schema_version: '1.0',
    title: String(script.title || 'RC 高通滤波器：从分水岭到相位超前'),
    duration_seconds: durationSeconds,
    fps: 30,
    layout_contract_version: '1.0',
    scenes: script.beats.map((beat, index) => {
      const segment = timing.segments[index];
      const startSeconds = Number(segment.scene_start_microseconds) / 1_000_000;
      const endSeconds = Number(segment.scene_end_microseconds) / 1_000_000;
      if (!Number.isFinite(startSeconds) || !Number.isFinite(endSeconds) || endSeconds <= startSeconds) throw new Error('timing_scene_range_invalid');
      if (beat.visual_kind !== kinds[index]) throw new Error('script_visual_kind_invalid');
      return {
        start_seconds: startSeconds,
        end_seconds: endSeconds,
        heading: String(beat.subtitle || ''),
        visual_kind: kinds[index],
        timing_segment_index: index + 1,
      };
    }),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scriptPath = path.resolve(args['--script']);
  const storyboardPath = path.resolve(args['--storyboard']);
  const outputPath = path.resolve(args['--output']);
  const reportPath = path.resolve(args['--report']);
  const timingPath = path.resolve(args['--timing']);
  if ([outputPath, reportPath].some((value) => value.toUpperCase().startsWith('C:'))) throw new Error('c_drive_output_forbidden');
  const [script, storyboard, timing, scriptBytes, storyboardBytes, timingBytes] = await Promise.all([
    fs.readFile(scriptPath, 'utf8').then(JSON.parse),
    fs.readFile(storyboardPath, 'utf8').then(JSON.parse),
    fs.readFile(timingPath, 'utf8').then(JSON.parse),
    fs.readFile(scriptPath),
    fs.readFile(storyboardPath),
    fs.readFile(timingPath),
  ]);
  const scriptSha = sha256(scriptBytes);
  if (timing.script?.sha256 && timing.script.sha256 !== scriptSha) throw new Error('timing_manifest_script_mismatch');
  const inputProps = buildInput(script, storyboard, timing);
  await fs.mkdir(path.dirname(outputPath), {recursive: true});
  await fs.mkdir(path.dirname(reportPath), {recursive: true});
  const chrome = await approvedChrome();
  const serveUrl = await bundle({entryPoint: path.join(ROOT, 'remotion', 'src', 'index.ts')});
  const composition = await selectComposition({serveUrl, id: 'RcHighPass1080x1920', inputProps, browserExecutable: chrome});
  const previewPath = path.join(path.dirname(outputPath), `${path.basename(outputPath, path.extname(outputPath))}.preview.png`);
  const rawPath = path.join(path.dirname(outputPath), `${path.basename(outputPath, path.extname(outputPath))}.raw.mp4`);
  await renderStill({composition, serveUrl, inputProps, frame: 30, output: previewPath, scale: 0.25, browserExecutable: chrome, imageFormat: 'png', logLevel: 'error'});
  await renderMedia({
    composition,
    serveUrl,
    inputProps,
    outputLocation: rawPath,
    browserExecutable: chrome,
    codec: 'h264',
    enforceAudioTrack: false,
    concurrency: 1,
    logLevel: 'warn',
  });
  await execFileAsync('ffmpeg', ['-y', '-nostdin', '-v', 'error', '-i', rawPath, '-map', '0:v:0', '-c:v', 'copy', '-an', outputPath], {timeout: 900000});
  await fs.rm(rawPath, {force: true});
  const [outputBytes, previewBytes] = await Promise.all([fs.readFile(outputPath), fs.readFile(previewPath)]);
  const report = {
    schema_version: '1.0',
    status: 'remotion_visual_ready_for_post_render_gate',
    renderer: 'remotion',
    composition: composition.id,
    input: {
      script_filename: path.basename(scriptPath),
      script_sha256: scriptSha,
      storyboard_filename: path.basename(storyboardPath),
      storyboard_sha256: sha256(storyboardBytes),
      timing_manifest_filename: path.basename(timingPath),
      timing_manifest_sha256: sha256(timingBytes),
    },
    visual: {
      filename: path.basename(outputPath),
      sha256: sha256(outputBytes),
      width: 1080,
      height: 1920,
      fps: 30,
      duration_seconds: inputProps.duration_seconds,
      audio_present: false,
      burned_in_subtitles: false,
      scene_timing: inputProps.scenes.map((scene) => ({
        start_seconds: scene.start_seconds,
        end_seconds: scene.end_seconds,
        visual_kind: scene.visual_kind,
        timing_segment_index: scene.timing_segment_index,
      })),
    },
    layout_contract: {
      version: '1.0',
      safe_area: {left: 72, right: 72, top: 68, bottom: 180},
      subtitle_reserve: {top: 1590, height: 220, authority: 'jianying_native'},
      text_policy: 'bounded_natural_wrap',
      overflow_policy: 'fail_closed',
      theme_token: 'technical_neutral',
      background_is_theme_driven: true,
      pink_global_background: false,
    },
    preview: {filename: path.basename(previewPath), sha256: sha256(previewBytes), frame: 30, scale: 0.25},
    outputs_on_e_drive: true,
    sync_contract: {
      status: 'voice_first_manifest_driven',
      authority: 'jianying_voice_timing_manifest',
      remotion_scene_boundaries_are_voice_boundaries: true,
      subtitle_authority: 'jianying_native_subtitles_track',
    },
    automatic_export: false,
  };
  await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify(report));
}

try {
  await main();
} catch (error) {
  console.error(error instanceof Error ? error.message : 'render_failed');
  process.exitCode = 1;
}
