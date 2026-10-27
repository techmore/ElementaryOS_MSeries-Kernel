#!/usr/bin/env bash
# Kernel-side checks moved from the hub's mseries/validate.sh (no hardware, no network).
set -uo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
fail=0
run() { echo "== $*"; "$@" >/dev/null 2>&1 && echo ok || { echo FAIL; fail=1; }; }
run python3 -m unittest discover -s aurora -p 'test_*.py'
run python3 -m unittest discover -s aurora-sep -p 'test_touchid*.py'
run python3 -m unittest discover -s qualification -p 'test_*.py'
run python3 tools/test-kernel-config.py
for f in fairydust/usb4/test-*.py fairydust/debian/test-*.py fairydust/usb4/tools/test-staging-tools.py; do run python3 "$f"; done
run python3 aurora/check_freezes.py
run bash -n fairydust/debian/build.sh fairydust/debian/fetch-asahi-boot-packages.sh aurora-sep/install-aurora-sep.sh
exit $fail
