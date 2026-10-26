"use strict";

const prism = require("prismjs");
const loadLanguages = require("prismjs/components/");
const { readFileSync } = require("node:fs");

function buildThemeMap(cssModule = "prismjs/themes/prism-okaidia.css") {
  const palette = { plain: "FFFFFF", comment: "999999" };
  let css;
  try {
    css = readFileSync(require.resolve(cssModule), "utf8");
  } catch (_) {
    return palette;
  }
  for (const block of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const colour = /(?:^|;)\s*color\s*:\s*#([\da-f]{6}|[\da-f]{3})\b/i.exec(block[2]);
    if (!colour) continue;
    const hex = colour[1].length === 3 ? [...colour[1]].map((digit) => digit + digit).join("") : colour[1];
    for (const selector of block[1].matchAll(/\.token\.([\w-]+)/g)) palette[selector[1]] = hex;
  }
  return palette;
}

let palette;
function codeToRuns(source, language) {
  const aliases = { js: "javascript", ts: "typescript", py: "python", sh: "bash", yml: "yaml", html: "markup", xml: "markup" };
  const requested = String(language || "plain").toLowerCase();
  const id = aliases[requested] || requested;
  // The bundled loader resolves dependencies (e.g. TypeScript -> JavaScript).
  if (/^[a-z][a-z0-9-]*$/.test(id) && !prism.languages[id]) {
    try {
      require.resolve(`prismjs/components/prism-${id}.js`);
      loadLanguages(id);
    } catch (_) {
      /* Unavailable grammars produce an uncoloured listing. */
    }
  }
  palette ||= buildThemeMap();
  const listing = String(source ?? "").split("\n");
  const gutter = String(listing.length).length;
  const result = [];
  const append = (text, kind) =>
    result.push({
      text,
      options: {
        fontFace: "Consolas",
        fontSize: 14,
        color: palette[kind] || palette.plain,
      },
    });
  const visit = (node, kind = "plain") => {
    if (typeof node === "string") append(node, kind);
    else if (Array.isArray(node)) node.forEach((child) => visit(child, kind));
    else visit(node.content, node.type || kind);
  };
  listing.forEach((line, number) => {
    if (number) append("\n", "plain");
    append(`${String(number + 1).padStart(gutter)} `, "comment");
    const tokens = prism.languages[id] ? prism.tokenize(line, prism.languages[id]) : [line];
    visit(tokens.length ? tokens : [""]);
  });
  return result;
}

module.exports = { codeToRuns, buildThemeMap };
