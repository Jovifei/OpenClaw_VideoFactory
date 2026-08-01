export const TEMPLATE_IDS = [
  'protocol-frame',
  'code-explainer',
  'flow-diagram',
  'engineering-case',
] as const;

export type TemplateId = (typeof TEMPLATE_IDS)[number];

export type Caption = {
  start: number;
  end: number;
  text: string;
};

type Mascot = {asset: string; pose: string};
type Audio = {asset: string; duration_seconds: number};
type LegacyScene = {heading: string; body: string; accent?: string};
type TimedScene = LegacyScene & {start_seconds: number; end_seconds: number};

export type CandidateRenderInputV1 = {
  schema_version: '1.0';
  job_id: string;
  template: TemplateId;
  title: string;
  scenes: LegacyScene[];
  captions: Caption[];
  mascot: Mascot;
  audio: Audio;
};

export type CandidateRenderInputV2 = {
  schema_version: '2.0';
  job_id: string;
  template: TemplateId;
  title: string;
  requested_duration_seconds: number;
  resolved_duration_seconds: number;
  fps: 30;
  scenes: TimedScene[];
  captions: Caption[];
  mascot: Mascot;
  audio: Audio;
};

export type CandidateRenderInput = CandidateRenderInputV1 | CandidateRenderInputV2;

const isSafeRelativeAsset = (asset: unknown, prefix: string, extension: string): asset is string =>
  typeof asset === 'string' &&
  asset.startsWith(prefix) &&
  asset.endsWith(extension) &&
  !asset.includes('..') &&
  !asset.includes('\\') &&
  !asset.includes('://') &&
  !asset.startsWith('/');

const isDuration = (value: unknown, minimum: number, maximum: number): value is number =>
  typeof value === 'number' && Number.isFinite(value) && value >= minimum && value <= maximum;

const validateBase = (input: Record<string, unknown>) => {
  if (typeof input.job_id !== 'string' || !/^job-[a-f0-9]{24}$/.test(input.job_id)) throw new Error('job_id_invalid');
  if (!TEMPLATE_IDS.includes(input.template as TemplateId)) throw new Error('template_invalid');
  if (typeof input.title !== 'string' || input.title.length < 4 || input.title.length > 80) throw new Error('title_invalid');
  const mascot = input.mascot as Partial<Mascot> | undefined;
  const audio = input.audio as Partial<Audio> | undefined;
  if (!mascot || !isSafeRelativeAsset(mascot.asset, 'mascot/', '.svg') || typeof mascot.pose !== 'string') {
    throw new Error('mascot_asset_invalid');
  }
  if (!audio || !isSafeRelativeAsset(audio.asset, 'runtime/', '.wav') || !isDuration(audio.duration_seconds, 0.001, 60)) {
    throw new Error('audio_asset_invalid');
  }
};

const validateCaption = (captions: unknown, maximumEnd: number) => {
  if (!Array.isArray(captions) || captions.length < 1) throw new Error('captions_invalid');
  let previousEnd = 0;
  for (const caption of captions) {
    if (!caption || typeof caption.start !== 'number' || typeof caption.end !== 'number' || typeof caption.text !== 'string' ||
      caption.start < previousEnd || caption.end <= caption.start || caption.end > maximumEnd || caption.text.split('\n').length > 2 || caption.text.replace(/\n/g, '').length > 36) {
      throw new Error('caption_invalid');
    }
    previousEnd = caption.end;
  }
};

const validateLegacyScenes = (scenes: unknown) => {
  if (!Array.isArray(scenes) || scenes.length < 1 || scenes.length > 5) throw new Error('scenes_invalid');
  for (const scene of scenes) {
    if (!scene || typeof scene.heading !== 'string' || typeof scene.body !== 'string' || scene.heading.length > 30 || scene.body.length > 72) {
      throw new Error('scene_invalid');
    }
  }
};

export const validateInput = (value: unknown): CandidateRenderInput => {
  if (!value || typeof value !== 'object') throw new Error('input_not_object');
  const input = value as Record<string, unknown>;
  if (input.schema_version !== '1.0' && input.schema_version !== '2.0') throw new Error('schema_version_invalid');
  validateBase(input);
  if (input.schema_version === '1.0') {
    const legacy = input as unknown as CandidateRenderInputV1;
    validateLegacyScenes(legacy.scenes);
    validateCaption(legacy.captions, 10);
    if (!isDuration(legacy.audio.duration_seconds, 0.001, 10.1)) throw new Error('audio_asset_invalid');
    return legacy;
  }
  const current = input as unknown as CandidateRenderInputV2;
  if (!Number.isInteger(current.requested_duration_seconds) || !isDuration(current.requested_duration_seconds, 25, 60)) {
    throw new Error('requested_duration_invalid');
  }
  if (!isDuration(current.resolved_duration_seconds, 25, 60) || current.fps !== 30) {
    throw new Error('resolved_duration_invalid');
  }
  if (current.audio.duration_seconds > current.resolved_duration_seconds) throw new Error('audio_asset_invalid');
  if (!Array.isArray(current.scenes) || current.scenes.length < 1 || current.scenes.length > 5) throw new Error('scenes_invalid');
  let previousEnd = 0;
  for (const scene of current.scenes) {
    if (!scene || typeof scene.heading !== 'string' || typeof scene.body !== 'string' || scene.heading.length > 30 || scene.body.length > 72 ||
      !isDuration(scene.start_seconds, 0, current.resolved_duration_seconds) || !isDuration(scene.end_seconds, 0, current.resolved_duration_seconds) ||
      scene.start_seconds !== previousEnd || scene.end_seconds <= scene.start_seconds) {
      throw new Error('scene_timing_invalid');
    }
    previousEnd = scene.end_seconds;
  }
  if (Math.abs(previousEnd - current.resolved_duration_seconds) > 0.001) throw new Error('scene_timing_invalid');
  validateCaption(current.captions, current.resolved_duration_seconds);
  return current;
};

export const durationSeconds = (input: CandidateRenderInput): number =>
  input.schema_version === '2.0' ? input.resolved_duration_seconds : input.audio.duration_seconds;

export const fpsOf = (input: CandidateRenderInput): number =>
  input.schema_version === '2.0' ? input.fps : 30;

export const sceneIndexAt = (input: CandidateRenderInput, seconds: number): number => {
  if (input.schema_version === '2.0') {
    const index = input.scenes.findIndex((scene) => seconds >= scene.start_seconds && seconds < scene.end_seconds);
    return index >= 0 ? index : input.scenes.length - 1;
  }
  return Math.min(input.scenes.length - 1, Math.floor(seconds / (durationSeconds(input) / input.scenes.length)));
};

export const sceneAt = (input: CandidateRenderInput, seconds: number): LegacyScene | TimedScene =>
  input.scenes[sceneIndexAt(input, seconds)];
