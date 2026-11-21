#!/bin/sh
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    echo "CampusConnect needs Python 3.11 or newer on macOS/Linux."
    echo "See README.md in this folder for the manual launch command."
    if [ -t 0 ]; then printf 'Press Return to close. '; read -r answer; fi
    exit 1
fi
exec python3 -X utf8 src/start.py "$@"
