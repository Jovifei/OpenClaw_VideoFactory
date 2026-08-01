import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {bundle} from '@remotion/bundler';
import {makeCancelSignal, renderMedia, selectComposition} from '@remotion/renderer';

// Keep TypeScript 7.0.2 for type checks. Remotion 4.0.500's webpack loader
// relies on APIs removed in TS7, so this render child redirects only that
// loader's `typescript` resolution to the separately locked TS5 compatibility alias.
const require = createRequire(import.meta.url);
const primaryTypescript = require.resolve('typescript');
require(primaryTypescript);
require.cache[primaryTypescript].exports = require('typescript-remotion');

const [inputPath, outputPath, chromePath, concurrencyArgument] = process.argv.slice(2);
if (!inputPath || !outputPath || !chromePath) throw new Error('render_arguments_required');
const concurrency = Number.parseInt(concurrencyArgument ?? '1', 10);
if (![1, 2, 4].includes(concurrency)) throw new Error('render_concurrency_invalid');
const inputProps = JSON.parse(await fs.readFile(path.resolve(inputPath), 'utf8'));
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const serveUrl = await bundle({entryPoint: path.join(root, 'src', 'index.ts')});
const composition = await selectComposition({serveUrl, id: 'P1Candidate', inputProps, browserExecutable: chromePath});
const {cancelSignal, cancel} = makeCancelSignal();
process.once('SIGINT', cancel);
process.once('SIGTERM', cancel);
let progress = {rendered_frames: 0, encoded_frames: 0, rendered_done_in_seconds: null, encoded_done_in_seconds: null};
await renderMedia({
  composition,
  serveUrl,
  codec: 'h264',
  outputLocation: path.resolve(outputPath),
  inputProps,
  browserExecutable: chromePath,
  cancelSignal,
  enforceAudioTrack: true,
  concurrency,
  logLevel: 'warn',
  onProgress: (update) => {
    progress = {
      rendered_frames: Number.isFinite(update.renderedFrames) ? update.renderedFrames : progress.rendered_frames,
      encoded_frames: Number.isFinite(update.encodedFrames) ? update.encodedFrames : progress.encoded_frames,
      rendered_done_in_seconds: Number.isFinite(update.renderedDoneIn) ? Number((update.renderedDoneIn / 1000).toFixed(3)) : progress.rendered_done_in_seconds,
      encoded_done_in_seconds: Number.isFinite(update.encodedDoneIn) ? Number((update.encodedDoneIn / 1000).toFixed(3)) : progress.encoded_done_in_seconds,
    };
  },
});
console.log(JSON.stringify({status: 'rendered', composition: composition.id, metrics: {resolved_concurrency: concurrency, ...progress}}));
