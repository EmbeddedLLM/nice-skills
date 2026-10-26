# Writing quality

## Contents

- [Editorial review for documents](#editorial-review-for-documents)
- [Failure modes in professional writing](#failure-modes-in-professional-writing)
- [Human readers and the author's voice](#human-readers-and-the-authors-voice)

## Editorial review for documents

Review the writing before final formatting, and run the relevant checks again after any substantial revision. The examples below exist to help you recognise a problem and then rewrite the _actual_ document — apply a suggested phrasing only where the source and the section support that meaning, and never carry dates, roles, results, or other facts across from an example.

### Read headings as an outline

Read the title and every section heading together, with no body text. They should convey the subject, the scope, and the shape of the document. Then check that each heading describes what its section really contains.

When a heading is vague, reconsider what the section is for before polishing words; when an existing heading already does the job, leave it alone.

| Framing that obscures                | Plainer label, if the section supports it |
| ------------------------------------ | ----------------------------------------- |
| Momentum heading into the next phase | Rollout Plan for Q3                       |
| What the numbers are telling us      | Regional Sales by Quarter                 |
| Navigating the road ahead            | Risks and Mitigations                     |

Background, definitions, and process descriptions take a plain subject label. A factual finding works as a heading only when the section establishes that finding. Follow the title and heading rules in `SKILL.md`, including the ban on punctuation.

### Use paragraphs to explain relationships

Each paragraph makes one point and shows how its facts or actions connect. The document has to stand on its own, with no presenter nearby to supply the missing links. Write complete sentences and let their lengths vary naturally. When one sentence carries several actions, state their sequence or dependency if the source supports it.

Three fragments — "Sign-off needed. Compliance reviews the form. Training starts after sign-off." — become one sentence: "Compliance must sign off on the form before training starts." The actor and the condition survive; the relationship between them becomes visible.

Use lists for distinct items a reader needs to identify, follow, or compare, and keep a three-item list when all three items matter. Do not pad a list to make a trio, do not fall into the same three-part rhythm everywhere, and never invent an owner, a sequence, or a causal link to make thin source material sound concrete.

### Unpack compressed labels and unnecessary compounds

Swap dense modifiers and abstract labels for ordinary phrases that say what you mean. Rewrite the phrase; do not merely strip its hyphens.

| Compressed                          | Clearer                               |
| ----------------------------------- | ------------------------------------- |
| Launch-critical readiness checklist | Checks required before launch         |
| Cross-functional alignment velocity | How quickly the teams reach agreement |

The first rewrite suits a section listing what launch requires. If the original meant a checklist that is already complete, keep that status: "Checks completed before launch." A plainer label still has to carry the intended meaning.

Keep official names, defined terms, and established technical vocabulary where precision depends on them. Explain an unfamiliar term the first time the audience meets it, then use it consistently. Keep ordinary grammatical hyphens where they clarify.

### Preserve the claim when simplifying

Check every rewrite against its source. Numbers stay attached to their units, comparison baseline, and time period. Conditions and uncertainty survive, including the difference between "may", "should", and "must". Recommendations stay separate from findings, and associations stay separate from causal claims.

| Source | Edit to avoid | Safer |
| --- | --- | --- |
| Error rates could drop if batch size shrinks | Smaller batches reduce errors | Error rates could drop with smaller batches |
| Attendance returned to 84 percent of its pre-strike level | Attendance rose by 84 percent | Attendance reached 84 percent of its pre-strike level |
| A structurally smaller workforce | A permanent reduction in staff | Keep the structural claim, or explain the underlying change from the source; do not infer permanence |

Where the original is ambiguous, go back to the source or keep the uncertainty. Do not quietly adopt the stronger reading, add a result, or drop a qualification to make the prose sound decisive.

### Use punctuation and voice in context

Prefer the active voice when the actor is known and relevant. Use the passive when the action or result deserves the emphasis, or when the source does not name an actor — and never invent one just to avoid a passive.

Punctuation in body text exists to make relationships and qualifications clear. Revise punctuation that is there to manufacture emphasis or rhythm. Apply these checks in context instead of banning a construction outright; the separate rule against punctuation in titles and headings still applies.

## Failure modes in professional writing

The patterns below are contextual signals, not forbidden tokens. Penalise one when it is conspicuous, repeated, unearned, or actively harmful to the writing that was asked for. Do not fail an otherwise strong document over a single phrase or a single punctuation mark.

### Packaged as formula rather than analysis

**Flag when** the underlying claim may be fine but arrives as a stock formula, a slogan, a staged cadence, a canned emotional phrase, or a strained metaphor instead of clear analysis. This includes colons, semicolons, and dashes deployed for rhythm or emphasis rather than meaning.

Examples of the problem:

- Inflated contrast: "This isn't a status report — it's a mirror held up to how we plan." / "Tooling is not an afterthought. It is the foundation of delivery."
- Words that do not fit their subject: "Proceed only when all five readiness gates are green," said of criteria for a budget memo.
- Parallelism and semicolons doing work the sentence cannot: "The earlier draft fenced off the affected routes; the revised draft removes that layer entirely" — where it is also unclear what "that layer" is.
- Dashes used for punchy interruption: "Objective: capture what shifted — and what we deliberately left alone — during the migration window." Plain sentences read better.
- Stock formula: "The dashboard not only saves time, but also transforms how teams plan." / "cleaner, faster, and more intuitive."
- Slogan or fragment as a transition: "From spreadsheets to a single source of truth." / "One fleet. One schedule. No surprises." / "Close the quarter. Keep the audit trail." / "Headcount is flat. Demand isn't." / "Backlog is not capacity. Plan for both." / "This is not just another migration. The better framing is modernization." / "It's not a bug it's a workflow gap."
- Colons stacked for effect: "Ops: hold the rollout. Support: expect tickets. Everyone: keep Friday clear."
- Staged cadence: "Different teams, same underlying incentive: defer the work that has no owner."
- Canned empathy: "I completely understand how stressful and frustrating this outage must have been for your team."
- Balance with no real trade-off: "While automation improves throughput, it also introduces new considerations."
- Mannered parallelism: "The picture is clear: costs are rising; margins are thinning; patience is running out — and the window for action is now."
- Inflated significance: ordinary facts dressed as legacy, identity, industry turning points, or an "evolving landscape."
- Promotional or travel-guide tone: unrequested salesy praise, brochure atmosphere, reflexive adjectives such as "vibrant", "rich", "renowned", "groundbreaking", "seamless", or "nestled."
- Vague authority and synthetic consensus: "experts argue", "observers note", "scholars say", "several sources suggest" — with nothing behind them.
- Canned endings: a generic "challenges", "legacy", or "future outlook" paragraph that the content never earned.
- Habitual triads: sets of three adjectives, abstract nouns, clauses, or examples that make the prose feel manufactured.
- Overlong parallel enumerations: rhythmic catalogues of who/what/where clauses piled up to simulate exhaustiveness after the point has landed. Penalise the accumulation unless the task genuinely needs the list.
- Repeated negative parallelism: "not X, but Y", "not only X, but also Y", "not just X, but Y", "no X, no Y, just Z."
- Dense clusters of AI-associated vocabulary: "delve", "pivotal", "robust", "tapestry", "underscore", "showcase", "foster", "intricate", "landscape", "testament", "vibrant".
- Mechanical bold-label bullets: run after run of "**Label:** explanation" when that structure was neither useful nor requested.

**Not a defect:** a construction that states a concrete distinction, gives a clear warning, or quotes an identified source — "the fault is in the retry handler, not the queue." Nor is parallel structure or punctuation a defect when it separates a genuine list, contrast, or logical relationship — "the amber light means prepare to stop, and the red light means stop."

### Claims the reader cannot check

**Flag when** the reader cannot tell what changed, why a benefit follows, what e supports a claim, or what drove a decision — because evidence, causality, actors, or observable meaning are missing.

Examples of the problem:

- Empty abstraction: "This unlocks value, fosters alignment, and drives meaningful impact." / "Labour is scarce; demand is not; so the segment grows." / "Breadth plus tooling, not the original product, is where the growth comes from."
- Meaning the reader cannot recover: "Every routine task gets the same agentic loop" — which loop, applied to what?
- A benefit bolted on at the end: "The portal consolidates key information, ensuring a seamless user experience."
- Inflated significance or unnamed authority: "This represents a profound shift" or "Research consistently shows this approach improves outcomes," with no source and none excluded.
- Informal language standing in for a fact: "The platform team is doing the heavy lifting" instead of "Most of the migration work is done by the platform team"; "The next release raises the bar" instead of "Projected Q3 revenue is $46M."
- Process narrated instead of a reason: "After several rounds of cross-functional review, we aligned on the next phase."
- Oversimplification that loses the meaning: "Where to draw the line on speed investments" trimmed to "Where to draw the line"; "When faster shipping drives growth rather than merely adding cost" trimmed to "When faster shipping drives growth."

**Not a defect:** a claim backed by a concrete result, source, constraint, or approval requirement — "The change removes one approval step"; "The 14 March accessibility audit found 9 missing labels"; "Legal and Security must approve the exception before release."

**The fix:** name the observable change, the source, the deciding constraint, or the actual trade-off.

### Longer than it needs to be

**Flag when** the same meaning could be shorter and clearer without losing a necessary qualification — the reasoning is present but the wording is long, indirect, compressed, bureaucratic, jargon-heavy, or over-hedged.

Examples of the problem:

- Bureaucratic phrasing: "Stakeholders should be informed of the operational implications associated with this transition."
- Structure that fights the reader: "The clean end state is therefore not 'the platform replaces every product.' It is: shared primitives provide durable identity and lifecycle; the runtime provides portable execution; each surface becomes an orientation onto that shared graph." → "The platform provides a portable execution runtime every surface can reuse, alongside shared identity and lifecycle primitives."
- Same problem, smaller scale: "The most important improvement over the earlier proposals was not the third mode. It was the unified sidebar… they would no longer behave like separate applications with separate navigation." → "The unified sidebar meant modes decided how a thread starts, while navigation stayed shared."
- Compressed abstraction: "The practical event ceiling remains anchored to both a headcount cap and a percentage cap."
- Indirect comparison: "The update reads as a broader continuation of requests rather than a list of named restricted zones."
- Over-hedging: "It may potentially be worth considering whether the team could possibly defer the release."
- Padding: "At this point in time, it would be advisable for the team to begin the process of reviewing the draft."
- Unexplained jargon: "The workflow operationalizes a cross-functional enablement layer for downstream value realization." Likewise, instead of "Restrained colour versus visual noise: a navy-and-gray palette reads as calm and credible," write "We moved to a simpler palette — navy and gray, no loud colours."
- A recommendation wrapped in abstractions: "Prioritize promise-date clarity and reliability before network acceleration: customers rank on-time delivery above sheer speed." → "Prioritize dependable two-to-three-day delivery and accurate promise dates; customers rank on-time delivery above speed."

**Not a defect:** accurate technical terms, legal conditions, or explained uncertainty — "The API returns 429 when the client exceeds the rate limit"; "The estimate is preliminary because two regions have not reported"; "The vendor may terminate only after giving 30 days' written notice."

**The fix:** concrete subjects and verbs; the shortest accurate wording; only the uncertainty markers that correspond to real unknowns.

### Structure that delays the point

**Flag when** setup, repetition, or formatting postpones the point or makes the document harder to scan.

Examples of the problem:

- Generic scene-setting: "In today's fast-moving regulatory environment, compliance reporting matters more than ever."
- Restating the request: "When it comes to reducing onboarding time, there are several strategies worth considering."
- Meta-announcement: "Below is a polished and comprehensive rewrite tailored to your needs."
- Redundant conclusion: "In conclusion, adopting these practices can help the organization achieve its goals."
- Excessive structure: a two-sentence answer spread over six headings and twelve bullets.

**Not a defect:** framing that narrows scope, corrects the request, explains an omission, or helps a reader navigate reference material — "This memo covers the two launch decisions due Friday"; "Each endpoint uses Request, Response, and Errors headings so it can be looked up quickly."

**The fix:** start with the answer or the decision; delete generic setup and repeated recaps; use the lightest structure that helps the reader act or find something.

### Baseline expectations

- Direct, natural prose that would earn an A from a demanding editor.
- Lead with the point.
- Concrete nouns, strong verbs.
- No needless words, repeated conclusions, or redundant framing.
- Sentences that vary in length naturally.
- No throat-clearing, inflated claims, vague abstractions, generic headings, or ornamental transitions.
- No canned AI phrasing — in particular "not just X, but Y", "the better framing is", and gratuitous contrast pairs.
- Keep the useful nuance: careful writing must not become overconfident writing.
- Preserve deliberate warmth, humour, informality, and domain vocabulary.
- Invent no facts, context, commitments, or evidence.
- Never mention the editorial framework in the output unless the user asks.

### What a strong document looks like

Score above 80 when:

- Above all, there is **no** writing slop — slop being the buckets above — and any expert professional would believe a human wrote it. Any slop at all puts the score below 60 percent.
- The response answers the task directly and leads with the conclusion or decision.
- Each major claim names a concrete subject and states an observable result, comparison, or constraint.
- Claims carry their evidence: a number, a source, an example, an approval requirement, or a stated basis.
- Facts, interpretation, recommendation, and uncertainty are distinguishable, with caveats that are local and specific.
- Every heading and bullet adds information, and the amount of structure fits the task.
- The reader can tell what a finding changes for a decision, an owner, or a next action.

## Human readers and the author's voice

Documents in this package are written for people, in a container, and reviewed as rendered pages.

User instructions come first, and the style of an existing document or supplied reference is preserved.

1. Read the request and the source files. Identify the author, the recipient, and what the document must help that recipient understand or do.
2. Decide what kind of document is needed — letter, memo, report, proposal, procedure, form, or another requested format — and choose the structure that fits that use.
3. Read any supplied writing examples and inspect their layout. Follow the relevant tone, sentence patterns, headings, and mix of prose, lists, and tables. Keep the task's facts; do not borrow facts from a style example.

### Write in the author's voice

- **Strongly prefer writing directly in the author's voice**, using "I" or "we" where that is natural and appropriate to the document. Unless the request specifies another role, write as the user — or as the person or team they represent — addressing the intended recipient.
- Present the update, recommendation, or request yourself. Do not narrate what the author or their organisation might say.
- Match the tone, language, and sentence structure of natural human writing for similar documents and situations. Supplied examples are the primary reference when they exist; keep the voice appropriate to author, audience, and purpose.
- Keep the speaker's register consistent with the relationship: an analyst writing to peers, managers, or investors should sound like that analyst writing to those readers.
- Do not invent the author's experience, authority, or commitments.
