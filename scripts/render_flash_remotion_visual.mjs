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
    if (!['--script', '--output', '--report'].includes(key) || values[key]) throw new Error('arguments_invalid');
    const value = argv[++i];
    if (!value || value.startsWith('--')) throw new Error('arguments_invalid');
    values[key] = value;
  }
  if (!values['--script'] || !values['--output'] || !values['--report']) throw new Error('arguments_required');
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

function buildInput(script) {
  if (!script || !Array.isArray(script.beats) || script.beats.length !== 5) throw new Error('script_must_have_five_beats');
  const durationSeconds = 50;
  const sceneDuration = durationSeconds / script.beats.length;
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
    scenes: script.beats.map((beat, index) => ({
      start_seconds: Number((index * sceneDuration).toFixed(3)),
      end_seconds: Number(((index + 1) * sceneDuration).toFixed(3)),
      heading: headings[index],
      visual_kind: ['window', 'sequence', 'budget', 'recovery', 'checklist'][index],
      source_subtitle: String(beat.subtitle || ''),
    })),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const scriptPath = path.resolve(args['--script']);
  const outputPath = path.resolve(args['--output']);
  const reportPath = path.resolve(args['--report']);
  if (outputPath.toUpperCase().startsWith('C:') || reportPath.toUpperCase().startsWith('C:')) throw new Error('c_drive_output_forbidden');
  const script = JSON.parse(await fs.readFile(scriptPath, 'utf8'));
  const inputProps = buildInput(script);
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
  const [outputBytes, previewBytes, scriptBytes] = await Promise.all([
    fs.readFile(outputPath),
    fs.readFile(previewPath),
    fs.readFile(scriptPath),
  ]);
  const report = {
    schema_version: '1.0',
    status: 'remotion_visual_ready_for_jianying',
    renderer: 'remotion',
    composition: composition.id,
    input: {script_filename: path.basename(scriptPath), script_sha256: sha256(scriptBytes)},
    visual: {
      filename: path.basename(outputPath),
      sha256: sha256(outputBytes),
      width: 1920,
      height: 1080,
      fps: 30,
      duration_seconds: inputProps.duration_seconds,
      audio_present: false,
      burned_in_subtitles: false,
    },
    preview: {filename: path.basename(previewPath), sha256: sha256(previewBytes), frame: 30, scale: 0.25},
    outputs_on_e_drive: true,
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
