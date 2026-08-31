import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Execute the existing pure builder, without invoking rendering or media writes.
const source = fs.readFileSync(new URL('../../scripts/render_phase1_topic_visual.mjs', import.meta.url), 'utf8');
const start = source.indexOf('function build(');
const end = source.indexOf('async function main(', start);
assert.ok(start >= 0 && end > start);
const build = vm.runInNewContext(`(${source.slice(start, end).trim()})`);
const script = {schema_version: '1.0', script_id: 'test', title: 'Evidence role contract'};
const scenes = [
  {scene_type: 'hook', narrative_role: 'hook', information_role: 'hook_question', source_refs: []},
  {scene_type: 'explain_verified_fact', narrative_role: 'explain_verified_fact', information_role: 'explain_verified_fact', source_refs: ['f1']},
  {scene_type: 'scope_boundary', narrative_role: 'scope_boundary', information_role: 'engineering_process_frame', source_refs: []},
  {scene_type: 'causal_path', narrative_role: 'causal_path', information_role: 'engineering_process_frame', source_refs: []},
  {scene_type: 'measurement_evidence', narrative_role: 'measurement_evidence', information_role: 'engineering_process_frame', source_refs: []},
].map((scene, index) => ({...scene, scene_index: index + 1, on_screen_knowledge: 'Check the evidence boundary'}));
const timing = {schema_version: '1.0', visual_duration_seconds: 5, segments: scenes.map((_, index) => ({index: index + 1, scene_start_microseconds: index * 1e6, scene_end_microseconds: (index + 1) * 1e6}))};
const plan = {schema_version: '1.0', script_id: 'test', scenes};
for (const aspect of ['16:9', '9:16']) {
  assert.equal(build(script, plan, timing, aspect).scenes.length, 5);
}
const invalidCases = [[1, {source_refs: []}], [2, {source_refs: ['invented_fact']}], [2, {information_role: 'unknown'}], [1, {source_refs: 'f1'}], [1, {source_refs: ['']}], [2, {scene_type: 'hook', narrative_role: 'hook', information_role: 'hook_question'}], [0, {scene_type: undefined}], [0, {scene_type: 'not_hook'}]];
invalidCases.push([2, {scene_type: 'hook', narrative_role: 'hook', information_role: 'engineering_process_frame'}], [0, {source_refs: ['f1']}], [0, {narrative_role: 'not_hook'}]);
for (const [index, patch] of invalidCases) {
  const altered = structuredClone(plan);
  Object.assign(altered.scenes[index], patch);
  assert.throws(() => build(script, altered, timing, '16:9'));
}
console.log('topic_evidence_builder_verified');

// Import the actual compiled Remotion validator. Layout measurement is separate;
// this pure validator must not require a browser or substitute fake references.
const {validateTechnicalSceneEvidence} = await import('../.contract-build/TechnicalExplainer.js');
assert.equal(typeof validateTechnicalSceneEvidence, 'function');
for (const scene of scenes) validateTechnicalSceneEvidence(scene);
for (const [index, patch] of invalidCases) {
  assert.throws(() => validateTechnicalSceneEvidence({...scenes[index], ...patch}));
}
console.log('topic_evidence_remotion_verified');
