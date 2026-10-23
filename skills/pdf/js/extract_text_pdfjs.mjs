// Emit each page's PDF.js text items as a line followed by a blank line.
// Local input only; reading order is the order supplied by PDF.js.
import { readFile } from 'node:fs/promises';
import { getDocument } from 'pdfjs-dist/legacy/build/pdf.mjs';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { input: { type: 'string', short: 'i' }, help: { type: 'boolean', short: 'h' } },
});
const filename = values.input ?? positionals[0];
if (values.help || !filename) {
  console.error('Usage: node extract_text_pdfjs.mjs [--input] input.pdf');
  process.exit(2);
}
const loading = getDocument({
  data: new Uint8Array(await readFile(filename)),
  standardFontDataUrl: fileURLToPath(new URL('./node_modules/pdfjs-dist/standard_fonts/', import.meta.url)),
});
try {
  const document = await loading.promise;
  for (let number = 1; number <= document.numPages; number += 1) {
    const page = await document.getPage(number);
    const { items } = await page.getTextContent();
    process.stdout.write(items.map(({ str }) => str ?? '').join(' ') + '\n\n');
    page.cleanup();
  }
} finally {
  await loading.destroy();
}
