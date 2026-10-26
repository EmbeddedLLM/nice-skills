# Scene, interaction, and motion delivery

Define a scene graph with semantic parts, pivots, sockets, local axes, and clear ownership of shared resources. Test transform order and the neutral pose before keyframes or controls. A rest-pose screenshot does not establish skinning quality: inspect bending, contact, foot sliding, interpenetration, and joint limits through the requested motion.

Retargeting needs compatible source/target skeleton definitions, scale, coordinate conversion, and a known rest pose. Model/code licenses do not automatically cover motion datasets, body models, pretrained weights, or a supplied performer's footage. Keep those inputs outside the bundle unless their own terms are verified; do not promise a complete motion-capture pipeline from a public repository license alone.

For an interactive web scene, keep essential information and controls in semantic HTML, provide keyboard behavior, and make a static/reduced-motion state useful. Pause unnecessary rendering while offscreen or hidden. Bound pixel ratio and quality to the target device; release textures, geometry, listeners, and animation loops when their owner is disposed. Use demand rendering for static scenes when the existing renderer supports it.

Record a representative desktop/mobile performance measurement with actual asset sizes and draw complexity. Add postprocessing only after establishing the scene's visual and performance need. A 3D hero must not block the user's primary action or hide loading/failure states.

Reopen exported GLB/FBX/OBJ in an appropriate consumer, checking units, axes, materials, textures, pivots/animation where the format supports them, and bundled dependencies. A preview image proves appearance from one view, not export parity. Report unavailable consumer checks and the source files needed to reproduce the export.
