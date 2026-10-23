# Hand-painted 2D character animation

Use this when the film is an acted cartoon rather than typographic motion graphics: a character wants something, tries, fails or gets it, and the drawing itself is the style. It is an abridged adaptation of the _Claude Animation Base_ guide by John Heibel (MIT; see [SOURCES.md](../SOURCES.md)), kept for the craft rules that do not depend on that kit's engine. The kit itself is bundled at [`assets/hand-painted-cartoon/`](../assets/hand-painted-cartoon/): read its `ANIMATION_GUIDE.md` for the drawing, emotion and shot API, `src/clawd.js` for the character and its 31 emotions, `docs/views.jpg` and `docs/emotions.jpg` for the model sheets, and `render.mjs` for contact sheets, frame strips and MP4 output. It needs `npm install` in that directory (p5, p5.brush, puppeteer-core) and Chrome plus ffmpeg; it is optional, and everything below can be implemented on another 2D brush engine.

The rules below assume a code-drawn character on a 2D canvas with a brush/pigment engine (`p5.brush`, a canvas brush library, or your own stroke renderer) and a fixed whole-number timeline. Read them before drawing anything; they decide more of the result than any single helper.

## The three goals

Every rule serves one of them.

- **Handmade.** It should look painted frame by frame: brush strokes, ink lines that boil, flat 2D, no lettering.
- **Alive.** Something is always moving and something is always happening. Faces act instead of snapping, and characters are big enough to feel.
- **One piece.** It is one short film, not a pile of clips. Plan it before drawing it, and link every scene to the next.

Underneath all three the viewer has to be able to follow it. Timing is the rule generated animation breaks most often.

## The rules

### 1. The medium is solid

- **Paint, do not draw primitives.** Characters get flat wash colour plus an ink outline; backgrounds get soft fill shapes, usually with no outline or a thin one. Plain `rect`/`ellipse`/`fill` calls read as 2000s Flash.
- **The linework boils.** Reseed the jitter a fixed number of times per second (12 is a good default) so every drawing wobbles slightly. Anything that must stay put from frame to frame (star positions, tuft heights, texture) needs a stable hash of its own index, not the frame's random stream. Give each separate element its own seed, or one moving thing makes everything drawn after it jitter.
- **Everything is flat 2D.** No projected 3D, no `rotateY`, no depth faked with maths. A character turns through **drawn key views** — front, three-quarter, side, back three-quarter, back — exactly like a model sheet. Depth comes from overlap, scale and colour (farther is smaller, bluer, paler).
- **Light is the one exception.** Pigment-mixing engines mix colour like paint, so a yellow glow painted over blue turns green and a thin wash turns grey. Add real light with an additive glow pass drawn under the paper grain instead.
- **Soft palette, no pure black or white.** Use the palette's ink and cream. Keep colours harmonious and the character clearly readable against the background.

### 2. No text

- **Show it, don't write it.** No captions, titles, object labels, signs, speech bubbles, words on screens, or typed sound effects. Models overuse text more than any other device.
- **Reactions are painted marks, never letters:** an exclamation mark as a shape, a question mark, zzz, sweat, hearts, a bulb, a rain cloud.
- **A sign that repeats the story is the classic failure.** If the character holds a sign saying "I'm lost", the shot has failed; show them looking left, then right, the map upside down, a sweat drop.
- If the brief truly needs a word (a name, a shop sign that is the joke), paint it into the scene once, in one or two words.

### 3. Something happens in every scene

- **Every shot needs an event:** something changes between its first frame and its last. The character wants something, finds something, tries, fails, reacts or gets it. "The character stands in a meadow being cute" is not a shot.
- **One focal action at a time,** staged with a clear silhouette and nothing competing for attention.
- **Cause, then reaction.** When something happens, the character reacts to it: a take, an emotion change, a turn toward it. The reaction is often the funniest part, so give it time.
- **Pay it off.** Whatever a shot sets up gets resolved on screen, in that shot or a later one.

### 4. Timing: model the viewer

You know what happens because you wrote the code. The viewer sees it once, at full speed, for the first time. For every moment, ask what the viewer needs to understand and how long that will take, and time it for that.

- **Write the reads.** For each shot, list in order what the viewer must understand. Each item is a _read_: time for the eye to find it, time to understand it, and a moment to register before the next thing starts. Small, distant, fast or subtle things take longer than big, central, obvious ones.
- **One read at a time.** When two things happen at once the viewer sees only one. Put a cause and its reaction in sequence, not on top of each other.
- **Fast actions, slow meanings.** A motion can be very quick if it is anticipated; what it means needs held time. Anticipation tells the viewer where to look, the hold after lets them understand it. Moving quickly through what does not matter and slowly through what does is what gives a film rhythm; one constant speed makes it flat and hard to follow.
- **Lead the eye.** The viewer looks at whatever moves, is bright, is big or is being looked at. Before an important read, get the eye there — the character looks at it, the camera moves to it, it lights up first — and allow time for the eye to travel.
- **Let the reads set the length.** A shot with many reads cannot be short, and a shot whose reads have landed should not be padded. That includes the last shot: its final read needs time to land before the video ends.

### 5. Alive

- **Nothing is ever still.** Every emotion has its own idle motion, cameras drift or push, grass sways, stars twinkle, the linework boils. A frozen frame reads as a bug.
- **Faces act, they never snap.** Change moods through one acted emotion function that does anticipation, a squint, a take and overshoot around every change. Never swap eyes and mouth by hand between two frames.
- **Move like a cartoon, not a machine** (next section).
- **The character is big.** A medium shot fills a third of the frame; a close-up fills most of it. Tiny characters are for wide establishing shots only, and never for the whole film.
- **Everything moves on a beat,** even silently: one tempo drives idles, bounces and gestures, and hits land on it.

## Animation principles

These fix the main defect of code-written motion: every part moving at once, on the same curve, by the same amount.

- **Anticipation.** Before a big move, a small move the other way: a crouch before a jump, a wind-up before a throw, a squint before a take.
- **Squash and stretch.** Bodies squash on impact and stretch when fast, keeping their volume.
- **Slow in, slow out.** Almost nothing moves at a constant speed. Run progress through an easing instead of a plain linear interpolation.
- **Weight.** How something starts and stops says what it weighs. Heavy things take longer to start and stop and land with little bounce; light things snap into motion and flutter to rest.
- **Arcs.** Living things move on arcs, not straight lines: thrown props, hops, arm swings, head turns.
- **Overlapping action and follow-through.** The eyes lead, the body follows, and arms, hats, props and tails drag behind, overshoot and settle last. Offset each part's timing slightly from the part it hangs off.
- **Avoid twinning.** Code copies values, so both arms end at the same angle, both eyes blink together and a crowd bounces in unison. Give one arm the action and the other something smaller; offset timings, phases and seeds.
- **Exaggeration.** Push poses and takes further than feels natural; in a short cartoon, subtle reads as nothing.
- **Strong key poses.** Each shot's storytelling poses must read as stills, with a clear silhouette. If the key poses do not read, motion will not fix it.
- **Show the thought.** A character notices, thinks, then acts, and the eyes move first.
- **Secondary action.** A bobbing hat, a popping emote, stirring grass — it supports the main action and never competes with it.

## Workflow

### 1. Storyboard before any scene code

Write `STORYBOARD.md` with a logline, the world and its palette, the recurring motif, the character's emotion arc, and the shot list. For each shot record what is seen, its event, the reaction, the camera, the transitions in and out, and — the part generated animation always skips — its **reads with start and end times**.

Check the storyboard against the rules: an event in every shot, every read landing before the next starts, a transition at every seam, no text anywhere, and an ending that rhymes with the opening. If a shot's reads do not fit its length, lengthen the shot or cut a read. Never squeeze them.

### 2. Build one shot at a time

Block the key poses first and check them as stills at the key times; add the motion between them once they read. Wrap each shot as a function of local time, keep the camera moving slightly even in a locked-off shot, and end every seam with a transition (a wipe, an iris, a painted shape crossing frame) so the film is one piece.

### 3. Look at it: the review loop

You cannot judge motion by reading code. Render and look at every shot, several times, at three zoom levels:

- **Contact sheet** — every shot's first, middle and last frame, all at once: the shape of the whole piece.
- **Frame strip** — every frame of one moment (a turn, a take, a jump, a throw, a transition): the motion itself.
- **Full-resolution crops** — faces, hands, contacts between props and hands, glows.

Read the images, list what is wrong, fix the biggest thing first, and repeat. Check that props touch hands, that the character is not floating, and that no two shots look like different worlds.

### 4. Optional music

Set the project tempo to the song's and the first downbeat offset; land hits, cuts and takes on beats, and give each musical phrase its own visual. **Lyrics are not text**: act the meaning of a line instead of printing it.

## Common failures

Generated cartoons fail in the same ways. Check the storyboard and the sheets against this list:

- signs, captions, labels or speech bubbles with words
- the character standing still and smiling while nothing happens
- everything moving at one brisk speed, events stacked, no holds
- moments over before the viewer understands them
- a tiny character in a big empty landscape for the whole film
- faces that snap from one expression to the next
- mechanical motion: linear moves, every part moving at once, both arms or several characters in sync
- timid poses and takes that barely read
- jittery linework, or still things re-boiling every frame because something moving before them shifted the random stream
- hard cuts everywhere, or a film that just starts and stops
- 3D rotation, perspective boxes or projected turns
- primitive shapes, gradients or digital glows mixed into the paint
- muddy green-grey glows from painting yellow over blue
- props floating near a hand instead of touching it
- every shot a different world with nothing linking them

## Adapting this to another engine

The bundled kit supplies one brush-based engine, a character rig and an emotion library. Keep the rules and map the rest:

- If you do not use that engine, implement the three primitives it assumes: a painted fill, an ink outline, and a seeded boil. Everything else is poses and timing. If you do use it, copy the kit out of the skill directory before editing, expose `window.render(t)` for this skill's renderer, and keep the kit's own licence file with your copy.
- Watercolour fills are expensive without a GPU. On integrated graphics, replace the soft fills with flat washes or paper-colour fields and say so in your report.
- If the character design is supplied, keep it; otherwise design your own views and emotions first and treat the model sheet as part of the deliverable.
- Verify the finished film with the stills, strips and crops above before delivery, and report which checks you ran.
