#!/bin/sh
set -eu
BENCH_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec node "$BENCH_ROOT/bin/webgames-server.mjs"
