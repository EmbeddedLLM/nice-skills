#!/usr/bin/env bash
# Fetch the JS helpers' npm dependencies (pdf-lib, pdfjs-dist) into this
# directory. Requires network access.
set -euo pipefail
cd -- "$(dirname -- "$0")"

command -v npm >/dev/null 2>&1 || {
  printf '[FAIL] npm is unavailable\n' >&2
  exit 1
}

if [ -d node_modules ]; then
  printf '[OK] dependencies already present (node_modules exists)\n'
  exit 0
fi

printf '[INFO] npm ci: locked pdf-lib + pdfjs-dist\n'
npm ci --silent
printf '[OK] JS dependencies ready\n'
