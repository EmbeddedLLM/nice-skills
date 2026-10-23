# Behavioral evaluation of a skill

Read this when changing routing or workflow behavior and a structural validator cannot show whether the change helps. Adapted from Anthropic's Apache-licensed skill-creator; see the [license](../LICENSE.anthropic.txt).

1. Select a small, representative set of real tasks. Include a positive trigger, a near-miss that should not trigger, and a difficult case that exercises the changed guidance. Keep expected outcomes independent of the exact wording of the skill.
2. Record inputs, relevant environment/dependency versions, and success criteria before testing. Check observable outputs such as a working artifact, correct calculation, preserved template, or correctly avoided tool call.
3. Where the harness supports authorized agent evaluations, compare the same task with the prior skill (or without it) and the revised skill in separate contexts. Keep inputs and tools constant. Do not silently invoke a paid API or vendor CLI to run evaluations.
4. Inspect the actual artifacts as well as automated assertions. An assertion that merely finds a phrase from the instructions is weak evidence of quality. For subjective comparisons, hide which version produced each output if an independent reviewer is available.
5. Record failures, token/time observations when available, and the smallest useful revision. Separate measured observations from judgments; a single successful run is not a general success rate.
6. Preserve useful regression cases and repeat only the affected checks after a revision. Do not optimize the description to a tiny test set or broaden its trigger to improve a superficial score.

If independent executions are unavailable, perform and label a manual walkthrough. Never report a simulated walkthrough as a live agent evaluation. No evaluation harness, parallel delegation, or user approval loop is required for every small editorial change.
