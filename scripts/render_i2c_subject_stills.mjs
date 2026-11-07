import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {buildVisualProps} from './render_phase1_topic_visual.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const LOCAL_REMOTION = path.join(ROOT, 'remotion');
const DEPENDENCY_REMOTION = fsSync.existsSync(path.join(LOCAL_REMOTION, 'node_modules', '@remotion', 'bundler'))
  ? LOCAL_REMOTION
  : 'E:/project/OpenClaw_VideoFactory/remotion';
const req = createRequire(path.join(DEPENDENCY_REMOTION, 'package.json'));
const {bundle} = req('@remotion/bundler');
const {renderStill, selectComposition} = req('@remotion/renderer');
const ts = req.resolve('typescript');
req(ts);
req.cache[ts].exports = req('typescript-remotion');
const CHROME = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
];

const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i];
    if (!['--script', '--scene-plan', '--timing-manifest', '--output-dir', '--report'].includes(key) || out[key]) throw Error('arguments_invalid');
    const value = argv[i + 1];
    if (!value || value.startsWith('--')) throw Error('arguments_invalid');
    out[key] = value;
  }
  if (Object.keys(out).length !== 5) throw Error('arguments_required');
  return out;
}

async function chrome() {
  for (const value of CHROME) {
    try { if ((await fs.stat(value)).isFile()) return value; } catch {}
  }
  throw Error('approved_chrome_missing');
}

async function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const scriptPath = path.resolve(args['--script']);
  const planPath = path.resolve(args['--scene-plan']);
  const timingPath = path.resolve(args['--timing-manifest']);
  const outputDir = path.resolve(args['--output-dir']);
  const reportPath = path.resolve(args['--report']);
  if (!/^E:[\\/]/i.test(outputDir) || !/^E:[\\/]/i.test(reportPath)) throw Error('output_must_use_e_drive');
  const [scriptBytes, planBytes, timingBytes] = await Promise.all([
    fs.readFile(scriptPath), fs.readFile(planPath), fs.readFile(timingPath),
  ]);
  const script = JSON.parse(scriptBytes), plan = JSON.parse(planBytes), timing = JSON.parse(timingBytes);
  const inputProps = buildVisualProps(script, plan, timing, '9:16');
  const browserExecutable = await chrome();
  await fs.mkdir(outputDir, {recursive: true});
  const serveUrl = await bundle({entryPoint: path.join(ROOT, 'remotion', 'src', 'index.ts')});
  const composition = await selectComposition({serveUrl, id: 'TechnicalExplainer', inputProps, browserExecutable});
  if (composition.width !== 1080 || composition.height !== 1920 || composition.fps !== 30) throw Error('portrait_composition_contract_mismatch');
  const stills = [];
  for (const scene of inputProps.scenes) {
    const frame = Math.min(composition.durationInFrames - 1, Math.max(0, Math.floor(((scene.start_seconds + scene.end_seconds) / 2) * 30)));
    const filename = `scene_${String(scene.scene_index).padStart(2, '0')}_frame_${frame}.png`;
    const target = path.join(outputDir, filename);
    await renderStill({composition, serveUrl, inputProps, frame, output: target, browserExecutable, imageFormat: 'png', logLevel: 'error'});
    const bytes = await fs.readFile(target);
    stills.push({scene_index: scene.scene_index, frame, filename, sha256: sha(bytes), fact_refs: scene.visual_spec?.fact_refs ?? [], visual_spec_kind: scene.visual_spec?.kind ?? null});
  }
  const report = {
    schema_version: 'phase1_i2c_subject_stills_v1',
    status: 'PASS_BOUNDED_STILL_ONLY',
    renderer: 'remotion',
    composition: 'TechnicalExplainer',
    aspect_ratio: '9:16',
    width: 1080,
    height: 1920,
    fps: 30,
    full_render: false,
    render_media_called: false,
    input: {script_sha256: sha(scriptBytes), scene_plan_sha256: sha(planBytes), timing_manifest_sha256: sha(timingBytes)},
    stills,
  };
  await fs.writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`, {flag: 'w', encoding: 'utf8'});
  console.log(JSON.stringify({status: report.status, stills: stills.length, report: reportPath}));
  return 0;
}

main().catch((error) => { console.error(error instanceof Error ? error.message : 'render_stills_failed'); process.exitCode = 1; });
