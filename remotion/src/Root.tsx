import React from 'react';
import {Composition, type CalculateMetadataFunction} from 'remotion';
import {durationSeconds, fpsOf, validateInput, type CandidateRenderInput} from './contracts';
import {CandidateVideo} from './Video';
import {ReferenceFlashVisual, type FlashVisualInput} from './ReferenceFlashVisual';
import {ReferenceRcHighPassVisual, type RcHighPassVisualInput} from './ReferenceRcHighPassVisual';

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

const defaultRcHighPassProps: RcHighPassVisualInput = {
  schema_version: '1.0',
  title: 'RC 高通滤波器：从分水岭到相位超前',
  duration_seconds: 102,
  fps: 30,
  layout_contract_version: '1.0',
  geometry: {
    version: '2.0',
    topology: {
      resistor: {x: 485, y: 430, width: 100, height: 120},
      ground: {x: 485, y: 550, width: 100, height: 76},
      wave_paths: [],
    },
    bode: {
      x: {left: 118, right: 754, fc_ratio: 1},
      magnitude_lane: {top: 110, bottom: 350, min_db: -20, max_db: 0},
      phase_lane: {top: 420, bottom: 620, min_degrees: 0, max_degrees: 90},
      markers: {magnitude_fc: {db: -3.0103}, phase_fc: {degrees: 45}},
    },
  },
  visual_cues: [
    {cue_id: 'watershed', start_microseconds: 70_000_000, end_microseconds: 72_000_000},
    {cue_id: 'phase_lead', start_microseconds: 72_100_000, end_microseconds: 74_000_000},
    {cue_id: 'time_scale', start_microseconds: 74_100_000, end_microseconds: 76_000_000},
    {cue_id: 'design_fc', start_microseconds: 76_100_000, end_microseconds: 78_000_000},
    {cue_id: 'design_validate', start_microseconds: 78_100_000, end_microseconds: 80_000_000},
    {cue_id: 'next_preview', start_microseconds: 80_100_000, end_microseconds: 82_000_000},
  ],
  scenes: [
    {start_seconds: 0, end_seconds: 12, heading: '为什么变化通过，稳态却被挡住？', visual_kind: 'hook'},
    {start_seconds: 12, end_seconds: 40, heading: '串联电容，分压取输出', visual_kind: 'topology'},
    {start_seconds: 40, end_seconds: 68, heading: 'fc 是幅度和相位的分水岭', visual_kind: 'bode'},
    {start_seconds: 68, end_seconds: 87, heading: '相位超前，就是时间位移', visual_kind: 'phasor'},
    {start_seconds: 87, end_seconds: 102, heading: '三个轴，掌握动态滤波', visual_kind: 'summary'},
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
  <Composition
    id="RcHighPass1080x1920"
    component={ReferenceRcHighPassVisual}
    durationInFrames={Math.round(defaultRcHighPassProps.duration_seconds * defaultRcHighPassProps.fps)}
    fps={defaultRcHighPassProps.fps}
    width={1080}
    height={1920}
    defaultProps={defaultRcHighPassProps}
    calculateMetadata={({props}) => {
      const input = props as RcHighPassVisualInput;
      return {
        durationInFrames: Math.round(input.duration_seconds * input.fps),
        fps: input.fps,
        width: 1080,
        height: 1920,
      };
    }}
  />
</>;
