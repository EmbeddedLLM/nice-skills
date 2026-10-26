"use strict";

// Each call returns independently mutable PptxGenJS options.
exports.safeOuterShadow = (color = "000000", opacity = 0.25, angle = 45, blur = 3, offset = 2) => ({
  type: "outer",
  color,
  opacity,
  angle,
  blur,
  offset,
});
