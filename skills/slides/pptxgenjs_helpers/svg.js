"use strict";

// Output compatibility normalization, NOT an untrusted-SVG security filter.
// The 8.5px relative-unit convention is retained for existing slide generators.
const namespace = "http://www.w3.org/2000/svg";

function sanitizeSvg(input) {
  let markup = String(input).replace(/<\?xml[\s\S]*?\?>/gi, "");
  const start = markup.search(/<svg(?=[\s/>])/i);
  if (start >= 0) {
    markup = markup.slice(start);
    const last = markup.toLowerCase().lastIndexOf("</svg>");
    if (last >= 0) markup = markup.slice(0, last + 6);
    else if (/^<svg\b[^>]*\/>/i.test(markup)) markup = markup.match(/^<svg\b[^>]*\/>/i)[0];
  }
  markup = markup.replace(/<svg\b([^>]*)>/i, (tag, attrs) => {
    if (/\sxmlns\s*=/.test(attrs)) return tag;
    return tag.replace(/^<svg/i, `<svg xmlns="${namespace}"`);
  });
  return markup
    .replace(
      /\b(width|height)\s*=\s*(["'])(\d*\.?\d+)(?:ex|em)\2/gi,
      (_, name, quote, magnitude) => `${name}=${quote}${Math.round(Number(magnitude) * 8.5)}px${quote}`,
    )
    .replace(/currentColor/g, "#000000");
}

function toDataUri(input) {
  const encoded = Buffer.from(input, "utf8").toString("base64");
  return `data:image/svg+xml;base64,${encoded}`;
}

module.exports = {
  toDataUri,
  sanitizeSvg,
  svgToDataUri: (input) => toDataUri(sanitizeSvg(input)),
};
