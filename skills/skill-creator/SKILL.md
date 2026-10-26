---
name: skill-creator
description: Create or revise a portable agent skill with precise triggers, concise instructions, self-contained resources, and structural and behavioral checks. Use for skill packages rather than ordinary task documentation.
license: See LICENSE.openai.txt, LICENSE.anthropic.txt, and SOURCES.md
---

# Skill authoring

Build the smallest package that reliably improves the intended task. Instructions should preserve the user's scope and host permissions. No paid model API, evaluation platform, or vendor-specific installation path is required.

## Define and implement

1. Establish the outcome and realistic requests the skill should handle. Identify neighboring tasks it should not capture. Read the destination repository's conventions before editing.
2. Give the skill a lowercase hyphenated name matching its directory. Write YAML frontmatter with `name` and a concise `description` that says what the skill does and when to use it. Keep optional metadata accurate.
3. Write only guidance that changes decisions: prerequisites, essential workflow, operational constraints, outputs, failure behavior, and one useful example. Assume the agent can perform ordinary reasoning and editing.
4. Keep the entry point short. Link substantial conditional guidance from `references/`, deterministic helpers from `scripts/`, and output templates from `assets/`. Load only the resources relevant to the task.
5. Keep required resources inside the skill. Resolve paths relative to its installation directory, write outputs to a separate workspace, preserve licenses, and document network/credential requirements and side effects.
6. Avoid requiring a commercial tool when a local route achieves the outcome. Optional services must remain explicit choices under user authorization. Do not silently install tools or change permissions to make a workflow run.

Apply YAGNI to both instructions and helpers. Distinguish the requested outcome from a proposed workflow; preserve existing skill behavior and host permissions. Reuse resources already in the package, then standard-library facilities, native platform tools, and installed dependencies before adding a script or service. Add a helper only when a repeated operation benefits from deterministic execution. Do not create a runtime stack, configuration layer, or mandatory agent workflow for a task that concise instructions already handle. Resolve uncertain tool behavior with authoritative documentation or a focused experiment before prescribing it.

Before adding complexity for a speculative or vanishingly unlikely race or security edge case, explain the concrete failure mode, evidence for its likelihood (or uncertainty), implementation and maintenance cost, and simpler alternative. Get user buy-in for that scope expansion unless existing approval already covers the trade-off. Do not silently add theoretical robustness, weaken required controls, or delay an already-authorized fix for a demonstrated defect.

The optional initializer uses Python's standard library:

```sh
python scripts/init_skill.py example-skill --path /absolute/collection --resources references,assets
```

It creates a new directory and starter entry point and refuses an existing destination. Add only needed resources and replace scaffold placeholders before delivery; no generated UI metadata is required.

## Validate

The validator requires the pinned PyYAML dependency in [requirements.txt](requirements.txt):

```sh
python scripts/quick_validate.py /absolute/collection/example-skill
```

Check metadata, local links, invocation examples, missing-input handling, and helper behavior. Structural validation cannot establish routing or task quality. Use [behavioral evaluation](references/behavioral-evaluation.md) for a representative request, a boundary request, and a failure/missing-input case. An independent agent is useful only when available and authorized; a documented self-review is an acceptable fallback and must not be mislabeled.

After evaluation, relate each instruction and helper path to an actual requirement. Remove repeated guidance, unused resources, speculative options, and abstractions that add no reliability. Fix root causes revealed by representative cases; preserve useful regression cases instead of adding blanket rules for one-off failures. Keep independently installed skills self-contained, and pin any added dependencies with their applicable lockfiles.

Deliver the usable directory and actual verification outcomes. Do not claim tests passed if execution was unavailable.

Example: “Make a skill that summarizes local incident logs.” Specify the input schema, preserve timestamps and uncertainty, reject missing logs clearly, and verify a synthetic incident and an empty-input case without uploading logs to an external service.
