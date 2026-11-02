#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
    echo "usage: $0 EXTRACTED_GAME_DIR AMIGA_OPENSURGE OUTPUT_DIR" >&2
    exit 2
fi

game_dir=$1
engine_bin=$2
output_dir=$3

[ -d "$game_dir" ] || { echo "game directory not found: $game_dir" >&2; exit 1; }
[ -f "$engine_bin" ] || { echo "engine not found: $engine_bin" >&2; exit 1; }
[ ! -e "$output_dir" ] || { echo "output already exists: $output_dir" >&2; exit 1; }

mkdir -p "$output_dir"
tar -C "$game_dir" \
    --exclude='*.exe' \
    --exclude='*.dll' \
    --exclude='logfile.txt' \
    --exclude='allegro.log' \
    --exclude='surge.prefs' \
    -cf - . | tar -C "$output_dir" -xf -
cp "$engine_bin" "$output_dir/opensurge"
chmod +x "$output_dir/opensurge"
cp README.md "$output_dir/AMIGA-PORT.md"

echo "Prepared $output_dir"
sha256sum "$output_dir/opensurge"

