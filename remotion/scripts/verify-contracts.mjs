import assert from 'node:assert/strict';
import {validateInput, TEMPLATE_IDS} from '../.contract-build/contracts.js';

const legacy = {
  schema_version: '1.0',
  job_id: 'job-0123456789abcdef01234567',
  template: 'protocol-frame',
  title: 'Modbus 响应字节计数',
  scenes: [{heading: '一个字节', body: '字节计数字段描述后续数据字节数。'}],
  captions: [{start: 0, end: 10, text: '字节计数不是寄存器数量'}],
  mascot: {asset: 'mascot/normal.svg', pose: 'normal'},
  audio: {asset: 'runtime/job-0123456789abcdef01234567/voice.wav', duration_seconds: 10},
};

const current = {
  ...legacy,
  schema_version: '2.0',
  requested_duration_seconds: 40,
  resolved_duration_seconds: 40,
  fps: 30,
  scenes: [{heading: '一个字节', body: '字节计数字段描述后续数据字节数。', start_seconds: 0, end_seconds: 40}],
  captions: [{start: 0, end: 40, text: '字节计数不是寄存器数量'}],
  audio: {...legacy.audio, duration_seconds: 38.5},
};

for (const template of TEMPLATE_IDS) assert.equal(validateInput({...current, template}).template, template);
assert.equal(validateInput(legacy).schema_version, '1.0');
assert.throws(() => validateInput({...current, requested_duration_seconds: 24}), /requested_duration_invalid/);
assert.throws(() => validateInput({...current, resolved_duration_seconds: 61}), /resolved_duration_invalid/);
assert.throws(() => validateInput({...current, scenes: [{...current.scenes[0], end_seconds: 39}]}), /scene_timing_invalid/);
assert.throws(() => validateInput({...current, audio: {...current.audio, asset: 'https://example.invalid/voice.wav'}}), /audio_asset_invalid/);
assert.throws(() => validateInput({...current, mascot: {...current.mascot, asset: '../secret.svg'}}), /mascot_asset_invalid/);
assert.throws(() => validateInput({...current, captions: [{start: 0, end: 40, text: '第一行\n第二行\n第三行'}]}), /caption_invalid/);
assert.equal(validateInput({...current, captions: [{start: 0, end: 40, text: '123456789012345678\n123456789012345678'}]}).captions.length, 1);
console.log(JSON.stringify({status: 'contracts_validated', templates: TEMPLATE_IDS.length, versions: ['1.0', '2.0']}));
