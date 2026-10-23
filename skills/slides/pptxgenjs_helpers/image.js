"use strict";

// Image probing and sizing for pptxgenjs decks.
//
// `getImageDimensions` accepts a filesystem path, a data URI, a raw SVG string,
// or a Buffer, and reports width, height, aspect ratio, and format without
// loading a decoder. The two sizing helpers turn that into the geometry
// pptxgenjs needs for "cover" (crop) and "contain" placement.

const fs = require("fs");

const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const SVG_PROBE_BYTES = 200;
const CSS_DPI = 96;
const EM_EX_FALLBACK_PX = 16; // rough, but em/ex are rare in generated SVG
const SVG_FALLBACK_SIZE = 100;
const EPSILON = 1e-6;

// ---------------------------------------------------------------- input handling

// Normalise any accepted source to a Buffer plus a label used in error text.
function readInputAsBuffer(source) {
  if (!source) throw new Error("Image source is empty");
  if (Buffer.isBuffer(source)) return { buffer: source, type: "buffer" };

  if (typeof source !== "string") throw new Error("Unsupported image source type");

  if (source.startsWith("data:")) {
    const comma = source.indexOf(",");
    const payload = comma !== -1 ? source.slice(comma + 1) : source;
    // The helpers here emit base64; fall back to URI-decoded and then raw text.
    try {
      return { buffer: Buffer.from(payload, "base64"), type: "dataUri" };
    } catch (_notBase64) {
      try {
        return { buffer: Buffer.from(decodeURIComponent(payload), "utf8"), type: "dataUri" };
      } catch (_notUriEncoded) {
        return { buffer: Buffer.from(payload, "utf8"), type: "dataUri" };
      }
    }
  }

  if (source.includes("<svg")) return { buffer: Buffer.from(source, "utf8"), type: "rawSvg" };

  return { buffer: fs.readFileSync(source), type: "path" };
}

// ------------------------------------------------------------------- sniffing

function hasPrefix(buf, bytes) {
  return buf.length >= bytes.length && bytes.every((value, index) => buf[index] === value);
}

const FORMATS = [
  {
    type: "png",
    // 24 bytes is the smallest buffer whose IHDR width/height can be read.
    matches: (buf) => buf.length >= 24 && hasPrefix(buf, PNG_SIGNATURE),
    // IHDR carries width and height, big-endian, at 16 and 20.
    size: (buf) => ({ width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) }),
  },
  {
    type: "jpeg",
    matches: (buf) => buf.length > 3 && buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff,
    size: (buf) => jpegSize(buf),
  },
  {
    type: "gif",
    matches: (buf) =>
      buf.length >= 10 &&
      hasPrefix(buf, [0x47, 0x49, 0x46, 0x38]) &&
      (buf[4] === 0x39 || buf[4] === 0x37) &&
      buf[5] === 0x61,
    size: (buf) => ({ width: buf.readUInt16LE(6), height: buf.readUInt16LE(8) }),
  },
  {
    type: "webp",
    matches: (buf) =>
      buf.length >= 16 && hasPrefix(buf, [0x52, 0x49, 0x46, 0x46]) &&
      buf[8] === 0x57 && buf[9] === 0x45 && buf[10] === 0x42 && buf[11] === 0x50,
    size: (buf) => webpSize(buf),
  },
  {
    type: "svg",
    matches: (buf) => buf.slice(0, SVG_PROBE_BYTES).toString("utf8").includes("<svg"),
    size: (buf) => svgSize(buf),
  },
];

// Start-of-frame markers: SOF0-3, SOF5-7, SOF9-11, SOF13-15.
function isStartOfFrame(marker) {
  return (
    (marker >= 0xc0 && marker <= 0xc3) ||
    (marker >= 0xc5 && marker <= 0xc7) ||
    (marker >= 0xc9 && marker <= 0xcb) ||
    (marker >= 0xcd && marker <= 0xcf)
  );
}

function jpegSize(buf) {
  let offset = 2;

  while (offset < buf.length) {
    if (buf[offset] !== 0xff) {
      offset += 1;
      continue;
    }

    const marker = buf[offset + 1];
    if (isStartOfFrame(marker)) {
      return { width: buf.readUInt16BE(offset + 7), height: buf.readUInt16BE(offset + 5) };
    }

    const segmentLength = buf.readUInt16BE(offset + 2);
    if (!Number.isFinite(segmentLength) || segmentLength < 2) break;
    offset += 2 + segmentLength;
  }

  throw new Error("JPEG size not found");
}

// RIFF container: https://developers.google.com/speed/webp/docs/riff_container
function webpSize(buf) {
  const riffSize = buf.readUInt32LE(4) + 8;
  let offset = 12; // first chunk

  while (offset + 8 <= riffSize && offset + 8 <= buf.length) {
    const tag = buf.slice(offset, offset + 4).toString("ascii");
    const chunkSize = buf.readUInt32LE(offset + 4);
    const data = offset + 8;

    if (tag === "VP8X") {
      // Extended format: 24-bit canvas dimensions, each stored minus one.
      return {
        width: buf.readUIntLE(offset + 12, 3) + 1,
        height: buf.readUIntLE(offset + 15, 3) + 1,
      };
    }

    if (tag === "VP8 " && data + 10 < buf.length) {
      // Lossy: the frame header carries 14-bit dimensions.
      return {
        width: buf.readUInt16LE(data + 6) & 0x3fff,
        height: buf.readUInt16LE(data + 8) & 0x3fff,
      };
    }

    if (tag === "VP8L" && data + 5 <= buf.length) {
      // Lossless: 14-bit dimensions packed across four bytes.
      const b0 = buf[data + 1];
      const b1 = buf[data + 2];
      const b2 = buf[data + 3];
      const b3 = buf[data + 4];
      return {
        width: 1 + (((b1 & 0x3f) << 8) | b0),
        height: 1 + (((b3 & 0xf) << 10) | (b2 << 2) | ((b1 & 0xc0) >> 6)),
      };
    }

    offset += 8 + ((chunkSize + 1) & ~1); // chunks are padded to an even size
  }

  throw new Error("Unsupported WEBP variant for size detection");
}

function cssLengthToPixels(value) {
  if (!value) return null;

  const match = String(value).trim().match(/([0-9.]+)\s*(px|pt|em|ex|cm|mm|in|%)?/i);
  if (!match) return null;

  const amount = parseFloat(match[1]);
  switch ((match[2] || "px").toLowerCase()) {
    case "px":
      return amount;
    case "pt":
      return (amount * CSS_DPI) / 72;
    case "in":
      return amount * CSS_DPI;
    case "cm":
      return (amount * CSS_DPI) / 2.54;
    case "mm":
      return (amount * CSS_DPI) / 25.4;
    case "em":
    case "ex":
      return amount * EM_EX_FALLBACK_PX;
    default:
      return null; // percentages and anything unrecognised
  }
}

function svgSize(buf) {
  const text = buf.toString("utf8");
  const open = text.indexOf("<svg");
  const close = text.indexOf("</svg>");
  const markup = open !== -1 && close !== -1 ? text.slice(open, close + 6) : text;

  const declared = (attribute) => {
    const found = markup.match(new RegExp(`\\b${attribute}\\s*=\\s*"([^"]+)"`, "i"));
    return found ? cssLengthToPixels(found[1]) : null;
  };

  let width = declared("width");
  let height = declared("height");

  // Fall back to the viewBox when an attribute is missing or not absolute.
  if (width == null || height == null) {
    const viewBox = markup.match(/\bviewBox\s*=\s*"([^"]+)"/i);
    if (viewBox) {
      const parts = viewBox[1].trim().split(/\s+/).map(Number);
      if (parts.length === 4) {
        const [, , boxWidth, boxHeight] = parts;
        if (!width && boxHeight) width = boxWidth;
        if (!height && boxWidth) height = boxHeight;
      }
    }
  }

  return {
    width: width || SVG_FALLBACK_SIZE,
    height: height || SVG_FALLBACK_SIZE,
  };
}

// ------------------------------------------------------------------ public API

function getImageDimensions(pathOrData) {
  const { buffer, type } = readInputAsBuffer(pathOrData);

  const format = FORMATS.find((candidate) => candidate.matches(buffer));
  if (!format) {
    const suffix =
      type === "path" && typeof pathOrData === "string" ? ` (path: ${pathOrData})` : "";
    throw new Error("Unsupported image format for provided source" + suffix);
  }

  const { width, height } = format.size(buffer);
  return {
    width,
    height,
    aspectRatio: width > 0 && height > 0 ? width / height : 1,
    type: format.type,
  };
}

// Default crop fractions: centre the image and trim whichever axis overflows
// the target box.
function centredCropFractions(aspectRatio, boxAspect) {
  if (aspectRatio >= boxAspect) {
    const widthFraction = boxAspect / aspectRatio;
    return { cx: (1 - widthFraction) / 2, cy: 0, cw: widthFraction, ch: 1 };
  }
  const heightFraction = aspectRatio / boxAspect;
  return { cx: 0, cy: (1 - heightFraction) / 2, cw: 1, ch: heightFraction };
}

function imageSizingCrop(source, x, y, w, h, cx, cy, cw, ch) {
  const { aspectRatio } = getImageDimensions(source);
  const boxAspect = w / h;

  if (cx === undefined || cy === undefined || cw === undefined || ch === undefined) {
    ({ cx, cy, cw, ch } = centredCropFractions(aspectRatio, boxAspect));
  }

  // Derive the virtual (uncropped) size from the width, then check it against
  // the height; if the two disagree beyond rounding, derive from the height
  // instead so the crop window still lands exactly on the target box.
  let virtualW = w / cw;
  let virtualH = virtualW / aspectRatio;
  if (Math.abs(virtualH * ch - h) > EPSILON) {
    virtualH = h / ch;
    virtualW = virtualH * aspectRatio;
  }

  return {
    x,
    y,
    w: virtualW,
    h: virtualH,
    sizing: {
      type: "crop",
      x: cx * virtualW,
      y: cy * virtualH,
      w,
      h,
    },
  };
}

function imageSizingContain(source, x, y, w, h) {
  const { aspectRatio } = getImageDimensions(source);
  const boxAspect = w / h;

  // Fit inside the box, then centre on whichever axis has room left over.
  const fitted =
    aspectRatio >= boxAspect
      ? { w: w, h: w / aspectRatio }
      : { h: h, w: h * aspectRatio };

  return {
    x: x + (w - fitted.w) / 2,
    y: y + (h - fitted.h) / 2,
    w: fitted.w,
    h: fitted.h,
  };
}

module.exports = {
  getImageDimensions,
  imageSizingCrop,
  imageSizingContain,
};
