# UI and native apps

Read the platform's current guidance for the installed SDK and the project's existing view code before adding UI. Reuse the project's components, layout helpers, and theme. Prefer platform controls, icons, panels, and permission flows over custom versions, because native components carry accessibility, localization, and system behavior that a copy must rebuild.

Give each piece of UI state one owner. Derive displayed values from that owner instead of storing a second copy. When a default depends on other state, such as selecting the first item when nothing is selected, decide where that default is stored and when it changes. Persist it in the owner when later updates must keep it. Otherwise compute it on read.

Keep update and render paths free of side effects. A function that refreshes labels, enables controls, or draws a view must not change model state, start work, or request permission. Hidden mutations in these paths depend on call order and frequency, which makes the behavior hard to reproduce.

Keep UI mutation on the main thread or the platform's UI actor. Run file, network, and decode work in the background. Tag each asynchronous request with a generation or token. Discard a result when the user has since changed the selection, folder, or document, so that an obsolete result cannot replace the current state.

Treat the platform's permission and sandbox model as the trust boundary. Request access at the operation that needs it. Keep the granted scope alive while work that uses it is in flight. When the user cancels a permission request, keep the current state unchanged and visible.

Give each interactive element an accessible name, role, and keyboard path. Check that menu items and toolbar controls are enabled only when their action can run. When a control changes meaning, such as View becoming Open for a folder, update its title, tooltip, and accessibility label together.

Test state transitions through the controller or view model with synthetic fixtures: open, select, refresh, navigate, cancel, and return. Verify layout, rendering, and accessibility in the target environment. When a check needs the real platform and it is unavailable, report it as unverified with the exact command or manual step.
