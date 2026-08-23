# RC High-Pass Reference Reconstruction Design

## Goal

Create a 9:16 local review candidate about an RC high-pass filter using the supplied video's generic chapter rhythm and technical-card grammar, while generating all script, diagrams, animation, narration, and subtitles anew.

## Non-goals and safety boundary

- The supplied MP4 remains an analysis-only reference. No source frame, audio, full transcript, watermark, creator identity, or recognizable shot sequence is imported.
- This is not a pixel-identical copy and does not change the current Phase 1 status.
- Pink Pig remains off. The background palette is selected from the technical topic, not from the mascot brand.
- HeyGen is an optional newly generated narration/benchmark adapter. Remotion remains the sole picture renderer and `jianying-editor-skill` remains the sole Jianying backend.

## Design

The composition is 1080x1920 at 30 FPS with a target duration of approximately 102 seconds. Five voice-first windows follow the reference's broad arc:

1. Hook/title: why a capacitor and resistor can pass change but reject steady state.
2. Topology: series capacitor, shunt resistor, input/output labels, and signal path.
3. Quantitative behavior: cutoff frequency `fc = 1/(2πRC)`, -3 dB at `fc`, and phase lead.
4. Time/phase intuition: Bode curve, phasor, and waveform motion reveal what changes around `fc`.
5. Summary/next preview: cutoff, phase, and time constant as a compact matrix.

The theme token is `technical_neutral`: warm light-gray canvas, white cards, charcoal text, mint amplitude, orange phase, and violet time-constant accents. All content stays inside a 72px left/right safe margin and a 180px bottom subtitle reserve. Headings wrap naturally and use explicit max widths; axis labels use smaller bounded text; no visual subtitle is burned in.

HyperFrames rules are represented in the layout contract: explicit scene starts/durations, one timeline authority, end-state-first layout, deterministic motion, and transition-owned scene exits. Remotion renders the SVG/HTML-like diagrams. The Jianying draft receives the visual-only MP4, exact narration segments from the timing manifest, and exactly one native subtitle track.

## Failure handling

- Script, timing, layout contract, or source hash mismatch stops before rendering.
- Post-render checks fail closed on wrong canvas, text/layout boxes outside the safe area, black/frozen samples, missing/silent audio, C-drive paths, burned-in subtitles, or decode failure.
- A HeyGen failure records `unavailable` and falls back to the pinned local SAMI adapter; it never blocks the visual render or causes a false pass.
- Jianying draft creation failure is recorded separately from render failure; automatic export is never attempted.

## Evidence

The job writes the original brief/script, storyboard, timing manifest, visual-only render report, post-render quality report, assembled audio preview report, and Jianying draft report under `reports/phase1/`. Generated media and drafts remain on E:.
