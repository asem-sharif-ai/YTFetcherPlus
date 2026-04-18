#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$DIR/env/bin/activate" ]; then
    echo "[YTFetcherPlus] Error: Virtual Environment NOT Found. Run ./setup.sh First."
    exit 1
fi

cd $DIR
source "env/bin/activate"
exec python3 "App.py" "$@"