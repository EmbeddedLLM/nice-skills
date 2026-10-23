"use strict";

const { svgToDataUri } = require("./svg.js");
let renderEquation;

exports.latexToSvgDataUri = function (source, display = true) {
  if (!renderEquation) {
    let resolve;
    try {
      resolve = require.resolve("mathjax-full/js/mathjax.js");
    } catch (cause) {
      throw new Error("mathjax-full is not installed. Run `npm ci` in pptxgenjs_helpers before using latexToSvgDataUri().", { cause });
    }
    // MathJax's documented synchronous component API keeps this helper synchronous.
    const mj = require(resolve).mathjax;
    const adapter = require("mathjax-full/js/adaptors/liteAdaptor.js").liteAdaptor();
    require("mathjax-full/js/handlers/html.js").RegisterHTMLHandler(adapter);
    const tex = require("mathjax-full/js/input/tex.js");
    const output = require("mathjax-full/js/output/svg.js");
    const packages = require("mathjax-full/js/input/tex/AllPackages.js").AllPackages;
    const document = mj.document("", {
      InputJax: new tex.TeX({ packages }),
      OutputJax: new output.SVG({ fontCache: "local" }),
    });
    renderEquation = (value, block) => adapter.outerHTML(document.convert(value, { display: block }));
  }
  return svgToDataUri(renderEquation(source, display));
};
