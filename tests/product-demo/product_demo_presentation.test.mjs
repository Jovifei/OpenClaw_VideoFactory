import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const require = createRequire(path.join(root, 'remotion/package.json'));
const ts = require('typescript-remotion');
const React = require('react');
const {renderToStaticMarkup} = require('react-dom/server');
const sourcePath = path.join(root, 'remotion/src/product-demo/WebsiteProductDemo.tsx');
const contract = pathToFileURL(path.join(root, 'remotion/src/product-demo/website-product-contract.mjs')).href;
const sourceRevision = process.env.VIDEO_FACTORY_TEST_SOURCE_REVISION;
if (sourceRevision && !/^[a-f0-9]{40}$/.test(sourceRevision)) throw Error('invalid_test_source_revision');
const sourceText = sourceRevision ? execFileSync('git', ['show', `${sourceRevision}:remotion/src/product-demo/WebsiteProductDemo.tsx`], {cwd: root, encoding: 'utf8'}) : await fs.readFile(sourcePath, 'utf8');
const source = sourceText
  .replace("'./website-product-contract.mjs'", JSON.stringify(contract));
// Export private pure helpers only in this temporary test build; no production API changes.
const compiled = ts.transpileModule(source + '\nexport {cameraFor, HookCover};\n', {
  compilerOptions: {target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext,
    jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true}, fileName: sourcePath,
}).outputText;
const runtimePath = path.join(root, 'remotion/.contract-build', `presentation-test-${process.pid}.mjs`);
await fs.mkdir(path.dirname(runtimePath), {recursive: true});
await fs.writeFile(runtimePath, compiled);
after(() => fs.unlink(runtimePath));
const {cameraFor, HookCover} = await import(pathToFileURL(runtimePath).href);

const cue = duration => ({startFrame: 0, endFrame: duration, label: 'TEST',
  panX: 2, panY: 1, zoom: 1.02, targetX: 0.5, targetY: 0.5});
const scene = duration => ({id: 'hook', kind: 'title', visualRole: 'hook', startFrame: 0,
  endFrame: 180, voiceEndFrame: duration, voiceCues: [cue(duration)], focus: null,
  headline: '工程演示', detail: 'UNIT LAYOUT FIXTURE', badge: 'TEST', asset: null,
  assetSha256: null, attribution: 'UNIT TEST'});

for (const duration of [1, 2, 3, 5, 6, 10, 11, 12, 30]) {
  test(`camera renders every frame of a ${duration}-frame measured speech cue`, () => {
    const input = scene(duration);
    for (let frame = 0; frame < duration; frame++) {
      const camera = cameraFor(input, frame);
      assert.ok(Number.isFinite(camera.markerOpacity));
      assert.ok(camera.markerOpacity >= 0 && camera.markerOpacity <= 1);
      if (duration <= 2) assert.ok(camera.markerOpacity > 0);
      assert.ok(Number.isFinite(camera.labelOpacity));
      assert.doesNotMatch(camera.transform, /NaN|Infinity/);
    }
    assert.equal(cameraFor(input, duration).markerOpacity, 0);
  });
}

function box(html, name) {
  const tag = html.match(new RegExp(`<div data-layout-box="${name}" style="([^"]*)"`));
  assert.ok(tag, `missing actual rendered element: ${name}`);
  return Object.fromEntries(tag[1].split(';').filter(Boolean).map(item => {
    const at = item.indexOf(':');
    return [item.slice(0, at), item.slice(at + 1)];
  }));
}

for (const aspect of ['9:16', '16:9']) {
  test(`${aspect} hook map, attribution and footer stay above the subtitle region`, () => {
    const portrait = aspect === '9:16';
    const width = portrait ? 1080 : 1920, left = portrait ? 76 : 96;
    const subtitleTop = portrait ? 1640 : 918;
    const input = scene(30);
    const html = renderToStaticMarkup(React.createElement(HookCover, {
      aspect, scene: input, local: 10, left, contentWidth: width - 2 * left,
      camera: cameraFor(input, 10), preview: false,
    }));
    const map = box(html, 'product-hook-map');
    assert.ok(parseFloat(map.top) + parseFloat(map.height) <= subtitleTop);
    assert.ok(parseFloat(map.left) + parseFloat(map.width) <= width - left);
    for (const name of ['product-attribution', 'product-hook-footer']) {
      assert.ok(parseFloat(box(html, name).top) + 40 <= subtitleTop, `${name} overlaps subtitle/canvas`);
    }
  });
}
