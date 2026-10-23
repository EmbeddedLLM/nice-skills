// Print a PDF's AcroForm fields, one "<name>\t<type>" line each (pdf-lib).
//
//   node extract_form_fields.mjs <input.pdf>
//   node extract_form_fields.mjs --input in.pdf
import { readFileSync } from 'node:fs';
import { PDFDocument } from 'pdf-lib';

const USAGE = [
  'Usage (positional): node extract_form_fields.mjs <input.pdf>',
  'Usage (flags):      node extract_form_fields.mjs --input in.pdf',
];

const takeInput = (argv) => {
  const standalone = [];
  let flagged;
  argv.slice(2).forEach((arg, i, all) => {
    if (arg === '--help' || arg === '-h') {
      console.error(USAGE.join('\n'));
      process.exit(2);
    } else if (arg === '--input' || arg === '-i') {
      flagged = all[i + 1];
    } else if (!arg.startsWith('-')) {
      standalone.push(arg);
    }
  });
  return flagged ?? standalone[0];
};

const target = takeInput(process.argv);
if (!target) {
  console.error(USAGE.join('\n'));
  process.exit(2);
}

const pdf = await PDFDocument.load(readFileSync(target));
let form;
try {
  form = pdf.getForm();
} catch {
  console.log('No AcroForm found.');
  process.exit(0);
}

const found = form.getFields();
if (found.length === 0) {
  console.log('No form fields found.');
} else {
  for (const field of found) {
    const kind = field.constructor?.name || 'Field';
    console.log(`${field.getName()}\t${kind}`);
  }
}
