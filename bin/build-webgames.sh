#!/bin/sh
set -eu
BENCH_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BENCH_ROOT/webgames"
npx --yes pnpm@9.15.9 install --frozen-lockfile
npx --yes pnpm@9.15.9 run build
