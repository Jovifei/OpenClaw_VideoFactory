import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '..');

test('registers WebsiteProductDemo without removing existing compositions', () => {
  const source = fs.readFileSync(path.join(ROOT, 'remotion', 'src', 'Root.tsx'), 'utf8');
  assert.match(source, /WebsiteProductDemoRegistration/);
  assert.match(source, /<WebsiteProductDemoRegistration\s*\/>/);
  for (const id of ['TechnicalExplainer', 'P1Candidate', 'FlashWatchdog16x9', 'RcHighPass1080x1920']) {
    assert.match(source, new RegExp(`id=["']${id}["']`), `missing ${id}`);
  }
});

test('renderer exposes an explicit production product route', () => {
  const source = fs.readFileSync(path.join(ROOT, 'scripts', 'render_phase1_topic_visual.mjs'), 'utf8');
  assert.match(source, /--product-input/);
  assert.match(source, /WebsiteProductDemo/);
  assert.match(source, /requireProduction:\s*true/);
});

test('renderer parser accepts product input only with a timing manifest', async () => {
  const {parseArgs} = await import('../scripts/render_phase1_topic_visual.mjs');
  const args = parseArgs([
    '--product-input', 'E:/runtime/product_input.json',
    '--timing-manifest', 'E:/runtime/timing.json',
    '--aspect', '9:16',
    '--output', 'E:/runtime/visual_master.mp4',
    '--report', 'E:/runtime/render_report.json',
    '--stills-dir', 'E:/runtime/stills',
    '--clips-dir', 'E:/runtime/clips',
  ]);
  assert.equal(args['--product-input'], 'E:/runtime/product_input.json');
  assert.throws(() => parseArgs(['--product-input', 'E:/runtime/product_input.json']), /required/);
});

test('product demo source remains separate from the technical scene contract', () => {
  const source = fs.readFileSync(path.join(ROOT, 'remotion', 'src', 'product-demo', 'WebsiteProductDemo.tsx'), 'utf8');
  assert.match(source, /WebsiteProductDemoRegistration/);
  assert.match(source, /layout_preview/);
  assert.match(source, /validateProductInput/);
  assert.doesNotMatch(source, /TechnicalScene/);
});

test('portrait product captures reserve readable space without cropping the source image', () => {
  const source = fs.readFileSync(path.join(ROOT, 'remotion', 'src', 'product-demo', 'WebsiteProductDemo.tsx'), 'utf8');
  assert.match(source, /sceneLayout\(input\.aspect, scene\.id, scene\.captureViewport\)/);
  assert.match(source, /objectFit: 'contain'/);
  const contract = fs.readFileSync(path.join(ROOT, 'remotion', 'src', 'product-demo', 'website-product-contract.mjs'), 'utf8');
  assert.match(contract, /captureHeight: 720/);
  assert.match(contract, /captureHeight: 1000/);
});
