---
name: resolve-recipients
description: Disambiguate people and bound recipient groups before an authorized message, invitation, or meeting action. Use for ambiguous names, cross-platform identities, or requests such as everyone on a project; this skill resolves identities and does not send.
license: MIT
---

# Resolve recipients

Return a defensible recipient set with identifiers and concise evidence, or the clarification needed to resolve it. Use supplied rosters/history or available authorized directory, mail, chat, and calendar tools. A particular paid communication platform is not required.

## Resolve the intended audience

1. Extract the requested action, surface, names, group scope, project, time period, and relationship clues. Preserve explicit additions and exclusions.
2. Search relevant sources using exact names and context. Rank exact user anchors first, then direct relevant history, recent project participation, and shared context with other named recipients. Contact frequency alone does not establish identity.
3. Resolve each individual, then check whether the group fits the request. Map identities across services only through a solid anchor such as an exact work email or explicit profile link; similar names are insufficient.
4. For groups, prefer a current authoritative roster. Separate core participants from observers, former participants, bots, and mailing lists. Channel membership or an old meeting is not proof of current inclusion.
5. Proceed with the resolved set only when each identity is clearly supported and no plausible rival remains. If candidates conflict or “everyone” lacks a defined boundary, ask one concise question distinguishing the candidates by relevant work context.

With no directory or history access, use an explicit address supplied by the user or request a roster/disambiguator. Never invent an address or pretend a search ran. Do not broaden the audience beyond the user's scope.

## Verify and hand off

Check current identifiers, exclusions, and cross-surface mappings. Keep project-specific disambiguations scoped to the project. Expose only information needed to distinguish people. Sending, scheduling, and publishing remain governed by the user's authorization and the host's permissions; resolution alone grants none.

Example: “Email Alex the Aurora plan.” If the roster contains two Alexes, use project evidence to distinguish them. If both remain plausible, ask “Alex Chen from Aurora design or Alex Reed from operations?” and leave the recipient unset until answered.
