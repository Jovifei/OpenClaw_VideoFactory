---
name: topic-intelligence
description: "Generate, deduplicate, evidence-check, score, and rank Chinese embedded-engineering short-video topics."
version: 0.2.0
metadata:
  openclaw:
    emoji: "🔎"
---

# Topic intelligence

## Inputs

- `config/account.yaml`
- `config/topic_rules.yaml`
- `config/account_columns.yaml`
- `config/mascot_usage.yaml`
- published topic history
- audience questions
- user project notes, Git commits, issue logs, and monthly reports
- current public web sources when trend information matters

For an explicit Phase 1 user topic, normalize the topic and perform Codex web
research automatically. Produce at least two unique sources, including one
official document, standard, research paper, or other primary source; link every
fact to source IDs. Pass the validated brief to `attach-research` without an
intermediate user gate.

## Rules

1. Generate at least ten raw candidates.
2. Prefer real engineering problems the user can defend in comments.
3. Search history and semantic similarity before scoring.
4. Verify all material technical claims with primary sources when possible.
5. Never use a crawler as the default research method.
6. Do not generate a topic based only on popularity; account fit and visual explainability are mandatory.
7. Reject claims that cannot be verified.
8. Output the top 3–5 topic cards.
9. In user-topic mode, comparables are optional (maximum three) and may contain
   only URL, title, hook style, structure, pace, and visual grammar. Do not retain
   paths, frames, audio, transcripts, logos, provider/render/publish controls, or
   recognizable expression.

## Topic card

Each card must include:

- topic;
- audience pain;
- hook;
- core answer;
- 3–5 beat outline;
- visual approach;
- cover text;
- target duration;
- required evidence;
- production difficulty;
- risk;
- score breakdown.

## Auto selection

Only auto-select when:

- total score >= configured threshold;
- source verification passes;
- no duplicate within the configured window;
- no unresolved copyright or safety issue;
- the production path has a deterministic fallback.


## Column quota

Before ranking, calculate the rolling 28-video mix. Penalize candidates that would push the AI secondary line above 25% or the embedded mainline below 65%.

AI-hot-topic candidates require an event date, two reliable sources, and a clear engineering consequence.
