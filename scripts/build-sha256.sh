#!/bin/sh
# Build port/sha256/SHA256, the small AmigaOS 3 command the Installer runs to
# check a download's SHA-256, from port/sha256/sha256.c with the
# os32-gcc16-open6 stove. The binary is committed beside its source so that
# packaging needs no stove; this script remakes it and says whether it changed.
#
#   scripts/build-sha256.sh [STOVE]      (default ~/AmiCradle/stoves/os32-gcc16-open6)
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
stove=${1:-$HOME/AmiCradle/stoves/os32-gcc16-open6}
cc=$stove/prefix/bin/m68k-amigaos-gcc
[ -x "$cc" ] || { echo "no compiler at $cc" >&2; exit 1; }
out=$root/port/sha256/SHA256
tmp=$(mktemp "${TMPDIR:-/tmp}/SHA256.XXXXXX")
trap 'rm -f "$tmp"' EXIT HUP INT TERM
"$cc" -O2 -m68020 -noixemul -s -Wall -Wextra -Werror -o "$tmp" "$root/port/sha256/sha256.c"
if [ -f "$out" ] && cmp -s "$tmp" "$out"; then
    echo "port/sha256/SHA256 is unchanged ($(sha256sum < "$out" | cut -d' ' -f1))"
else
    cp "$tmp" "$out"
    echo "port/sha256/SHA256 written: $(wc -c < "$out" | tr -d ' ') bytes, $(sha256sum < "$out" | cut -d' ' -f1)"
fi
