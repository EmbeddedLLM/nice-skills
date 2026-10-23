#!/usr/bin/env python3
"""Validate a packed or unpacked Office document (read-only by default).

XSD coverage is selective;
--original suppresses inherited schema errors, not relationship failures.
"""
import argparse
from contextlib import ExitStack
from pathlib import Path
import sys
import tempfile
import zipfile

# Allow direct script invocation as well as python -m office.validate.
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from office.helpers import safe_extract, rezip

FAMILY = 'docx'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--original', type=Path)
    parser.add_argument('--author', help='Enable body-text redline validation against --original (DOCX only)')
    parser.add_argument('--auto-repair', action='store_true', help='Repair IDs/whitespace; requires a new --output file')
    parser.add_argument('--output', type=Path)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    if args.author is not None and (FAMILY != 'docx' or args.original is None):
        parser.error('--author requires DOCX and --original')
    if args.auto_repair != (args.output is not None):
        parser.error('--auto-repair and --output must be used together')
    try:
        extensions = ('.docx', '.dotx') if FAMILY == 'docx' else ('.pptx', '.potx')
        if args.original and (not args.original.is_file() or args.original.suffix.lower() not in extensions):
            raise ValueError('--original must be a file of the same document family')
        if args.output and (args.output.exists() or args.output.is_symlink() or args.output.suffix.lower() not in extensions):
            raise ValueError('Choose a new output path of the same document family')
        with ExitStack() as stack:
            work = args.path
            if args.path.is_file():
                if args.path.suffix.lower() not in extensions:
                    raise ValueError(f'Expected one of {extensions}')
                work = Path(stack.enter_context(tempfile.TemporaryDirectory()))
                with zipfile.ZipFile(args.path) as archive:
                    safe_extract(archive, work)
            elif args.auto_repair:
                raise ValueError('Repair requires a packed input; directory validation is read-only')
            required = 'word/document.xml' if FAMILY == 'docx' else 'ppt/presentation.xml'
            if not (work/required).is_file() or not (work/'[Content_Types].xml').is_file():
                raise ValueError(f'Package lacks {required} or [Content_Types].xml')
            if any(p.is_symlink() for p in work.rglob('*')):
                raise ValueError('Unpacked inputs must not contain symlinks')
            if FAMILY == 'docx':
                from office.validators.docx import DOCXSchemaValidator
                from office.validators.redlining import RedliningValidator
                validators = [DOCXSchemaValidator(work, args.original, args.verbose)]
                if args.author is not None:
                    validators.append(RedliningValidator(work, args.original, args.verbose))
            else:
                from office.validators.pptx import PPTXSchemaValidator
                validators = [PPTXSchemaValidator(work, args.original, args.verbose)]
            if args.auto_repair:
                print(f'Repaired {sum(v.repair() for v in validators)} issue(s) in temporary copy')
            success = all([v.validate() for v in validators])
            if success and args.output:
                rezip(work, args.output)
            print('Validation PASSED (see documented coverage limits)' if success else 'Validation FAILED; no repaired output published')
            return 0 if success else 1
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
