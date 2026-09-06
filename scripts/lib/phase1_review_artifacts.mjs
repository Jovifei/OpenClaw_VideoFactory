/** Review derivatives of ONE visual master. No Remotion, provider, or job state. */
import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

const execute = promisify(execFile);
const US = 1_000_000;
const fail = (reason) => {throw new Error(reason);};
const integer = (value) => Number.isSafeInteger(value) && value >= 0;
const ceilFrame = (us, fps) => Number((BigInt(us) * BigInt(fps) + 999999n) / 1000000n);

export async function fileSha256(filename) {
  const digest = crypto.createHash('sha256');
  for await (const chunk of createReadStream(filename)) digest.update(chunk);
  return digest.digest('hex');
}

/** Half-open frame ranges match TechnicalExplainer's start <= frame/fps < end.
 * Last end is clamped to Root.tsx's rounded composition duration, not rounded
 * independently for each scene. Otherwise a 0.501s boundary includes frame 15
 * from the previous scene. Microseconds are the existing timing authority.
 */
export function planReviewFrames(segments, durationInFrames, fps = 30) {
  if (fps !== 30 || !integer(durationInFrames) || durationInFrames < 1 ||
      !Array.isArray(segments) || segments.length < 1 || segments.length > 100) {
    fail('review_frame_plan_invalid');
  }
  let previousUs = 0;
  const ranges = segments.map((segment, index) => {
    const startUs = segment?.scene_start_microseconds;
    const endUs = segment?.scene_end_microseconds;
    if (segment?.index !== index + 1 || !integer(startUs) || !integer(endUs) ||
        startUs !== previousUs || endUs <= startUs) fail('review_timing_invalid');
    previousUs = endUs;
    const start = ceilFrame(startUs, fps);
    const end = Math.min(ceilFrame(endUs, fps), durationInFrames);
    if (end <= start) fail('review_scene_has_no_frames');
    return {scene_index: index + 1, start_frame: start, end_frame_exclusive: end,
      midpoint_frame: Math.floor((start + end - 1) / 2), frame_count: end - start,
      start_seconds: startUs / US, end_seconds: endUs / US,
      duration_microseconds: endUs - startUs,
      rendered_duration_microseconds: Math.round((end - start) * US / fps)};
  });
  if (Math.round(previousUs * fps / US) !== durationInFrames ||
      ranges.at(-1).end_frame_exclusive !== durationInFrames ||
      ranges.some((range, i) => i > 0 && range.start_frame !== ranges[i - 1].end_frame_exclusive)) {
    fail('review_composition_duration_mismatch');
  }
  return ranges;
}

function inside(root, filename) {
  const relative = path.relative(root, filename);
  return relative !== '' && relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

async function noSymlink(filename) {
  let current = path.resolve(filename);
  for (;;) {
    try {if ((await fs.lstat(current)).isSymbolicLink()) fail('review_symlink_forbidden');}
    catch (error) {if (error.code !== 'ENOENT') throw error;}
    const parent = path.dirname(current);
    if (parent === current) return;
    current = parent;
  }
}

export async function assertAbsent(filename) {
  try {await fs.lstat(filename);}
  catch (error) {if (error.code === 'ENOENT') return; throw error;}
  fail('review_output_already_exists');
}

/** Only fresh, mutually separate artifact targets beneath the report root. */
export async function prepareReviewTargets({output, report, stills, clips, inputs = []}) {
  const root = path.dirname(path.resolve(report));
  const targets = [output, report, stills, clips].map((value) => path.resolve(value));
  if (new Set(targets).size !== targets.length ||
      [output, stills, clips].some((value) => !inside(root, path.resolve(value))) ||
      inside(path.resolve(stills), path.resolve(clips)) || inside(path.resolve(clips), path.resolve(stills)) ||
      [output, report, ...inputs].some((value) => [stills, clips].some((dir) =>
        path.resolve(value) === path.resolve(dir) || inside(path.resolve(dir), path.resolve(value))))) {
    fail('review_target_paths_invalid');
  }
  if (inputs.some((value) => targets.includes(path.resolve(value)))) fail('review_target_is_input');
  for (const filename of [...targets, ...inputs]) await noSymlink(filename);
  await assertAbsent(output);
  await assertAbsent(report);
  for (const directory of [stills, clips]) {
    await fs.mkdir(directory, {recursive: true});
    if ((await fs.readdir(directory)).length) fail('review_directory_not_empty');
  }
  await fs.mkdir(root, {recursive: true});
  await fs.mkdir(path.dirname(output), {recursive: true});
}

async function run(program, args) {
  try {
    const result = await execute(program, args, {timeout: 300_000, maxBuffer: 2 * 1024 * 1024, windowsHide: true, shell: false});
    if (result.stderr.trim()) fail('review_media_diagnostic_error');
    return result;
  }
  catch {fail('review_media_command_failed');}
}

export async function probeVisual(filename, {fps = 30, frames, width, height} = {}) {
  const {stdout} = await run('ffprobe', ['-v', 'error', '-count_frames', '-show_streams', '-of', 'json', filename]);
  const {streams} = JSON.parse(stdout);
  if (!Array.isArray(streams) || streams.length !== 1 || streams[0].codec_type !== 'video' ||
      streams[0].codec_name !== 'h264') fail('review_visual_stream_invalid');
  const stream = streams[0];
  const rate = (value) => {const [n, d] = String(value).split('/').map(Number); return n / d;};
  if (rate(stream.avg_frame_rate) !== fps || rate(stream.r_frame_rate) !== fps ||
      !integer(Number(stream.nb_read_frames)) || Number(stream.nb_read_frames) < 1 ||
      (frames !== undefined && Number(stream.nb_read_frames) !== frames) ||
      (width !== undefined && stream.width !== width) || (height !== undefined && stream.height !== height)) {
    fail('review_visual_geometry_or_frames_mismatch');
  }
  return {width: stream.width, height: stream.height, fps, frames: Number(stream.nb_read_frames)};
}

/** Extracts exact frame intervals; review clips are re-encoded, never the master.
 * Returns only after all derivatives decode and the source hash is unchanged.
 * An interrupted attempt retains its files but cannot produce a passed report.
 */
export async function extractReviewArtifacts({output, report, stills, clips, segments,
  durationInFrames, fps = 30, width, height, scenes}) {
  const ranges = planReviewFrames(segments, durationInFrames, fps);
  if (!Array.isArray(scenes) || scenes.length !== ranges.length ||
      scenes.some((scene, i) => scene.scene_index !== i + 1)) fail('review_scene_set_invalid');
  const root = path.dirname(path.resolve(report));
  for (const directory of [stills, clips]) {
    if (!inside(root, path.resolve(directory))) fail('review_target_paths_invalid');
    await noSymlink(directory);
    if ((await fs.readdir(directory)).length) fail('review_directory_not_empty');
  }
  await noSymlink(output);
  const sourceSha = await fileSha256(output);
  const media = await probeVisual(output, {fps, frames: durationInFrames, width, height});
  const entries = [];
  // Constant-rate timestamps retain the last decoded frame even on short clips.
  // Do not use passthrough timestamps here; the real-media regression covers EOF.
  const relative = (filename) => path.relative(root, filename).split(path.sep).join('/');
  for (const range of ranges) {
    const name = `scene_${String(range.scene_index).padStart(2, '0')}`;
    const still = path.join(stills, `${name}_mid.png`);
    const clip = path.join(clips, `${name}.mp4`);
    const common = ['-nostdin', '-v', 'error', '-xerror', '-n', '-i', output, '-map', '0:v:0', '-an', '-sn', '-dn', '-filter_threads', '1'];
    await run('ffmpeg', [...common, '-vf', `select=eq(n\\,${range.midpoint_frame}),setpts=PTS-STARTPTS`,
      '-frames:v', '1', '-fps_mode', 'passthrough', '-update', '1', still]);
    await run('ffmpeg', [...common, '-vf', `trim=start_frame=${range.start_frame}:end_frame=${range.end_frame_exclusive},setpts=N/(${fps}*TB)`,
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), '-fps_mode', 'cfr', clip]);
    await probeVisual(clip, {fps, frames: range.frame_count, width: media.width, height: media.height});
    if ((await fs.stat(still)).size === 0) fail('review_still_empty');
    entries.push({scene_index: range.scene_index, visual_type: scenes[range.scene_index - 1].visual_type,
      start_seconds: range.start_seconds, end_seconds: range.end_seconds,
      source_visual_sha256: sourceSha, extraction_method: 'ffmpeg_from_visual_master_v1',
      frame_range: {start: range.start_frame, end_exclusive: range.end_frame_exclusive},
      still: {filename: relative(still), sha256: await fileSha256(still), frame: range.midpoint_frame},
      clip: {filename: relative(clip), sha256: await fileSha256(clip),
        duration_microseconds: range.duration_microseconds, frame_count: range.frame_count,
        rendered_duration_microseconds: range.rendered_duration_microseconds}});
  }
  if (await fileSha256(output) !== sourceSha) fail('review_source_changed');
  return {entries, source_sha256: sourceSha, media};
}
