export type ProductFocus = {x: number; y: number; width: number; height: number; zoom: number};
export type ProductScene = {
  id: string; kind: 'title'|'capture'|'cta'; startFrame: number; endFrame: number;
  headline: string; detail: string; badge: string; asset: string|null;
  assetSha256: string|null; capturedAt: string; attribution: string;
  visualRole?: 'hook'|'message'|'cta'; focus?: ProductFocus | null;
  captureViewport?: {width: number; height: number} | null;
  captureDeviceScaleFactor?: number | null;
};
export type ProductInput = {
  schema_version: '1.0'; mode: 'layout_preview'|'production_candidate'; fps: 30;
  aspect: '9:16'|'16:9'; brand: '逐星'; website: 'photo.joviluma.com'; totalFrames: number;
  scriptSha256: string; timingSha256: string; captureManifestSha256: string;
  captureReviewSha256: string; scenes: ProductScene[];
};
export function validateProductInput(value: unknown, options?: {requireProduction?: boolean}): ProductInput;
export function findSceneIndex(value: ProductInput, frame: number): number;
export function isSafeAsset(value: unknown): boolean;
export function isHash(value: unknown): boolean;
export function isFocusRect(value: unknown): value is ProductFocus;
export function sceneFrameRanges(segments: unknown[], durationSeconds: number, fps?: number): {
  totalFrames: number; ranges: {startFrame: number; endFrame: number}[];
};
export function sceneLayout(aspect: '9:16' | '16:9', sceneId: string, captureViewport?: {width: number; height: number} | null): {
  captureTop: number; captureHeight: number; captureLabelTop: number; detailTop: number; headlineFontSize: number;
};
