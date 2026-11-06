#!/bin/sh
# The shared-engine route: game.zip and a StartGame for an engine installed
# at DH1:OpenSurgeRC1. scripts/package-standalone.sh uses the same game.zip.
set -eu

if [ "$#" -ne 2 ]; then
    echo "usage: $0 EXTRACTED_GAME_DIR OUTPUT_DIR" >&2
    exit 2
fi

game_dir=$1
output_dir=$(realpath -m "$2")
[ -d "$game_dir" ] || { echo "game directory not found: $game_dir" >&2; exit 1; }
[ ! -e "$output_dir" ] || { echo "output already exists: $output_dir" >&2; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "zip is required" >&2; exit 1; }

staging_dir=$(mktemp -d "${TMPDIR:-/tmp}/amigaspeedy.XXXXXX")
trap 'rm -rf "$staging_dir"' EXIT HUP INT TERM

tar -C "$game_dir" \
    --exclude='*.exe' --exclude='*.dll' \
    --exclude='logfile.txt' --exclude='allegro.log' --exclude='surge.prefs' \
    --exclude='./src' --exclude='./screenshots' --exclude='./boxarts' \
    --exclude='./CMakeLists.txt' --exclude='./CHANGES.md' \
    --exclude='./CONTRIBUTING.md' --exclude='./README.md' \
    -cf - . | tar -C "$staging_dir" -xf -
sed -i 's/^object "MenuButtonList"\r*$/object "MenuButtonList" is "private", "awake", "entity"/' "$staging_dir/scripts/ui/menubuttonlist.ss"
if [ ! -f "$staging_dir/surge.cfg" ]; then
    cp port/surge.cfg "$staging_dir/surge.cfg"
fi

mkdir -p "$output_dir"
# A fixed order and fixed dates (SOURCE_DATE_EPOCH, else the newest file's)
# make the same game.zip from the same download.
epoch=${SOURCE_DATE_EPOCH:-$(find "$staging_dir" -type f -printf '%T@\n' | sort -n | tail -1 | cut -d. -f1)}
find "$staging_dir" -exec touch -h -d "@$epoch" {} +
(cd "$staging_dir" && find . -mindepth 1 | LC_ALL=C sort | TZ=UTC zip -X -0 -q -@ "$output_dir/game.zip")
cp port/StartGame.shared "$output_dir/StartGame"
chmod +x "$output_dir/StartGame"
cp README.md "$output_dir/AMIGA-PORT.md"

echo "Prepared stored PhysFS archive: $output_dir/game.zip"
echo "Launch with: Execute $output_dir/StartGame"
