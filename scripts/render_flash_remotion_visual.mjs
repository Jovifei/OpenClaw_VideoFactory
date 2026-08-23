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
    if (!['--script', '--output', '--report', '--timing'].includes(key) || values[key]) throw new Error('arguments_invalid');
    const value = argv[++i];
    if (!value || value.startsWith('--')) throw new Error('arguments_invalid');
    values[key] = value;
  }
  if (!values['--script'] || !values['--output'] || !values['--report'] || !values['--timing']) throw new Error('arguments_required');
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

function buildInput(script, timing) {
  if (!script || !Array.isArray(script.beats) || script.beats.length !== 5) throw new Error('script_must_have_five_beats');
  if (!timing || timing.schema_version !== '1.0' || !Array.isArray(timing.segments) || timing.segments.length !== 5) {
    throw new Error('timing_manifest_invalid');
  }
  const durationSeconds = Number(timing.visual_duration_seconds);
  if (!Number.isFinite(durationSeconds) || durationSeconds < 25 || durationSeconds > 60) throw new Error('timing_visual_duration_invalid');
  const headings = [
    '擦除动作与独立看门狗同时运行',
    '把操作拆成四个可观察阶段',
    '先测最坏擦除时间，再计算窗口',
    '超出预算时进入受控恢复',
    '四项检查，避免无界重试',
  ];
  return {
    schema_version: '1.0',
    title: String(script.title || 'Flash 擦除时，如何安排看门狗服务窗口').replace(',', '，'),
    duration_seconds: durationSeconds,
    fps: 30,
    scenes: script.beats.map((beat, index) => {
      const segment = timing.segments[index];
      const startSeconds = Number(segment.scene_start_microseconds) / 1_000_000;
      const endSeconds = Number(segment.scene_end_microseconds) / 1_000_000;
      if (!Number.isFinite(startSeconds) || !Number.isFinite(endSeconds) || endSeconds <= startSeconds) throw new Error('timing_scene_range_invalid');
      return {
        start_seconds: startSeconds,
        end_seconds: endSeconds,
        heading: headings[index],
        visual_kind: ['window', 'sequence', 'budget', 'recovery', 'checklist'][index],
        source_subtitle: String(beat.subtitle || ''),
        timing_segment_index: index + 1,
      };
    }),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scriptPath = path.resolve(args['--script']);
  const outputPath = path.resolve(args['--output']);
  const reportPath = path.resolve(args['--report']);
  const timingPath = path.resolve(args['--timing']);
  if (outputPath.toUpperCase().startsWith('C:') || reportPath.toUpperCase().startsWith('C:')) throw new Error('c_drive_output_forbidden');
  const script = JSON.parse(await fs.readFile(scriptPath, 'utf8'));
  const timing = JSON.parse(await fs.readFile(timingPath, 'utf8'));
  const scriptBytes = await fs.readFile(scriptPath);
  const timingBytes = await fs.readFile(timingPath);
  const scriptSha = sha256(scriptBytes);
  if (timing.script?.sha256 && timing.script.sha256 !== scriptSha) throw new Error('timing_manifest_script_mismatch');
  const inputProps = buildInput(script, timing);
  await fs.mkdir(path.dirname(outputPath), {recursive: true});
  await fs.mkdir(path.dirname(reportPath), {recursive: true});
  const chrome = await approvedChrome();
  const serveUrl = await bundle({entryPoint: path.join(ROOT, 'remotion', 'src', 'index.ts')});
  const composition = await selectComposition({serveUrl, id: 'FlashWatchdog16x9', inputProps, browserExecutable: chrome});
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
  await execFileAsync('ffmpeg', ['-y', '-nostdin', '-v', 'error', '-i', rawPath, '-map', '0:v:0', '-c:v', 'copy', '-an', outputPath], {timeout: 300000});
  await fs.rm(rawPath, {force: true});
  const [outputBytes, previewBytes] = await Promise.all([
    fs.readFile(outputPath),
    fs.readFile(previewPath),
  ]);
  const report = {
    schema_version: '1.0',
    status: 'remotion_visual_ready_for_jianying',
    renderer: 'remotion',
    composition: composition.id,
    input: {
      script_filename: path.basename(scriptPath),
      script_sha256: scriptSha,
      timing_manifest_filename: path.basename(timingPath),
      timing_manifest_sha256: sha256(timingBytes),
    },
    visual: {
      filename: path.basename(outputPath),
      sha256: sha256(outputBytes),
      width: 1920,
      height: 1080,
      fps: 30,
      duration_seconds: inputProps.duration_seconds,
      audio_present: false,
      burned_in_subtitles: false,
      scene_timing: inputProps.scenes.map((scene) => ({
        start_seconds: scene.start_seconds,
        end_seconds: scene.end_seconds,
        timing_segment_index: scene.timing_segment_index,
      })),
    },
    preview: {filename: path.basename(previewPath), sha256: sha256(previewBytes), frame: 30, scale: 0.25},
    outputs_on_e_drive: true,
    sync_contract: {
      status: 'voice_first_manifest_driven',
      authority: 'jianying_sami_timing_manifest',
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
