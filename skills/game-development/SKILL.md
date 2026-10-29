---
name: game-development
description: Build, debug, optimize, or prepare a game using the project's engine, with task-specific guidance for gameplay, assets, UI, input, physics, AI, saves, networking, and release preparation. Supports Godot, Unity, Unreal, Ebitengine, Roblox, Bevy, Defold, LÖVE, pygame, Phaser, PixiJS, and Three.js.
license: Apache-2.0; see LICENSE.txt and NOTICE.txt
---

# Game development

Detect the existing engine and version from project files before choosing APIs. Read the minimal engine/task combination from [GUIDES.md](GUIDES.md); the 76 guides and their supporting references are bundled under `library/`. They are reference modules of this one independently installable skill. Resolve paths inside each guide relative to its directory, and named companion guides through the index.

Typical fingerprints: `project.godot`, Unity's `ProjectSettings/ProjectVersion.txt`, an Unreal `.uproject`, Ebitengine imports in `go.mod`, Roblox project files, a Bevy dependency in `Cargo.toml`, Defold's `game.project`, or the web engine in `package.json`. If multiple applications coexist, use the requested target. If no engine is established, clarify or propose a suitable choice; do not silently replace the user's stack.

## Work in a playable slice

Identify the player action, success/failure, target platform, controls, and constraints. Build the smallest playable loop, verify it in the real engine, and then add the relevant discipline or genre guidance. Keep presentation feedback separate from simulation, preserve deterministic rules when the game needs them, and test input across frame rates and device types.

Read only the needed references: engine fundamentals, then discipline, then genre or release workflow. Upstream fixed defaults are starting points; project rules, user requirements, and host permissions win. The library does not authorize installing engines, spending money, uploading builds, creating store listings, or changing shared infrastructure.

## Local helpers

Nine Python helpers inspect Godot, Unity, Defold, Ebitengine, Steam build layouts, and raster assets; Ebitengine also supplies project and macOS bundle creation. Their containing guides document flags and failure behavior. Checkers use the standard library; raster inspection/preview needs the pinned Pillow in `library/disciplines/create-game-assets/scripts/requirements.txt`. A passing static check does not prove the game runs or a store accepts it.

Example, from the skill directory:

```sh
python library/godot/godot-nodes-scenes/scripts/check_godot_project.py /path/to/game --json
```

Use `--help` for each helper before first use. Inspect synthetic fixtures or a copy before using a generator/packager on existing work. Engine/SDK versions, optional importers, platform signing, and publishing credentials belong to the destination project; no engine or proprietary runtime is bundled.

Deliver the requested source/build with actual playtest, regression, performance, and export evidence. Report unavailable engine or platform checks. Example: "Fix a Godot platformer's jump and save checkpoint." Read Godot movement, the platformer guide, and save systems; test jumping, collision, reload, and corrupted-save recovery in the project's version without publishing anything.

[Sources and notices](SOURCES.md) explain the adaptation and separately licensed starter notices.
