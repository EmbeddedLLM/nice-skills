# Portable HTML output

Choose the smallest implementation that supports the interactions. A single file with inline CSS and JavaScript often suffices. For an existing framework project, use its lockfile and build tools rather than introducing a competing stack.

The bundled Python 3 standard-library helpers create and export a simple artifact. Resolve the script paths from this skill directory; output paths refer to the user's writable project:

```sh
python scripts/init_artifact.py /absolute/new-project
python scripts/bundle_artifact.py /absolute/new-project/index.html /absolute/output.html
```

The initializer creates HTML, CSS, and JavaScript without package installation. Both commands refuse existing destinations. The exporter inlines local classic scripts, stylesheets, images, fonts, and supported media URLs. It rejects modules, deferred scripts, CSS imports, and unsupported asset forms. For React/TypeScript, use a compatible bundler and inliner installed in that project.

Inspect the exported file, not just the development server. Test controls, calculation results, console output, and all required assets. For offline delivery, disable networking and reload. Test `file://` explicitly if required: module loading and fetches can require a local HTTP server. Static inlining alone is not an offline guarantee.

Keep calculations and supplied data inspectable. Treat user input as text rather than executable HTML. Do not embed credentials, private remote URLs, or secret API keys in a shareable file. Explain unsupported export forms rather than silently omitting assets.
