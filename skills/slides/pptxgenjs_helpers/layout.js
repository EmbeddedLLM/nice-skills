"use strict";

// PptxGenJS stores inches in shape options and EMUs in presentation layouts.
const tolerance = 0.0001;
const settings = (shape) => shape?.data || shape?.options || {};
function box(shape) {
  const opts = settings(shape);
  const value = (name) => (typeof opts[name] === "number" ? opts[name] : 0);
  const viewport = opts.sizing?.type === "crop" ? opts.sizing : {};
  const x = value("x"),
    y = value("y");
  const w = typeof viewport.w === "number" ? viewport.w : value("w");
  const h = typeof viewport.h === "number" ? viewport.h : value("h");
  return { x, y, w, h, x2: x + w, y2: y + h };
}
function inferElementType(shape) {
  if (typeof shape?.type === "string" && shape.type) return shape.type;
  const opts = settings(shape);
  const candidates = [
    ["text", shape?.text || typeof opts.text === "string"],
    ["image", shape?.image || opts.path],
    ["chart", opts.chartType],
    ["shape", opts.shape || opts.line],
    ["media", opts.mediaType],
    ["table", opts.table || Array.isArray(opts.rows)],
    ["smartart", opts.smartArt],
  ];
  return candidates.find(([, present]) => present)?.[0] || "unknown";
}
function shapes(slide, caller) {
  if (!Array.isArray(slide?._slideObjects)) throw new Error(`Invalid slide object passed to ${caller}()`);
  return slide._slideObjects;
}
function selection(slide, indices, caller) {
  const objects = shapes(slide, caller);
  if (!Array.isArray(indices) || indices.length === 0) throw new Error("indices must be a non-empty array.");
  return [...new Set(indices)].map((index) => {
    if (!Number.isInteger(index)) throw new Error("Element indices must be integers.");
    if (index < 0 || index >= objects.length) throw new Error(`Element index out of bounds for ${caller}().`);
    return { index, object: objects[index], ...box(objects[index]) };
  });
}
function move(shape, axis, position) {
  const targets = new Set([shape.data, shape.options].filter((item) => item && typeof item === "object"));
  if (!targets.size) targets.add((shape.data = {}));
  for (const target of targets) target[axis] = position;
}
function compareElementPosition(slide, firstIndex, secondIndex) {
  const objects = shapes(slide, "compareElementPosition");
  if (![firstIndex, secondIndex].every(Number.isInteger)) throw new Error("Element indices must be integer values.");
  if ([firstIndex, secondIndex].some((i) => i < 0 || i >= objects.length))
    throw new Error("Element index out of bounds for compareElementPosition().");
  const a = box(objects[firstIndex]),
    b = box(objects[secondIndex]);
  const overlap = {
    x: Math.max(a.x, b.x),
    y: Math.max(a.y, b.y),
    w: Math.min(a.x2, b.x2) - Math.max(a.x, b.x),
    h: Math.min(a.y2, b.y2) - Math.max(a.y, b.y),
  };
  const result = { relation: "touching", containerIndex: null, containedIndex: null, aBounds: a, bBounds: b, intersection: null };
  if (Math.min(overlap.w, overlap.h) < -tolerance) {
    result.relation = "disjoint";
    return result;
  }
  if (overlap.w > tolerance && overlap.h > tolerance) {
    result.intersection = overlap;
    result.relation = "overlapping";
  }
  const contains = (outside, inside) =>
    ["x", "y"].every((axis) => outside[axis] <= inside[axis] + tolerance && outside[axis + "2"] >= inside[axis + "2"] - tolerance);
  const ab = contains(a, b),
    ba = contains(b, a);
  if (ab !== ba) {
    result.relation = "contained";
    result.containerIndex = ab ? firstIndex : secondIndex;
    result.containedIndex = ab ? secondIndex : firstIndex;
  }
  return result;
}
function alignSlideElements(slide, indices, alignment) {
  const chosen = selection(slide, indices, "alignSlideElements");
  const rules = {
    left: ["x", "w", 0],
    right: ["x", "w", 1],
    top: ["y", "h", 0],
    bottom: ["y", "h", 1],
    horizontallyCenter: ["x", "w", 0.5],
    verticallyCenter: ["y", "h", 0.5],
  };
  if (!Object.hasOwn(rules, alignment)) throw new Error(`Unsupported alignment option: ${alignment}`);
  const [axis, size, fraction] = rules[alignment];
  const low = Math.min(...chosen.map((item) => item[axis]));
  const high = Math.max(...chosen.map((item) => item[axis + "2"]));
  for (const item of chosen) move(item.object, axis, low + fraction * (high - low - item[size]));
}
function distributeSlideElements(slide, indices, direction) {
  const chosen = selection(slide, indices, "distributeSlideElements");
  if (!["horizontal", "vertical"].includes(direction)) throw new Error(`Unsupported distribution direction: ${direction}`);
  if (chosen.length === 1) return;
  const axis = direction === "horizontal" ? "x" : "y";
  const size = direction === "horizontal" ? "w" : "h";
  chosen.sort((a, b) => (Math.abs(a[axis] - b[axis]) < 1e-6 ? a.index - b.index : a[axis] - b[axis]));
  let cursor = chosen[0][axis];
  const extent = Math.max(...chosen.map((item) => item[axis + "2"])) - cursor;
  const occupied = chosen.reduce((total, item) => total + item[size], 0);
  const gap = (extent - occupied) / (chosen.length - 1);
  for (const item of chosen) {
    move(item.object, axis, cursor);
    cursor += item[size] + gap;
  }
}
function getSlideDimensions(slide, pptx) {
  const queue = [
    slide?._presLayout,
    slide?._slideLayout,
    slide?._pres?.layout,
    slide?._parent?.layout,
    slide?._layout,
    pptx?._presLayout,
    pptx?._layout,
    pptx?.layout,
    pptx?.presLayout,
  ];
  const visited = new Set();
  while (queue.length) {
    const current = queue.shift();
    if (!current || typeof current !== "object" || visited.has(current)) continue;
    visited.add(current);
    for (const [horizontal, vertical] of [
      ["width", "height"],
      ["w", "h"],
      ["cx", "cy"],
      ["slideWidth", "slideHeight"],
      ["slideWidthInches", "slideHeightInches"],
      ["widthInches", "heightInches"],
    ]) {
      const width = parseFloat(current[horizontal]),
        height = parseFloat(current[vertical]);
      if (![width, height].every((v) => Number.isFinite(v) && v > 0)) continue;
      const emu = Math.max(width, height) > 1000;
      return { width: width / (emu ? 914400 : 1), height: height / (emu ? 914400 : 1), source: emu ? "emu_converted" : "detected" };
    }
    queue.unshift(...["size", "slideSize", "layout", "slideLayout"].map((key) => current[key]));
  }
  throw new Error("getSlideDimensions(): Unable to determine slide dimensions from pptxgenjs internals.");
}
const label = (slide, deck) => {
  const n = deck?._slides?.indexOf(slide) ?? -1;
  return n < 0 ? "(Unknown slide index)" : `Slide ${n + 1}`;
};
// Slab clipping: a diagonal's bounding box alone cannot establish a collision.
function lineCrossesRectangle(line, rectangle) {
  let enter = 0,
    leave = 1;
  for (const [axis, size] of [
    ["x", "w"],
    ["y", "h"],
  ]) {
    const delta = line[size];
    if (!delta) {
      if (line[axis] < rectangle[axis] || line[axis] > rectangle[axis + "2"]) return false;
    } else {
      const times = [(rectangle[axis] - line[axis]) / delta, (rectangle[axis + "2"] - line[axis]) / delta];
      enter = Math.max(enter, Math.min(...times));
      leave = Math.min(leave, Math.max(...times));
    }
  }
  return enter <= leave + 1e-6;
}
function warnIfSlideHasOverlaps(slide, pptx, options = {}) {
  if (!Array.isArray(slide?._slideObjects)) {
    console.warn("Invalid slide object passed to warnIfSlideOverlaps()");
    return;
  }
  const entries = slide._slideObjects.map((object, index) => ({ object, index, type: inferElementType(object), ...box(object) }));
  const visible = entries.filter(({ object, type }) => {
    const opts = settings(object);
    return (
      !(options.ignoreLines && type === "line") && !(options.ignoreDecorativeShapes && type === "shape" && opts.line && opts.fill?.transparency >= 99)
    );
  });
  let overlaps = 0,
    contained = 0;
  for (let i = 0; i < visible.length; i++) {
    for (const b of visible.slice(i + 1)) {
      const a = visible[i];
      const comparison = compareElementPosition(slide, a.index, b.index);
      if (comparison.relation === "contained" && options.muteContainment === false) {
        contained++;
        console.warn(`${label(slide, pptx)}: element ${comparison.containedIndex} is fully contained within element ${comparison.containerIndex}.`);
      }
      if (comparison.relation !== "overlapping") continue;
      if ((a.type === "line") !== (b.type === "line")) {
        const line = a.type === "line" ? a : b;
        const rect = a.type === "line" ? b : a;
        if (line.w > 1e-6 && line.h > 1e-6 && !lineCrossesRectangle(line, rect)) continue;
      }
      overlaps++;
      const { w, h } = comparison.intersection;
      const severe = [a.type, b.type].includes("text") && Math.min(w, h) >= 0.1;
      const output = severe ? console.error : console.warn;
      output(
        `${label(slide, pptx)}: ${severe ? "Severe text overlap" : "Overlap"} between element ${a.index} (${a.type}) and element ${b.index} (${b.type}); intersection ${w.toFixed(3)} × ${h.toFixed(3)} in.`,
      );
    }
  }
  if (overlaps || contained) console.log(`${label(slide, pptx)}: Found ${overlaps} overlapping pair(s) and ${contained} containment case(s).`);
}
function warnIfSlideElementsOutOfBounds(slide, pptx) {
  if (!Array.isArray(slide?._slideObjects)) {
    console.warn("Invalid slide object passed to warnIfSlideElementsOutOfBounds()");
    return;
  }
  const dimensions = getSlideDimensions(slide, pptx);
  let count = 0;
  slide._slideObjects.forEach((object, index) => {
    const rect = box(object),
      problems = [];
    for (const [axis, extent, lowName, highName] of [
      ["x", "width", "left", "right"],
      ["y", "height", "top", "bottom"],
    ]) {
      if (rect[axis] < -tolerance) problems.push(`${lowName}=${rect[axis].toFixed(3)} < 0`);
      if (rect[axis + "2"] > dimensions[extent] + tolerance)
        problems.push(`${highName}=${rect[axis + "2"].toFixed(3)} > ${extent}=${dimensions[extent].toFixed(3)}`);
    }
    if (problems.length) {
      count++;
      console.warn(`${label(slide, pptx)}: Element ${index} (${inferElementType(object)}) exceeds slide bounds (${problems.join(", ")}).`);
    }
  });
  if (count) console.log(`${label(slide, pptx)}: Found ${count} element(s) extending beyond the slide bounds.`);
}
module.exports = {
  inferElementType,
  compareElementPosition,
  warnIfSlideHasOverlaps,
  alignSlideElements,
  distributeSlideElements,
  warnIfSlideElementsOutOfBounds,
  getSlideDimensions,
};
