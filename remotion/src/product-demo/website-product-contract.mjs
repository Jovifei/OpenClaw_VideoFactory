/** Pure contract for an additive WebsiteProductDemo composition; no I/O or network. */
const fail = (code) => { throw new Error(`product_demo:${code}`); };
export const isSafeAsset = (value) => typeof value === 'string' &&
  /^runtime\/[A-Za-z0-9_-]+\/[A-Za-z0-9_.-]+\.png$/.test(value) && !value.includes('..');
export const isHash = (value) => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
export function sceneFrameRanges(segments, durationSeconds, fps = 30) {
  if (fps !== 30 || !Number.isFinite(durationSeconds) || durationSeconds < 25 || durationSeconds > 60 ||
      !Array.isArray(segments) || segments.length < 5 || segments.length > 9) fail('timing_shape');
  const totalUs = Math.round(durationSeconds * 1e6);
  if (Math.abs(totalUs / 1e6 - durationSeconds) > 1e-9) fail('submicrosecond_duration');
  const totalFrames = Math.floor((totalUs * fps + 500000) / 1000000);
  const ceilFrame = (us) => Number((BigInt(us) * 30n + 999999n) / 1000000n);
  let cursor = 0;
  const ranges = segments.map((s, i) => {
    const a = s?.scene_start_microseconds, b = s?.scene_end_microseconds;
    if (s?.index !== i + 1 || !Number.isSafeInteger(a) || !Number.isSafeInteger(b) ||
        a !== cursor || b <= a || b > totalUs) fail('timing_range');
    cursor = b;
    const startFrame = ceilFrame(a), endFrame = Math.min(ceilFrame(b), totalFrames);
    if (startFrame >= endFrame) fail('empty_scene');
    return {startFrame, endFrame};
  });
  if (cursor !== totalUs || ranges.at(-1).endFrame !== totalFrames ||
      ranges.some((s, i) => i && s.startFrame !== ranges[i - 1].endFrame)) fail('timing_coverage');
  return {totalFrames, ranges};
}
export function validateProductInput(value, {requireProduction = false} = {}) {
  if (!value || typeof value !== 'object' || value.schema_version !== '1.0' ||
      !['layout_preview', 'production_candidate'].includes(value.mode) || value.fps !== 30 ||
      !['9:16', '16:9'].includes(value.aspect) || value.brand !== '逐星' ||
      value.website !== 'photo.joviluma.com' || !Number.isInteger(value.totalFrames) ||
      value.totalFrames < 750 || value.totalFrames > 1800 || !Array.isArray(value.scenes) ||
      value.scenes.length < 5 || value.scenes.length > 9) fail('input_shape');
  if (requireProduction && value.mode !== 'production_candidate') fail('preview_not_production');
  if (value.mode === 'production_candidate' && (!isHash(value.scriptSha256) ||
      !isHash(value.timingSha256) || !isHash(value.captureManifestSha256) ||
      !isHash(value.captureReviewSha256))) fail('missing_provenance');
  const ids = new Set(); let end = 0;
  for (const [i, s] of value.scenes.entries()) {
    if (!s || typeof s !== 'object' || !/^[a-z][a-z0-9_-]{1,30}$/.test(s.id) || ids.has(s.id) ||
        !['title', 'capture', 'cta'].includes(s.kind) || !Number.isInteger(s.startFrame) ||
        !Number.isInteger(s.endFrame) || s.startFrame !== end || s.endFrame <= end ||
        s.endFrame > value.totalFrames) fail('scene_shape');
    if (typeof s.headline !== 'string' || !s.headline.trim() || [...s.headline].length > 24 ||
        typeof s.detail !== 'string' || [...s.detail].length > 44 ||
        typeof s.badge !== 'string' || [...s.badge].length > 24) fail('text_budget');
    if (s.kind === 'capture') {
      if(s.asset !== null && !isSafeAsset(s.asset)) fail('capture_path');
      if (value.mode === 'production_candidate' && (!isSafeAsset(s.asset) || !isHash(s.assetSha256) ||
          !/^\d{4}-\d{2}-\d{2}T/.test(s.capturedAt) || !Number.isFinite(Date.parse(s.capturedAt)) ||
          typeof s.attribution !== 'string' || !s.attribution.trim() || [...s.attribution].length > 80)) fail('capture_binding');
    } else if (s.asset !== null || s.assetSha256 !== null) fail('text_scene_has_asset');
    if (s.kind === 'cta' && (i !== value.scenes.length - 1 || s.endFrame - s.startFrame < 120)) fail('cta_hold');
    ids.add(s.id); end = s.endFrame;
  }
  if (value.scenes[0].kind !== 'title' || value.scenes.at(-1).kind !== 'cta' || end !== value.totalFrames) fail('scene_coverage');
  return value;
}
export function findSceneIndex(value, frame) {
  if (!Number.isInteger(frame) || frame < 0 || frame >= value.totalFrames) fail('frame_out_of_bounds');
  const result = value.scenes.findIndex(s => s.startFrame <= frame && frame < s.endFrame);
  if (result < 0) fail('scene_missing');
  return result;
}
