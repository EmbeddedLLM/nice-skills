---
name: procedural-3d
description: Reconstruct objects or characters from reference images as editable procedural 3D models, or build and verify a Blender or Three.js scene. Use for code-authored geometry, pivots, assembly, and staged visual matching; not for claiming exact hidden geometry from one image.
license: Apache-2.0 and BSD-3-Clause and MIT; see SOURCES.md
---

# Procedural 3D reconstruction

Use the user's chosen renderer and existing project. This package provides a portable modeling workflow; it does not install Blender, Three.js, a model generator, or an MCP server. A supplied image and local renderer suffice. Read [reconstruction and review](references/reconstruction.md) before modeling; use [scene delivery](references/scene-delivery.md) for animation, interaction, rigs, or web delivery.

1. Inspect the actual reference and identify what makes the subject recognizable. Separate observed geometry from inferred/hidden regions. Record intended use, scale when known, coordinate convention, and delivery format.
2. Write a compact part hierarchy: semantic names, proportions, materials, attachment points, pivots, and required motion. Match camera and silhouette before detail.
3. Build in passes: blockout, structure, form, materials, lighting, interaction, optimization. Render the relevant view after each consequential pass. A wrong identity feature cannot be averaged away by an overall similarity score.
4. Check multiple views and the real output. For an assembly, verify intended contact, clearance, and attachment; do not repair intentional overlap blindly. For animation, verify neutral-pose preservation and joint limits before a polished sequence.
5. Deliver editable source and the requested export with units, assumptions, dependencies, asset notices, and evidence. Label approximation and unverified regions honestly.

Example: "Rebuild this desk lamp as an interactive Three.js object." Use a parent hierarchy for base, arm, and shade; put pivots at the hinges; compare reference-camera and side views; test the hinge controls and exported scene. One photograph establishes proportions, not certified physical dimensions.

No proprietary textures, pretrained weights, or reference art are bundled. Acquire external assets only under compatible terms; see [SOURCES.md](SOURCES.md). Apply existing project rules and authorization to scene mutation, downloads, and external integrations.
