// Apply a validated JSON mapping to AcroForm fields; flatten only on request.
import { readFile, writeFile } from 'node:fs/promises';
import { parseArgs } from 'node:util';
import * as pdf from 'pdf-lib';

const { values: cli, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    input: { type: 'string', short: 'i' },
    values: { type: 'string', short: 'v' },
    fields: { type: 'string' },
    output: { type: 'string', short: 'o' },
    flatten: { type: 'boolean', default: false },
    help: { type: 'boolean', short: 'h' },
  },
});
const source = cli.input ?? positionals[0];
const mapping = cli.values ?? cli.fields ?? positionals[1];
const destination = cli.output ?? positionals[2];
if (cli.help || !source || !mapping || !destination) {
  console.error('Usage (positional): node fill_form.mjs input.pdf values.json output.pdf [--flatten]');
  console.error('Usage (flags): --input, --values (or --fields), --output');
  process.exit(2);
}
const requested = JSON.parse(await readFile(mapping, 'utf8'));
if (requested === null || Array.isArray(requested) || typeof requested !== 'object') {
  throw new Error('Values must be a JSON object mapping field names to values');
}
const document = await pdf.PDFDocument.load(await readFile(source));
const form = document.getForm();
const pending = [];
const rejected = [];

// No serialization happens until all fields have been checked and applied.
for (const name of Object.keys(requested)) {
  const value = requested[name];
  try {
    const field = form.getField(name);
    let apply;
    if (field instanceof pdf.PDFTextField) {
      if (typeof value !== 'string') throw Error('text value must be a string');
      const limit = field.getMaxLength();
      if (limit !== undefined && value.length > limit) throw Error(`text exceeds maximum length ${limit}`);
      apply = () => field.setText(value);
    } else if (field instanceof pdf.PDFCheckBox) {
      if (typeof value !== 'boolean') throw Error('checkbox value must be true or false');
      apply = () => field[value ? 'check' : 'uncheck']();
    } else {
      const choice = [pdf.PDFDropdown, pdf.PDFOptionList, pdf.PDFRadioGroup].some(Type => field instanceof Type);
      if (!choice) throw Error(`unsupported field type: ${field.constructor.name}`);
      if (typeof value !== 'string' || !field.getOptions().includes(value)) {
        throw Error(`value must match an available option: ${JSON.stringify(field.getOptions())}`);
      }
      apply = () => field.select(value);
    }
    pending.push(apply);
  } catch (error) {
    rejected.push(`${name}: ${error.message}`);
  }
}
if (rejected.length > 0) {
  throw Error('Form values rejected; no output written:\n' + rejected.join('\n'));
}
pending.forEach(apply => apply());
if (cli.flatten) form.flatten();
await writeFile(destination, await document.save());
console.log(`[OK] wrote ${destination}`);
