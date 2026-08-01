import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import {PNG} from 'pngjs';

const require = createRequire(import.meta.url);
const primaryTypescript = require.resolve('typescript');
require(primaryTypescript);
require.cache[primaryTypescript].exports = require('typescript-remotion');

export const TEMPLATE_IDS = ['protocol-frame', 'engineering-case', 'flow-diagram', 'code-explainer'];
export const REVIEW_POSITIONS = [
  {name: 'start', ratio: 0},
  {name: 'quarter', ratio: 0.25},
  {name: 'half', ratio: 0.5},
  {name: 'three_quarters', ratio: 0.75},
  {name: 'end', ratio: 1},
];

const SCRIPT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PROJECT_ROOT = path.resolve(SCRIPT_ROOT, '..');
const REVIEW_OUTPUT_RE = /^reports\/p1_review_[a-z0-9][a-z0-9_-]*$/;
export const APPROVED_CHROME_PATHS = Object.freeze([
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
]);
const SAFE_FAILURE_CODES = new Set([
  'review_bundle_output_already_exists',
  'review_bundle_output_unsafe',
  'review_bundle_staging_unsafe',
  'review_chrome_override_disabled',
  'review_chrome_path_unsafe',
  'review_chrome_unavailable',
  'review_contact_coordinates_invalid',
  'review_duration_invalid',
  'review_input_path_unsafe',
  'review_input_template_mismatch',
  'review_inputs_manifest_duplicate',
  'review_inputs_manifest_invalid',
  'review_legacy_input_disabled',
  'review_output_already_exists',
  'review_output_path_unsafe',
  'review_stills_arguments_invalid',
  'review_stills_arguments_required',
  'review_stills_failed',
]);

function fail(code) {
  throw new Error(code);
}

export function safeErrorCode(error) {
  const candidate = error instanceof Error ? error.message : '';
  return SAFE_FAILURE_CODES.has(candidate) ? candidate : 'review_stills_failed';
}

export function failureRecord(error) {
  return {
    schema_version: '1.0',
    status: 'review_stills_failed',
    error_code: safeErrorCode(error),
  };
}

function sha256(buffer) {
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

export function relativeProjectPath(value, projectRoot = PROJECT_ROOT) {
  if (typeof value !== 'string' || !value || value.includes('\0') || /^[a-z][a-z0-9+.-]*:\/\//i.test(value) || /^[a-z]:/i.test(value) || /^\\\\/.test(value) || path.isAbsolute(value)) {
    fail('review_input_path_unsafe');
  }
  const candidate = value.replaceAll('\\', '/');
  if (candidate === '.' || candidate.split('/').includes('..')) fail('review_input_path_unsafe');
  const root = path.resolve(projectRoot);
  const resolved = path.resolve(root, candidate);
  const relative = path.relative(root, resolved);
  if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) fail('review_input_path_unsafe');
  return {relative: relative.replaceAll('\\', '/'), resolved};
}

function isWithin(root, candidate) {
  const relative = path.relative(root, candidate);
  return Boolean(relative) && !relative.startsWith('..') && !path.isAbsolute(relative);
}

function canonicalPathKey(value) {
  const normalized = path.normalize(value).replaceAll('\\', '/');
  return process.platform === 'win32' ? normalized.toLowerCase() : normalized;
}

async function lstatOrNull(fsOps, candidate) {
  try {
    return await fsOps.lstat(candidate);
  } catch (error) {
    if (error && error.code === 'ENOENT') return null;
    throw error;
  }
}

export async function canonicalProjectFile(value, {projectRoot = PROJECT_ROOT, containmentRelative, fsOps = fs} = {}) {
  if (typeof containmentRelative !== 'string') fail('review_input_path_unsafe');
  const location = relativeProjectPath(value, projectRoot);
  const lexicalRoot = path.resolve(projectRoot);
  const lexicalContainment = path.resolve(lexicalRoot, containmentRelative);
  const [canonicalRoot, canonicalContainment, containmentStat, fileStat] = await Promise.all([
    fsOps.realpath(lexicalRoot),
    fsOps.realpath(lexicalContainment),
    fsOps.lstat(lexicalContainment),
    fsOps.lstat(location.resolved),
  ]);
  if (!containmentStat.isDirectory() || containmentStat.isSymbolicLink() || !fileStat.isFile() || fileStat.isSymbolicLink()) {
    fail('review_input_path_unsafe');
  }
  const canonicalFile = await fsOps.realpath(location.resolved);
  if (!isWithin(canonicalRoot, canonicalContainment) || !isWithin(canonicalRoot, canonicalFile) || !isWithin(canonicalContainment, canonicalFile)) {
    fail('review_input_path_unsafe');
  }
  return {relative: path.relative(canonicalRoot, canonicalFile).replaceAll('\\', '/'), resolved: canonicalFile};
}

export function validateInputsManifest(manifest, projectRoot = PROJECT_ROOT) {
  if (!manifest || manifest.schema_version !== '1.0' || typeof manifest.templates !== 'object' || Array.isArray(manifest.templates)) {
    fail('review_inputs_manifest_invalid');
  }
  const keys = Object.keys(manifest.templates).sort();
  if (keys.join('|') !== [...TEMPLATE_IDS].sort().join('|')) fail('review_inputs_manifest_invalid');
  const inputs = {};
  const seen = new Set();
  for (const template of TEMPLATE_IDS) {
    const location = relativeProjectPath(manifest.templates[template], projectRoot);
    if (!location.relative.startsWith('jobs/p1_candidate/')) fail('review_input_path_unsafe');
    if (seen.has(location.resolved)) fail('review_inputs_manifest_duplicate');
    seen.add(location.resolved);
    inputs[template] = location;
  }
  return inputs;
}

export async function validateInputsManifestFiles(manifest, {projectRoot = PROJECT_ROOT, fsOps = fs} = {}) {
  const lexicalInputs = validateInputsManifest(manifest, projectRoot);
  const inputs = {};
  const seen = new Set();
  for (const template of TEMPLATE_IDS) {
    const entry = await canonicalProjectFile(lexicalInputs[template].relative, {
      projectRoot,
      containmentRelative: 'jobs/p1_candidate',
      fsOps,
    });
    if (seen.has(entry.resolved)) fail('review_inputs_manifest_duplicate');
    seen.add(entry.resolved);
    inputs[template] = entry;
  }
  return inputs;
}

export function framesForDuration(durationInFrames) {
  if (!Number.isInteger(durationInFrames) || durationInFrames < 2) fail('review_duration_invalid');
  return REVIEW_POSITIONS.map(({name, ratio}) => ({
    name,
    frame: ratio === 1 ? durationInFrames - 1 : Math.round((durationInFrames - 1) * ratio),
  }));
}

export function contactCoordinates(templateIndex, positionIndex) {
  if (!Number.isInteger(templateIndex) || !Number.isInteger(positionIndex) || templateIndex < 0 || templateIndex >= TEMPLATE_IDS.length || positionIndex < 0 || positionIndex >= REVIEW_POSITIONS.length) {
    fail('review_contact_coordinates_invalid');
  }
  return {column: templateIndex, row: positionIndex};
}

export function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const name = argv[index];
    if (name === '--input' || name.startsWith('--input=')) fail('review_legacy_input_disabled');
    if (name === '--chrome' || name.startsWith('--chrome=')) fail('review_chrome_override_disabled');
    if (!['--output', '--inputs-manifest'].includes(name) || values[name] !== undefined) fail('review_stills_arguments_invalid');
    const value = argv[index + 1];
    if (!value || value.startsWith('--')) fail('review_stills_arguments_invalid');
    values[name] = value;
    index += 1;
  }
  if (!values['--output'] || !values['--inputs-manifest']) fail('review_stills_arguments_required');
  return {
    output: values['--output'],
    manifest: values['--inputs-manifest'],
  };
}

export async function resolveApprovedChrome({fsOps = fs, approvedPaths = APPROVED_CHROME_PATHS} = {}) {
  for (const approvedPath of approvedPaths) {
    if (typeof approvedPath !== 'string' || !path.isAbsolute(approvedPath)) fail('review_chrome_path_unsafe');
    const lexicalPath = path.resolve(approvedPath);
    const stat = await lstatOrNull(fsOps, lexicalPath);
    if (stat === null) continue;
    if (!stat.isFile() || stat.isSymbolicLink()) fail('review_chrome_path_unsafe');
    const canonicalPath = await fsOps.realpath(lexicalPath);
    if (canonicalPathKey(canonicalPath) !== canonicalPathKey(lexicalPath)) fail('review_chrome_path_unsafe');
    return canonicalPath;
  }
  fail('review_chrome_unavailable');
}

async function inputMapFromArgs(args) {
  if (!args || !args.manifest || args.legacyInput !== undefined) fail('review_stills_arguments_required');
  const manifestPath = await canonicalProjectFile(args.manifest, {containmentRelative: 'reports'});
  const manifest = JSON.parse(await fs.readFile(manifestPath.resolved, 'utf8'));
  return validateInputsManifestFiles(manifest);
}

export async function resolveReviewOutput(value, {projectRoot = PROJECT_ROOT, fsOps = fs} = {}) {
  const location = relativeProjectPath(value, projectRoot);
  if (!REVIEW_OUTPUT_RE.test(location.relative)) fail('review_output_path_unsafe');
  const lexicalRoot = path.resolve(projectRoot);
  const lexicalReports = path.resolve(lexicalRoot, 'reports');
  const [canonicalRoot, canonicalReports, reportsStat] = await Promise.all([
    fsOps.realpath(lexicalRoot),
    fsOps.realpath(lexicalReports),
    fsOps.lstat(lexicalReports),
  ]);
  if (!reportsStat.isDirectory() || reportsStat.isSymbolicLink() || !isWithin(canonicalRoot, canonicalReports)) {
    fail('review_output_path_unsafe');
  }
  const outputName = location.relative.slice('reports/'.length);
  const outputRoot = path.resolve(canonicalReports, outputName);
  if (!isWithin(canonicalReports, outputRoot) || path.dirname(outputRoot) !== canonicalReports) fail('review_output_path_unsafe');
  if (await lstatOrNull(fsOps, outputRoot)) fail('review_output_already_exists');
  const stagingRoot = `${outputRoot}.tmp-${process.pid}`;
  if (await lstatOrNull(fsOps, stagingRoot)) fail('review_output_already_exists');
  return {outputRoot, stagingRoot};
}

export async function prepareContainedBundleOutput(stagingRoot, {fsOps = fs} = {}) {
  const lexicalStaging = path.resolve(stagingRoot);
  const stagingStat = await fsOps.lstat(lexicalStaging);
  if (!stagingStat.isDirectory() || stagingStat.isSymbolicLink()) fail('review_bundle_staging_unsafe');
  const canonicalStaging = await fsOps.realpath(lexicalStaging);
  if (canonicalPathKey(canonicalStaging) !== canonicalPathKey(lexicalStaging)) fail('review_bundle_staging_unsafe');
  const lexicalBundle = path.resolve(canonicalStaging, '.bundle');
  if (!isWithin(canonicalStaging, lexicalBundle) || path.dirname(lexicalBundle) !== canonicalStaging) {
    fail('review_bundle_output_unsafe');
  }
  if (await lstatOrNull(fsOps, lexicalBundle)) fail('review_bundle_output_already_exists');
  await fsOps.mkdir(lexicalBundle, {recursive: false});
  const bundleStat = await fsOps.lstat(lexicalBundle);
  if (!bundleStat.isDirectory() || bundleStat.isSymbolicLink()) fail('review_bundle_output_unsafe');
  const canonicalBundle = await fsOps.realpath(lexicalBundle);
  if (
    canonicalPathKey(canonicalBundle) !== canonicalPathKey(lexicalBundle)
    || !isWithin(canonicalStaging, canonicalBundle)
  ) {
    fail('review_bundle_output_unsafe');
  }
  return canonicalBundle;
}

async function propsForTemplate(template, entry) {
  const inputProps = entry.sourceProps || JSON.parse(await fs.readFile(entry.resolved, 'utf8'));
  if (!inputProps || inputProps.template !== template) fail('review_input_template_mismatch');
  return inputProps;
}

async function createContactSheet(stagingRoot, stills) {
  const width = 216;
  const height = 384;
  const contact = new PNG({width: width * TEMPLATE_IDS.length, height: height * REVIEW_POSITIONS.length, colorType: 6});
  for (const still of stills) {
    const image = PNG.sync.read(await fs.readFile(path.join(stagingRoot, still.file)));
    const {column, row} = contactCoordinates(TEMPLATE_IDS.indexOf(still.template), REVIEW_POSITIONS.findIndex((position) => position.name === still.position));
    for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
      const sourceX = Math.floor(x * image.width / width);
      const sourceY = Math.floor(y * image.height / height);
      const source = (sourceY * image.width + sourceX) * 4;
      const target = ((row * height + y) * contact.width + column * width + x) * 4;
      image.data.copy(contact.data, target, source, source + 4);
    }
  }
  const output = path.join(stagingRoot, 'contact-sheet.png');
  const buffer = PNG.sync.write(contact);
  await fs.writeFile(output, buffer);
  return {file: 'contact-sheet.png', sha256: sha256(buffer)};
}

export async function renderReviewStills(args) {
  const {outputRoot, stagingRoot} = await resolveReviewOutput(args.output);
  const inputs = await inputMapFromArgs(args);
  const browserExecutable = await resolveApprovedChrome();
  await fs.mkdir(stagingRoot, {recursive: false});
  try {
    const bundleOutput = await prepareContainedBundleOutput(stagingRoot);
    const serveUrl = await bundle({entryPoint: path.join(SCRIPT_ROOT, 'src', 'index.ts'), outDir: bundleOutput});
    const stills = [];
    for (const template of TEMPLATE_IDS) {
      const inputProps = await propsForTemplate(template, inputs[template]);
      const composition = await selectComposition({serveUrl, id: 'P1Candidate', inputProps, browserExecutable});
      for (const position of framesForDuration(composition.durationInFrames)) {
        const file = `${template}-${position.name}.png`;
        const output = path.join(stagingRoot, file);
        await renderStill({composition, serveUrl, output, inputProps, frame: position.frame, browserExecutable, imageFormat: 'png', logLevel: 'error'});
        stills.push({template, position: position.name, frame: position.frame, file, sha256: sha256(await fs.readFile(output))});
      }
    }
    const contactSheet = await createContactSheet(stagingRoot, stills);
    const reviewManifest = {
      schema_version: '1.0',
      baseline_status: 'provisional_pending_jovi',
      templates: TEMPLATE_IDS,
      positions: REVIEW_POSITIONS.map((position) => position.name),
      inputs: Object.fromEntries(TEMPLATE_IDS.map((template) => [template, inputs[template].relative])),
      stills,
      contact_sheet: contactSheet,
    };
    await fs.writeFile(path.join(stagingRoot, 'review-manifest.json'), JSON.stringify(reviewManifest, null, 2));
    await fs.rename(stagingRoot, outputRoot);
    return {status: 'review_stills_rendered', stills: stills.length, baseline_status: reviewManifest.baseline_status};
  } catch (error) {
    const failure = failureRecord(error);
    await fs.writeFile(path.join(stagingRoot, 'failure.json'), JSON.stringify(failure, null, 2)).catch(() => {});
    throw new Error(failure.error_code);
  }
}

const directInvocation = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (directInvocation) {
  try {
    console.log(JSON.stringify(await renderReviewStills(parseArgs(process.argv.slice(2)))));
  } catch (error) {
    console.error(safeErrorCode(error));
    process.exitCode = 2;
  }
}
