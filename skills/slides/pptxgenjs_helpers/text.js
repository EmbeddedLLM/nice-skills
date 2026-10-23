"use strict";

// Estimates in inches. Skia performs font selection and shaping; final Office
// rendering is still required because its line-layout engine may differ.
const { Canvas } = require("skia-canvas");
const LineBreaker = require("linebreak");
const context = new Canvas(1, 1).getContext("2d");
const number = (value, fallback) => {
  const parsed = typeof value === "string" ? parseFloat(value) : value;
  return Number.isFinite(parsed) ? parsed : fallback;
};
function calcTextBoxHeightSimple(size, lines = 1, leading = 1.15, padding = 0.3) {
  return (size * lines * leading) / 72 + padding;
}
function insets(margin) {
  return Object.fromEntries(
    ["left", "right", "top", "bottom"].map((side) => [side, number(margin && typeof margin === "object" ? margin[side] : margin, 0) / 72]),
  );
}
function paragraphs(input, size, options) {
  const pieces = Array.isArray(input) ? input : [input];
  return pieces.flatMap((piece) => {
    const run = typeof piece === "object" && piece !== null ? piece : { text: piece };
    const style = { ...options, fontSize: size, ...run.options };
    const pt = number(style.fontSize, size);
    const face = style.fontFace || "Arial";
    const italic = style.italic || style.fontStyle === "italic";
    const bold = style.bold || String(style.fontWeight).toLowerCase() === "bold";
    const indent = number(style.indent, number(style.bullet?.indent, 0));
    return String(run.text ?? "")
      .split(/\r?\n/)
      .map((text) => ({
        text,
        css: `${italic ? "italic" : "normal"} ${bold ? "bold" : "normal"} ${(pt * 96) / 72}px ${JSON.stringify(face)}`,
        height: (pt * number(style.leading, 1.15)) / 72,
        after: number(style.paraSpaceAfter, 0) / 72,
        indent: Math.max(0, indent - (style.bullet ? 0 : number(style.hanging, 0))) / 72,
      }));
  });
}
function width(text, paragraph) {
  context.font = paragraph.css;
  return context.measureText(text).width / 96;
}
function lineCount(paragraph, available) {
  const text = paragraph.text;
  if (!text.trim()) return 1;
  const limit = Math.max(0.01, available - paragraph.indent);
  const iterator = new LineBreaker(text);
  const ends = [];
  for (let point; (point = iterator.nextBreak()); ) ends.push(point);
  let offset = 0,
    lines = 0;
  while (offset < text.length) {
    while (offset < text.length && /\s/u.test(text[offset])) offset++;
    if (offset === text.length) break;
    let end = offset;
    for (const point of ends) {
      if (point.position <= offset) continue;
      if (width(text.slice(offset, point.position).trimEnd(), paragraph) > limit + 1e-6) break;
      end = point.position;
      if (point.required) break;
    }
    if (end === offset) {
      // Code points avoid cutting surrogate pairs when a word exceeds the box.
      for (const character of text.slice(offset)) {
        const next = end + character.length;
        if (end > offset && width(text.slice(offset, next), paragraph) > limit + 1e-6) break;
        end = next;
        if (width(text.slice(offset, end), paragraph) > limit + 1e-6) break;
      }
    }
    offset = end;
    lines++;
  }
  return Math.max(1, lines);
}
function measure(items, available) {
  return items.reduce(
    (result, paragraph, index) => {
      const count = lineCount(paragraph, available);
      result.lines += count;
      result.height += count * paragraph.height + (index + 1 < items.length ? paragraph.after : 0);
      return result;
    },
    { lines: 0, height: 0 },
  );
}
function calcTextBox(fontSizePt, opts = {}) {
  const margins = insets(opts.margin);
  const padding = number(opts.padding, 0.3);
  const explicitLines = number(opts.lines, NaN);
  const result = Object.fromEntries(Object.entries(opts).filter(([key]) => !["text", "lines", "w", "h", "leading", "padding"].includes(key)));
  result.fontSize ??= fontSizePt;
  if (opts.margin != null) result.margin = margins;
  const finish = (w, lines, height) => ({
    ...result,
    w,
    h: height + margins.top + margins.bottom,
    lines,
    contentH: height,
    margins,
    topInset: fontSizePt / 360,
  });
  if (Number.isFinite(explicitLines)) {
    return finish(
      number(opts.w, 0) || null,
      explicitLines,
      Math.max(0, calcTextBoxHeightSimple(fontSizePt, explicitLines, number(opts.leading, 1.15), padding)),
    );
  }
  const items = paragraphs(opts.text ?? "", fontSizePt, opts);
  const fixedWidth = number(opts.w, NaN),
    fixedHeight = number(opts.h, NaN);
  const hasText = items.some((item) => item.text.length > 0);
  const mode = Number.isFinite(fixedWidth) ? "width" : Number.isFinite(fixedHeight) ? "height" : null;
  if (!hasText || !mode) throw new Error("calcTextBox(): insufficient information. Provide {lines} or ({w,text}) or ({h,text}).");
  if (typeof opts.fontFace !== "string" || !opts.fontFace.trim())
    throw new Error(`calcTextBox(): opts.fontFace is required when measuring by ${mode}.`);
  const requested = mode === "width" ? fixedWidth : fixedHeight;
  if (!(requested > 0)) throw new Error(`calcTextBox(): ${mode} must be > 0 in mode '${mode}'`);
  if (mode === "width") {
    const measured = measure(items, Math.max(0, fixedWidth - margins.left - margins.right));
    return finish(fixedWidth, measured.lines, Math.max(0, measured.height + padding));
  }
  const available = fixedHeight - margins.top - margins.bottom - padding;
  const minimumHeight = items.reduce((sum, item, i) => sum + item.height + (i + 1 < items.length ? item.after : 0), 0);
  if (minimumHeight > available + 1e-6) throw new Error("calcTextBox(): height too small for one-line layout at this font size");
  let high = Math.max(0.01, ...items.map((item) => width(item.text, item) + item.indent));
  // Retain whole words when solving for a width; fixed-width mode can break them.
  let low = Math.max(0.01, ...items.flatMap((item) => item.text.split(/\s+/u).map((word) => width(word, item) + item.indent)));
  high = Math.max(high, low);
  for (let step = 0; step < 40; step++) {
    const mid = (low + high) / 2;
    if (measure(items, mid).height <= available + 1e-6) high = mid;
    else low = mid;
  }
  const measured = measure(items, high);
  return finish(high + margins.left + margins.right, measured.lines, measured.height + padding);
}
function autoFontSize(textOrRuns, fontFace, opts = {}) {
  const w = number(opts.w, 0),
    h = number(opts.h, 0);
  if (w <= 0 || h <= 0) throw new Error("autoFontSize(): non-positive w or h");
  if (typeof fontFace !== "string" || !fontFace.trim()) throw new Error("autoFontSize(): fontFace is required as the 2nd positional argument.");
  const mode = String(opts.mode || "auto").toLowerCase();
  if (!["auto", "shrink", "enlarge"].includes(mode))
    throw new Error(`autoFontSize(): unsupported mode "${opts.mode}", expected "auto" | "shrink" | "enlarge"`);
  const reference = number(opts.fontSize, NaN);
  if (mode !== "auto" && !Number.isFinite(reference)) throw new Error("autoFontSize(): mode 'shrink' or 'enlarge' requires fontSize");
  let lower = number(opts.minFontSize, 1),
    upper = number(opts.maxFontSize, 1000);
  if (mode === "shrink") upper = Math.min(upper, reference);
  if (mode === "enlarge") lower = Math.max(lower, reference);
  if (!(lower > 0 && upper >= lower)) throw new Error("autoFontSize(): invalid minFontSize/maxFontSize bounds after normalization");
  const text = (Array.isArray(textOrRuns) ? textOrRuns : [textOrRuns])
    .map((run) => (typeof run === "object" && run ? (run.text ?? "") : (run ?? "")))
    .join("");
  let size = Math.max(lower, Math.min(upper, Number.isFinite(reference) ? reference : lower));
  if (text.trim()) {
    const fits = (pt) =>
      calcTextBox(pt, { ...opts, fontSize: pt, fontFace, text: textOrRuns, w, h: undefined, lines: undefined }).h <= h * 0.97 + 1e-6;
    // A bound that already fits is returned exactly; otherwise bisect to 0.05pt.
    if (fits(upper)) size = upper;
    else {
      size = lower;
      while (upper - lower > 0.05) {
        const candidate = (lower + upper) / 2;
        if (fits(candidate)) size = lower = candidate;
        else upper = candidate;
      }
    }
  }
  const output = { ...opts, x: number(opts.x, 0), y: number(opts.y, 0), w, h, fontSize: size };
  if (mode === "shrink") output.fit = "shrink";
  return output;
}
module.exports = { calcTextBoxHeightSimple, calcTextBox, autoFontSize };
