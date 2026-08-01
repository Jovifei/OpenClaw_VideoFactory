import React from 'react';
import {Composition, type CalculateMetadataFunction} from 'remotion';
import {durationSeconds, fpsOf, validateInput, type CandidateRenderInput} from './contracts';
import {CandidateVideo} from './Video';

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

export const RemotionRoot: React.FC = () => <Composition
  id="P1Candidate"
  component={CandidateVideo}
  durationInFrames={1200}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={defaultProps}
  calculateMetadata={calculateCandidateMetadata}
/>;
