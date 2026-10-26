"use strict";

// Keep the published namespace, including module order, in one place.
module.exports.VERSION = "1.2.0";
for (const entry of ["text", "image", "svg", "latex", "code", "layout", "layout_builders", "util"]) {
  Object.assign(module.exports, require(`./${entry}.js`));
}
