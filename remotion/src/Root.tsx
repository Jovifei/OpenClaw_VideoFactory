import React from 'react';
import {Composition, type CalculateMetadataFunction} from 'remotion';
import {durationSeconds, fpsOf, validateInput, type CandidateRenderInput} from './contracts';
import {CandidateVideo} from './Video';
import {ReferenceFlashVisual, type FlashVisualInput} from './ReferenceFlashVisual';

export const calculateCandidateMetadata: CalculateMetadataFunction<CandidateRenderInput> = ({props}) => {
  const input = validateInput(props);
  return {
    durationInFrames: Math.round(durationSeconds(input) * fpsOf(input)),
    fps: fpsOf(input),
    width: 1080,
    height: 1920,
  };
};

const defaultProps: CandidateRenderInput = {
  schema_version: '2.0',
  job_id: 'job-000000000000000000000000',
  template: 'protocol-frame',
  title: '候选模板',
  requested_duration_seconds: 40,
  resolved_duration_seconds: 40,
  fps: 30,
  scenes: [{heading: '固定输入', body: '仅接收服务端构造的结构化候选数据。', start_seconds: 0, end_seconds: 40}],
  captions: [{start: 0, end: 40, text: '离线候选'}],
  mascot: {asset: 'mascot/normal.svg', pose: 'normal'},
  audio: {asset: 'runtime/default.wav', duration_seconds: 1},
};

const defaultFlashProps: FlashVisualInput = {
  schema_version: '1.0',
  title: 'Flash 擦除时，如何安排看门狗服务窗口',
  duration_seconds: 50,
  fps: 30,
  scenes: [
    {start_seconds: 0, end_seconds: 10, heading: '擦除动作与独立看门狗同时运行', visual_kind: 'window'},
    {start_seconds: 10, end_seconds: 20, heading: '把操作拆成四个可观察阶段', visual_kind: 'sequence'},
    {start_seconds: 20, end_seconds: 30, heading: '先测最坏擦除时间，再计算窗口', visual_kind: 'budget'},
    {start_seconds: 30, end_seconds: 40, heading: '超出预算时进入受控恢复', visual_kind: 'recovery'},
    {start_seconds: 40, end_seconds: 50, heading: '四项检查，避免无界重试', visual_kind: 'checklist'},
  ],
};

export const RemotionRoot: React.FC = () => <>
  <Composition
    id="P1Candidate"
    component={CandidateVideo}
    durationInFrames={1200}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={defaultProps}
    calculateMetadata={calculateCandidateMetadata}
  />
  <Composition
    id="FlashWatchdog16x9"
    component={ReferenceFlashVisual}
    durationInFrames={Math.round(defaultFlashProps.duration_seconds * defaultFlashProps.fps)}
    fps={defaultFlashProps.fps}
    width={1920}
    height={1080}
    defaultProps={defaultFlashProps}
    calculateMetadata={({props}) => {
      const input = props as FlashVisualInput;
      return {
        durationInFrames: Math.round(input.duration_seconds * input.fps),
        fps: input.fps,
        width: 1920,
        height: 1080,
      };
    }}
  />
</>;
