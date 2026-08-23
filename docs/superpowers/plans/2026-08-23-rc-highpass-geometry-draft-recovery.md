# RC High-Pass Geometry and Jianying Visibility Recovery Plan

**Goal:** Produce a corrected RC high-pass v6 candidate whose topology and Bode graph are geometrically correct, whose every frame is scanned, and whose E-drive Jianying draft is visible in the desktop app through a single verified junction.

1. Add red tests for resistor/wave separation, fc marker/curve alignment, all-frame scan reporting, and visible draft junction validation.
2. Add a geometry contract shared by render input/reporting; remove the topology sine overlay and render separate logical signal indications.
3. Replace the Bode graph with stacked magnitude/phase lanes and calculate curve markers from the same functions as the SVG paths.
4. Extend the post-render gate to decode and evaluate every frame, then visually inspect six key/transition frames.
5. Generate a fresh v6 Remotion visual, timing-bound Jianying draft, audible preview, and a non-overwriting C: junction to the E: draft.
6. Run focused and affected regressions, inspect the Jianying-visible draft structure, update Obsidian, commit, and push without phase promotion.
