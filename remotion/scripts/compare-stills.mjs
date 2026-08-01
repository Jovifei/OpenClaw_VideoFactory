import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import pixelmatch from 'pixelmatch';
import {PNG} from 'pngjs';

const args = process.argv.slice(2);
const baselineIndex = args.indexOf('--baseline');
const actualIndex = args.indexOf('--actual');
const outputIndex = args.indexOf('--output');
if (baselineIndex < 0 || actualIndex < 0 || outputIndex < 0) throw new Error('compare_stills_arguments_required');
const baselineRoot = path.resolve(args[baselineIndex + 1]);
const actualRoot = path.resolve(args[actualIndex + 1]);
const outputRoot = path.resolve(args[outputIndex + 1]);
await fs.mkdir(outputRoot, {recursive: true});
let baselineFiles = [];
try { baselineFiles = (await fs.readdir(baselineRoot)).filter((name) => name.endsWith('.png') && name !== 'contact-sheet.png'); } catch { baselineFiles = []; }
const actualFiles = (await fs.readdir(actualRoot)).filter((name) => name.endsWith('.png') && name !== 'contact-sheet.png');
const items = [];
for (const name of actualFiles.sort()) {
  if (!baselineFiles.includes(name)) { items.push({file: name, status: 'baseline_missing'}); continue; }
  const expected = PNG.sync.read(await fs.readFile(path.join(baselineRoot, name)));
  const actual = PNG.sync.read(await fs.readFile(path.join(actualRoot, name)));
  if (expected.width !== actual.width || expected.height !== actual.height) { items.push({file: name, status: 'dimensions_mismatch'}); continue; }
  const diff = new PNG({width: actual.width, height: actual.height});
  const changedPixels = pixelmatch(expected.data, actual.data, diff.data, actual.width, actual.height, {threshold: 0.1});
  const changedRatio = changedPixels / (actual.width * actual.height);
  const diffFile = `${name.replace(/\.png$/, '')}.diff.png`;
  await fs.writeFile(path.join(outputRoot, diffFile), PNG.sync.write(diff));
  items.push({file: name, status: changedRatio <= 0.005 ? 'within_threshold' : 'visual_review_required', changed_pixels: changedPixels, changed_ratio: changedRatio, diff_file: diffFile});
}
const status = baselineFiles.length === 0 ? 'provisional_review_required' : items.every((item) => item.status === 'within_threshold') ? 'pass' : 'visual_review_required';
await fs.writeFile(path.join(outputRoot, 'visual-regression.json'), JSON.stringify({schema_version: '1.0', status, threshold: 0.1, changed_ratio_limit: 0.005, items}, null, 2));
console.log(JSON.stringify({status, items: items.length}));
