import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {
  TEMPLATE_IDS,
  REVIEW_POSITIONS,
  canonicalProjectFile,
  contactCoordinates,
  framesForDuration,
  parseArgs,
  prepareContainedBundleOutput,
  relativeProjectPath,
  resolveApprovedChrome,
  resolveReviewOutput,
  failureRecord,
  safeErrorCode,
  validateInputsManifest,
  validateInputsManifestFiles,
} from './render-review-stills.mjs';

const root = await fs.mkdtemp(path.join(os.tmpdir(), 'p1-review-stills-'));
try {
  await fs.mkdir(path.join(root, 'reports'));
  const templates = {};
  for (const template of TEMPLATE_IDS) {
    const relative = `jobs/p1_candidate/job-${template.replaceAll('-', '')}/render_input.json`;
    const absolute = path.join(root, relative);
    await fs.mkdir(path.dirname(absolute), {recursive: true});
    await fs.writeFile(absolute, '{}');
    templates[template] = relative;
  }
  const mapped = validateInputsManifest({schema_version: '1.0', templates}, root);
  assert.deepEqual(Object.keys(mapped), TEMPLATE_IDS);
  const canonicalMapped = await validateInputsManifestFiles({schema_version: '1.0', templates}, {projectRoot: root});
  assert.deepEqual(Object.keys(canonicalMapped), TEMPLATE_IDS);
  assert.throws(() => validateInputsManifest({schema_version: '1.0', templates: {...templates, extra: templates['protocol-frame']}}, root), /review_inputs_manifest_invalid/);
  assert.throws(() => relativeProjectPath('../outside.json', root), /review_input_path_unsafe/);
  assert.throws(() => relativeProjectPath('https://example.invalid/input.json', root), /review_input_path_unsafe/);
  assert.throws(() => relativeProjectPath('C:relative-drive.json', root), /review_input_path_unsafe/);
  assert.throws(() => validateInputsManifest({schema_version: '1.0', templates: Object.fromEntries(TEMPLATE_IDS.map((template) => [template, templates['protocol-frame']]))}, root), /review_inputs_manifest_duplicate/);
  assert.throws(() => parseArgs(['--input', templates['protocol-frame'], '--output', 'reports/p1_review_test']), /review_legacy_input_disabled/);
  assert.throws(() => parseArgs(['--input=C:/outside.json', '--output', 'reports/p1_review_test', '--inputs-manifest', 'reports/inputs.json']), /review_legacy_input_disabled/);
  assert.throws(() => parseArgs(['--chrome', 'C:/outside/chrome.exe', '--output', 'reports/p1_review_test', '--inputs-manifest', 'reports/inputs.json']), /review_chrome_override_disabled/);
  assert.throws(() => parseArgs(['--chrome=C:/outside/chrome.exe', '--output', 'reports/p1_review_test', '--inputs-manifest', 'reports/inputs.json']), /review_chrome_override_disabled/);
  assert.throws(() => parseArgs(['--output', 'reports/p1_review_test', '--inputs-manifest']), /review_stills_arguments_invalid/);
  assert.throws(() => parseArgs(['--output', 'reports/p1_review_test', '--output', 'reports/p1_review_other', '--inputs-manifest', 'reports/inputs.json']), /review_stills_arguments_invalid/);
  assert.deepEqual(parseArgs(['--output', 'reports/p1_review_test', '--inputs-manifest', 'reports/inputs.json']), {
    output: 'reports/p1_review_test',
    manifest: 'reports/inputs.json',
  });
  const output = await resolveReviewOutput('reports/p1_review_test', {projectRoot: root});
  assert.equal(path.dirname(output.outputRoot), (await fs.realpath(path.join(root, 'reports'))));
  await assert.rejects(() => resolveReviewOutput('reports/unbounded-output', {projectRoot: root}), /review_output_path_unsafe/);
  assert.equal(safeErrorCode(new Error('review_output_path_unsafe')), 'review_output_path_unsafe');
  assert.equal(safeErrorCode(new Error(`failed at ${path.join(root, 'private-input.json')}`)), 'review_stills_failed');
  assert.equal(safeErrorCode({message: 'review_output_path_unsafe'}), 'review_stills_failed');
  assert.deepEqual(failureRecord(new Error(`failed at ${path.join(root, 'private-input.json')}`)), {
    schema_version: '1.0',
    status: 'review_stills_failed',
    error_code: 'review_stills_failed',
  });
  const bundleStage = path.join(root, 'bundle-stage');
  await fs.mkdir(bundleStage);
  const bundleOutput = await prepareContainedBundleOutput(bundleStage);
  assert.equal(path.dirname(bundleOutput), await fs.realpath(bundleStage));
  await assert.rejects(() => prepareContainedBundleOutput(bundleStage), /review_bundle_output_already_exists/);
  assert.throws(() => relativeProjectPath('reports/../p1_review_test', root), /review_input_path_unsafe/);
  const input = path.join(root, templates['protocol-frame']);
  const inputRoot = path.join(root, 'jobs', 'p1_candidate');
  const stats = (kind, symlink = false) => ({
    isFile: () => kind === 'file',
    isDirectory: () => kind === 'directory',
    isSymbolicLink: () => symlink,
  });
  const virtualStage = path.join(root, 'virtual-stage');
  let virtualBundleCreated = false;
  const virtualBundleFs = {
    realpath: async (candidate) => candidate,
    lstat: async (candidate) => {
      if (candidate === virtualStage) return stats('directory');
      if (candidate === path.join(virtualStage, '.bundle') && virtualBundleCreated) return stats('directory', true);
      throw Object.assign(new Error('missing'), {code: 'ENOENT'});
    },
    mkdir: async () => { virtualBundleCreated = true; },
  };
  await assert.rejects(() => prepareContainedBundleOutput(virtualStage, {fsOps: virtualBundleFs}), /review_bundle_output_unsafe/);
  virtualBundleCreated = false;
  const bundleEscapeFs = {
    realpath: async (candidate) => candidate === path.join(virtualStage, '.bundle') ? path.join(root, 'outside-bundle') : candidate,
    lstat: async (candidate) => {
      if (candidate === virtualStage) return stats('directory');
      if (candidate === path.join(virtualStage, '.bundle') && virtualBundleCreated) return stats('directory');
      throw Object.assign(new Error('missing'), {code: 'ENOENT'});
    },
    mkdir: async () => { virtualBundleCreated = true; },
  };
  await assert.rejects(() => prepareContainedBundleOutput(virtualStage, {fsOps: bundleEscapeFs}), /review_bundle_output_unsafe/);
  const approvedChrome = path.join(root, 'approved', 'chrome.exe');
  const chromeFs = {
    realpath: async (candidate) => candidate,
    lstat: async () => stats('file'),
  };
  assert.equal(await resolveApprovedChrome({fsOps: chromeFs, approvedPaths: [approvedChrome]}), approvedChrome);
  const chromeSymlinkFs = {
    realpath: async (candidate) => candidate,
    lstat: async () => stats('file', true),
  };
  await assert.rejects(() => resolveApprovedChrome({fsOps: chromeSymlinkFs, approvedPaths: [approvedChrome]}), /review_chrome_path_unsafe/);
  const chromeEscapeFs = {
    realpath: async () => path.join(root, 'outside', 'chrome.exe'),
    lstat: async () => stats('file'),
  };
  await assert.rejects(() => resolveApprovedChrome({fsOps: chromeEscapeFs, approvedPaths: [approvedChrome]}), /review_chrome_path_unsafe/);
  const chromeMissingFs = {
    realpath: async (candidate) => candidate,
    lstat: async () => { throw Object.assign(new Error('missing'), {code: 'ENOENT'}); },
  };
  await assert.rejects(() => resolveApprovedChrome({fsOps: chromeMissingFs, approvedPaths: [approvedChrome]}), /review_chrome_unavailable/);
  const symlinkFs = {
    realpath: async (candidate) => candidate,
    lstat: async (candidate) => candidate === inputRoot ? stats('directory') : stats('file', candidate === input),
  };
  await assert.rejects(
    () => canonicalProjectFile(templates['protocol-frame'], {projectRoot: root, containmentRelative: 'jobs/p1_candidate', fsOps: symlinkFs}),
    /review_input_path_unsafe/,
  );
  const outside = path.join(root, 'outside', 'render_input.json');
  const escapeFs = {
    realpath: async (candidate) => candidate === input ? outside : candidate,
    lstat: async (candidate) => candidate === inputRoot ? stats('directory') : stats('file'),
  };
  await assert.rejects(
    () => canonicalProjectFile(templates['protocol-frame'], {projectRoot: root, containmentRelative: 'jobs/p1_candidate', fsOps: escapeFs}),
    /review_input_path_unsafe/,
  );
  const reportsRoot = path.join(root, 'reports');
  const missing = Object.assign(new Error('missing'), {code: 'ENOENT'});
  const reportEscapeFs = {
    realpath: async (candidate) => candidate === reportsRoot ? path.join(path.dirname(root), 'outside-reports') : candidate,
    lstat: async (candidate) => candidate === reportsRoot ? stats('directory') : Promise.reject(missing),
  };
  await assert.rejects(
    () => resolveReviewOutput('reports/p1_review_test', {projectRoot: root, fsOps: reportEscapeFs}),
    /review_output_path_unsafe/,
  );
  const existingOutputFs = {
    realpath: async (candidate) => candidate,
    lstat: async (candidate) => candidate === reportsRoot ? stats('directory') : stats('file', true),
  };
  await assert.rejects(
    () => resolveReviewOutput('reports/p1_review_existing', {projectRoot: root, fsOps: existingOutputFs}),
    /review_output_already_exists/,
  );
  assert.deepEqual(framesForDuration(300), [{name: 'start', frame: 0}, {name: 'quarter', frame: 75}, {name: 'half', frame: 150}, {name: 'three_quarters', frame: 224}, {name: 'end', frame: 299}]);
  assert.deepEqual(contactCoordinates(3, 4), {column: 3, row: 4});
  assert.equal(REVIEW_POSITIONS.length * TEMPLATE_IDS.length, 20);
  console.log(JSON.stringify({status: 'review_still_contracts_passed', assertions: 36}));
} finally {
  await fs.rm(root, {recursive: true, force: true});
}
