"use strict";

/**
 * Composite slide builders on top of PptxGenJS.
 *
 * Three shapes come up often enough to be worth a helper:
 *
 *   addImageTextCard(slide, opts)      one image with a caption under it
 *   addCardRow(slide, region, cards)   a row of those cards, evenly laid out
 *   addThreeLevelTree(slide, opts)     root -> mid -> leaf boxes with connectors
 *
 * All three measure text before placing it (see ./text), so a font face is
 * mandatory wherever a label is drawn: guessing a font would produce boxes that
 * do not match what PowerPoint renders. The card and tree builders return or
 * record the geometry they used, so a caller can hang further shapes off it.
 */

const { calcTextBox, autoFontSize } = require("./text");
const { imageSizingCrop, imageSizingContain } = require("./image");
const { getSlideDimensions } = require("./layout");

// Card defaults, in inches unless noted.
const CARD_WIDTH = 3.0;
const CARD_GAP = 0.15;
const CARD_IMAGE_HEIGHT = 2.2;
const CARD_FONT_SIZE = 14;

// Row defaults.
const ROW_MARGIN_X = 0.4;
const ROW_TOP = 1.6;
const ROW_GAP = 0.25;

// Tree defaults.
const TREE_TOP = 1.6;
const TREE_ROOT_W = 3.3333333;
const TREE_ROOT_H = 0.93333333;
const TREE_FONT_SIZE = 16;
const TREE_MID_DROP = 1.2;
const TREE_MID_MARGIN_X = 0.6;
const TREE_MID_MIN_GAP = 0.4;
const TREE_MID_MIN_W = 0.8;
const TREE_LEAF_W = 1.05;
const TREE_LEAF_H = 1.0666667;
const TREE_LEAF_DROP = 1.0;
const TREE_LEAF_MIN_GAP = 0.2;
const TREE_LEAVES_PER_MID_FALLBACK = 3;

const LEVEL_STYLE = {
  root: { color: "FFFFFF", fill: "0B0F1A" },
  mid: { color: "000000", fill: "A0BEC2" },
  leaf: { color: "000000", fill: "A6C1EE" },
};
const CONNECTOR_DEFAULT = { color: "000000", pt: 1 };

module.exports = {
  addImageTextCard,
  addCardRow,
  addThreeLevelTree,
};

// ---------------------------------------------------------------------------
// image + caption card
// ---------------------------------------------------------------------------

/**
 * Place one image (optional) with a caption box beneath it, and report the
 * geometry used. The caption is either fitted to a caller-fixed height
 * (`textBox.h`, adjusting the font size) or grown to fit a fixed font size.
 */
function addImageTextCard(slide, opts = {}) {
  const x = numberOr(opts.x, 0);
  const y = numberOr(opts.y, 0);
  const w = numberOr(opts.width, CARD_WIDTH);
  const gap = numberOr(opts.gap, CARD_GAP);
  const image = opts.image || {};
  const text = opts.text || "";
  const textBox = opts.textBox || {};

  const boxH = numberOr(image.boxHeight, CARD_IMAGE_HEIGHT);
  const placement = placeCardImage(slide, image, x, y, w, boxH);

  const textY = y + boxH + gap;
  const fontSize = numberOr(textBox.fontSize, CARD_FONT_SIZE);
  const fontFace = requiredFace(
    textBox.fontFace,
    "addImageTextCard(): textBox.fontFace is required for text measurement."
  );

  const fixedHeight = textBox.h != null && Number.isFinite(numberOr(textBox.h, NaN));
  const { height: hText, options: textOptions } = fixedHeight
    ? fittedTextBox(text, fontFace, fontSize, textBox, opts, { x, y: textY, w })
    : measuredTextBox(text, fontFace, fontSize, textBox, opts, { x, y: textY, w });

  slide.addText(text, textOptions);

  return {
    x,
    y,
    w,
    image: {
      x: placement?.x ?? x,
      y,
      w: placement?.w ?? w,
      h: placement?.h ?? boxH,
    },
    text: { x, y: textY, w, h: hText },
  };
}

/** Add the card image when a source was given; return the placement used. */
function placeCardImage(slide, image, x, y, w, boxH) {
  if (!image.path && !image.data) return undefined;

  const base = image.path ? { path: image.path } : { data: image.data };
  const source = image.path || image.data;
  const crop = image.crop || {};
  const sizing = (image.sizing || "crop").toLowerCase();

  const placement =
    sizing === "contain"
      ? imageSizingContain(source, x, y, w, boxH)
      : imageSizingCrop(source, x, y, w, boxH, crop.cx, crop.cy, crop.cw, crop.ch);

  slide.addImage({ ...base, ...placement });
  return placement;
}

/** Layout-first: the caller fixed the height, so the font size moves. */
function fittedTextBox(text, fontFace, fontSize, textBox, opts, box) {
  const fixedH = numberOr(textBox.h, 0);
  const fitted = autoFontSize(text, fontFace, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: fixedH,
    mode: textBox.mode || "auto",
    fontSize,
    minFontSize: textBox.minFontSize,
    maxFontSize: textBox.maxFontSize,
    margin: textBox.margin,
    paraSpaceAfter: textBox.paraSpaceAfter,
  });
  return {
    height: fixedH,
    options: {
      ...fitted,
      fontFace,
      color: textBox.color,
      align: textBox.align,
      valign: textBox.valign || "top",
      fill: opts.background,
    },
  };
}

/** Content-first: the font size is fixed, so the box grows to fit. */
function measuredTextBox(text, fontFace, fontSize, textBox, opts, box) {
  const layout = calcTextBox(fontSize, {
    text,
    w: box.w,
    fontFace,
    margin: textBox.margin,
    paraSpaceAfter: textBox.paraSpaceAfter,
  });
  return {
    height: layout.h,
    options: {
      x: box.x,
      y: box.y,
      w: box.w,
      h: layout.h,
      fontFace,
      fontSize,
      color: textBox.color,
      align: textBox.align,
      valign: textBox.valign || "top",
      paraSpaceAfter: textBox.paraSpaceAfter,
      margin: textBox.margin,
      fill: opts.background,
    },
  };
}

// ---------------------------------------------------------------------------
// card row
// ---------------------------------------------------------------------------

/**
 * Lay cards out side by side inside a region. Widths are equal by default;
 * `widthStrategy: "fixed"` keeps a caller-chosen card width and lets the group
 * be aligned left, centred or right inside the region.
 */
function addCardRow(slide, region, cards = [], options = {}) {
  const rx = numberOr(region.x, ROW_MARGIN_X);
  const ry = numberOr(region.y, ROW_TOP);
  const slideWidth = getSlideDimensions(slide).width;
  const rw = numberOr(region.w, slideWidth - rx * 2);
  const gap = numberOr(options.gap, ROW_GAP);
  const count = cards.length;
  if (count === 0) return [];

  const cardW =
    options.widthStrategy === "fixed"
      ? numberOr(options.cardWidth, rw / count - (gap * (count - 1)) / count)
      : (rw - gap * (count - 1)) / count;

  const totalWidth = cardW * count + gap * (count - 1);
  const align = options.align || "left";
  const offsetX =
    align === "center"
      ? (rw - totalWidth) / 2
      : align === "right"
      ? rw - totalWidth
      : 0;

  const placements = [];
  for (let i = 0; i < count; i++) {
    placements.push(
      addImageTextCard(slide, {
        ...cards[i],
        x: rx + offsetX + i * (cardW + gap),
        y: ry,
        width: cardW,
      })
    );
  }
  return placements;
}

// ---------------------------------------------------------------------------
// three-level tree
// ---------------------------------------------------------------------------

/**
 * Root box on top, a row of mid boxes under it, and a row of leaves under each
 * mid box, with a connector from every parent to every child. Mid-box width is
 * derived from `mid.spacing` when given, otherwise the row is fitted into the
 * available width with a minimum gap.
 */
function addThreeLevelTree(slide, opts = {}) {
  const slideWidth = getSlideDimensions(slide).width;
  const cx = numberOr(opts.centerX, slideWidth / 2);
  const topY = numberOr(opts.topY, TREE_TOP);

  const rootFace = faceOf(opts.root, "opts.root");
  const root = drawTreeNode(slide, opts.root, rootFace, {
    text: opts.root?.text || "",
    x: cx - numberOr(opts.root?.w, TREE_ROOT_W) / 2,
    y: topY,
    w: numberOr(opts.root?.w, TREE_ROOT_W),
    h: numberOr(opts.root?.h, TREE_ROOT_H),
    size: numberOr(opts.root?.fontSize, TREE_FONT_SIZE),
    level: "root",
  });

  // Every level's face is required up front, even when its row is empty.
  const midFace = faceOf(opts.mid, "opts.mid");
  const mid = planMidRow(opts.mid, root, cx, slideWidth);
  for (let i = 0; i < mid.labels.length; i++) {
    const x = mid.startLeft + i * (mid.w + mid.gap);
    drawTreeNode(slide, opts.mid, midFace, {
      text: mid.labels[i] || "",
      x,
      y: mid.y,
      w: mid.w,
      h: mid.h,
      size: numberOr(opts.mid?.fontSize, TREE_FONT_SIZE),
      level: "mid",
    });
    addConnector(slide, cx, topY + root.h, x + mid.w / 2, mid.y, opts.line);
  }

  const leafFace = faceOf(opts.leaf, "opts.leaf");
  const leafPlan = planLeafRow(opts.leaf, mid);
  for (let i = 0; i < mid.labels.length; i++) {
    const xBase = mid.startLeft + i * (mid.w + mid.gap);
    const childLabels = Array.isArray(leafPlan.labelsPerMid[i]) ? leafPlan.labelsPerMid[i] : [];
    const childCount = childLabels.length || TREE_LEAVES_PER_MID_FALLBACK;
    // Keep each family inside its parent's column without overlapping.
    const leafGap = Math.max(
      TREE_LEAF_MIN_GAP,
      (mid.w - childCount * leafPlan.w) / Math.max(1, childCount - 1)
    );
    const familyWidth = childCount * leafPlan.w + (childCount - 1) * leafGap;
    const leftX = xBase + (mid.w - familyWidth) / 2;

    for (let j = 0; j < childCount; j++) {
      const x = leftX + j * (leafPlan.w + leafGap);
      drawTreeNode(slide, opts.leaf, leafFace, {
        text: childLabels[j] || "",
        x,
        y: leafPlan.y,
        w: leafPlan.w,
        h: leafPlan.h,
        size: numberOr(opts.leaf?.fontSize, TREE_FONT_SIZE),
        level: "leaf",
      });
      addConnector(
        slide,
        xBase + mid.w / 2,
        mid.y + mid.h,
        x + leafPlan.w / 2,
        leafPlan.y,
        opts.line
      );
    }
  }
}

/** Measure one node's label, draw it, and report the box that was used. */
function drawTreeNode(slide, levelOpts, fontFace, spec) {
  const textOptions = autoFontSize(spec.text, fontFace, {
    x: spec.x,
    y: spec.y,
    w: spec.w,
    h: spec.h,
    mode: levelOpts?.mode || "shrink",
    fontSize: spec.size,
    minFontSize: levelOpts?.minFontSize,
    maxFontSize: levelOpts?.maxFontSize,
  });
  const palette = LEVEL_STYLE[spec.level];
  const fill = levelOpts?.fill || palette.fill;

  slide.addText(spec.text, {
    ...textOptions,
    align: "center",
    valign: "mid",
    fontFace,
    color: levelOpts?.color || palette.color,
    fill: { color: fill },
    line: { color: levelOpts?.line || fill },
  });
  return { x: spec.x, y: spec.y, w: spec.w, h: spec.h };
}

/** Mid-row geometry: labels, box size, gap, vertical position. */
function planMidRow(midOpts, root, cx, slideWidth) {
  const labels = Array.isArray(midOpts?.labels) ? midOpts.labels : [];
  const rootH = root.h;
  const rootW = root.w;
  const topY = root.y;

  const midH = numberOr(midOpts?.h, rootH);
  const midY = numberOr(midOpts?.y, topY + rootH + TREE_MID_DROP);
  const requestedSpacing = numberOr(midOpts?.spacing, NaN); // centre-to-centre
  const marginX = numberOr(midOpts?.marginX, TREE_MID_MARGIN_X);
  const availableRowWidth = slideWidth - marginX * 2;
  const count = labels.length;

  let midW = numberOr(midOpts?.w, NaN);
  if (!Number.isFinite(midW) && Number.isFinite(requestedSpacing)) {
    // Span between the first and last centres, then share what is left.
    const totalSpan = requestedSpacing * (count - 1) + 0;
    midW = Math.max(
      TREE_MID_MIN_W,
      Math.min(rootW, (availableRowWidth - totalSpan) / count)
    );
  }
  if (!Number.isFinite(midW)) {
    midW = Math.max(
      TREE_MID_MIN_W,
      (availableRowWidth - TREE_MID_MIN_GAP * (count - 1)) / count
    );
  }

  const gap = Math.max(
    TREE_MID_MIN_GAP,
    (availableRowWidth - midW * count) / Math.max(1, count - 1)
  );
  const totalWidth = midW * count + gap * (count - 1);

  return {
    labels,
    w: midW,
    h: midH,
    y: midY,
    gap,
    startLeft: cx - totalWidth / 2,
  };
}

function planLeafRow(leafOpts, mid) {
  return {
    labelsPerMid: Array.isArray(leafOpts?.labelsPerMid) ? leafOpts.labelsPerMid : [],
    w: numberOr(leafOpts?.w, TREE_LEAF_W),
    h: numberOr(leafOpts?.h, TREE_LEAF_H),
    y: numberOr(leafOpts?.y, mid.y + mid.h + TREE_LEAF_DROP),
  };
}

/** Straight connector between two points, flipped when it runs right-to-left. */
function addConnector(slide, x1, y1, x2, y2, line = {}) {
  slide.addShape("line", {
    x: Math.min(x1, x2),
    y: Math.min(y1, y2),
    w: Math.abs(x2 - x1),
    h: Math.abs(y2 - y1),
    line: {
      color: line.color || CONNECTOR_DEFAULT.color,
      pt: line.pt || CONNECTOR_DEFAULT.pt,
    },
    flipH: x2 < x1 ? true : undefined,
  });
}

// ---------------------------------------------------------------------------
// shared helpers
// ---------------------------------------------------------------------------

/** A trimmed, non-empty font face, or a refusal naming the missing option. */
function requiredFace(value, message) {
  const face = typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
  if (!face) throw new Error(message);
  return face;
}

/** Tree levels all refuse the same way, naming the option that is missing. */
function faceOf(levelOpts, optionPath) {
  return requiredFace(
    levelOpts?.fontFace,
    `addThreeLevelTree(): ${optionPath}.fontFace is required for text measurement.`
  );
}

function numberOr(value, fallback) {
  const n = typeof value === "string" ? parseFloat(value) : value;
  return Number.isFinite(n) ? n : fallback;
}
