#!/bin/sh
# Build the standalone AmigaOS 3 release archive: the game's drawer with the
# Amiga OpenSurge engine inside it, its GlowIcons, the Installer script, the
# ReadMe, credits and licences, as one LhA.
#
#   scripts/package-standalone.sh [-e ENGINE.tar.gz] [-g GAME_DIR] OUTPUT_DIR
#
# -e  the engine release asset named in port/engine.env (downloaded from the
#     engine's release when not given); its SHA-256 is checked either way.
# -g  the extracted upstream game folder. Only for a game whose data may be
#     shipped (BUNDLE_DATA=yes in port/manifest.env); it becomes game.zip
#     through scripts/prepare-amiga-port.sh. For the other games no game file
#     goes into the archive: the Installer builds the game from the player's
#     own download on the Amiga.
#
# Every file is stamped with the commit time of HEAD and the archive members
# are written in a fixed order, so the same inputs make the same bytes.
# KEEP_STAGE=DIR also keeps the unpacked drawer there (for a lab).
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
. "$root/port/manifest.env"
. "$root/port/engine.env"

usage="usage: $0 [-e ENGINE.tar.gz] [-g GAME_DIR] OUTPUT_DIR"
engine_tar=
game_dir=
while getopts e:g: opt; do
    case $opt in
        e) engine_tar=$OPTARG ;;
        g) game_dir=$OPTARG ;;
        *) echo "$usage" >&2; exit 2 ;;
    esac
done
shift $((OPTIND - 1))
[ "$#" -eq 1 ] || { echo "$usage" >&2; exit 2; }
output_dir=$(realpath -m "$1")

if [ "$BUNDLE_DATA" = yes ]; then
    [ -n "$game_dir" ] || { echo "$GAME_TITLE ships its data: give the extracted game folder with -g" >&2; exit 2; }
    [ -d "$game_dir" ] || { echo "game directory not found: $game_dir" >&2; exit 1; }
    game_dir=$(realpath "$game_dir")
elif [ -n "$game_dir" ]; then
    echo "$GAME_TITLE's data may not be redistributed: -g is refused" >&2
    exit 2
fi
for tool in python3 sha256sum tar git; do
    command -v "$tool" >/dev/null 2>&1 || { echo "$tool is required" >&2; exit 1; }
done

work=$(mktemp -d "${TMPDIR:-/tmp}/standalone-$GAME_SLUG.XXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM

# --- the engine
if [ -z "$engine_tar" ]; then
    engine_tar="$work/$ENGINE_ASSET"
    if command -v gh >/dev/null 2>&1; then
        gh release download "$ENGINE_TAG" -R "$ENGINE_REPO" -p "$ENGINE_ASSET" -D "$work"
    else
        curl -fsSL -o "$engine_tar" "https://github.com/$ENGINE_REPO/releases/download/$ENGINE_TAG/$ENGINE_ASSET"
    fi
fi
echo "$ENGINE_SHA256  $engine_tar" | sha256sum -c --quiet - ||
    { echo "$engine_tar is not $ENGINE_ASSET ($ENGINE_SHA256)" >&2; exit 1; }
mkdir "$work/engine"
tar -C "$work/engine" -xzf "$engine_tar"
echo "$ENGINE_BINARY_SHA256  $work/engine/dist/opensurge" | sha256sum -c --quiet - ||
    { echo "dist/opensurge in $ENGINE_ASSET is not the expected build" >&2; exit 1; }

# --- the drawer
fill() {
    sed -e "s|@ENGINE_TAG@|$ENGINE_TAG|g" -e "s|@ENGINE_COMMIT@|$ENGINE_COMMIT|g" \
        -e "s|@ENGINE_SHA256@|$ENGINE_SHA256|g" -e "s|@ENGINE_BINARY_SHA256@|$ENGINE_BINARY_SHA256|g" \
        -e "s|@ENGINE_ASSET@|$ENGINE_ASSET|g" -e "s|@ENGINE_REPO@|$ENGINE_REPO|g" \
        -e "s|@ENGINE_COMPILER@|$ENGINE_COMPILER|g" -e "s|@ALLEGRO_COMMIT@|$ENGINE_ALLEGRO_COMMIT|g" \
        -e "s|@RELEASE_VERSION@|$RELEASE_VERSION|g" -e "s|@PORT_COMMIT@|$port_commit|g" "$1" > "$2"
    if grep -q '@[A-Z_]*@' "$2"; then
        echo "a field is left unfilled in $2" >&2
        exit 1
    fi
}
port_commit=$(cd "$root" && git rev-parse HEAD)
stage="$work/stage"
drawer="$stage/$DRAWER"
mkdir -p "$drawer/Licences"
cp -R "$work/engine/dist" "$drawer/Engine"
cp "$root/port/StartGame" "$drawer/StartGame"
cp "$root/port/icons/StartGame.info" "$root/port/icons/ReadMe.info" "$drawer/"
cp "$root/port/icons/$DRAWER.info" "$stage/"
cp "$root/port/Install-$DRAWER" "$root/port/icons/Install-$DRAWER.info" "$stage/"
fill "$root/port/ReadMe.in" "$drawer/ReadMe"
fill "$root/port/SOURCE.txt" "$drawer/Licences/SOURCE.txt"
cp "$work/engine/dist/LICENSE" "$drawer/Licences/GPL-3.0.txt"
cp "$root/LICENSE" "$drawer/Licences/Port-scripts-MIT.txt"

if [ "$BUNDLE_DATA" = yes ]; then
    (cd "$root" && SOURCE_DATE_EPOCH=$(git log -1 --format=%ct HEAD) \
        ./scripts/prepare-amiga-port.sh "$game_dir" "$work/prepared" >/dev/null)
    mv "$work/prepared/game.zip" "$drawer/game.zip"
    cp "$root/CREDITS" "$drawer/CREDITS"
    cp "$root/port/icons/CREDITS.info" "$drawer/"
    for f in $GAME_CREDIT_FILES; do
        cp "$game_dir/$f" "$drawer/Licences/$GAME_SLUG-$f"
    done
else
    mkdir -p "$drawer/Tools"
    if [ "${PATCH_MENUBUTTONLIST:-no}" = yes ]; then
        cp "$root/port/PatchMenu.rexx" "$drawer/Tools/PatchMenu.rexx"
    fi
    if [ -f "$root/port/surge.cfg" ]; then
        cp "$root/port/surge.cfg" "$drawer/Tools/surge.cfg"
    fi
fi

# --- the archive
epoch=$(cd "$root" && git log -1 --format=%ct HEAD)
find "$stage" -exec touch -h -d "@$epoch" {} +
mkdir -p "$output_dir"
archive="$DRAWER-AmigaOS3-$RELEASE_VERSION.lha"
python3 "$root/tools/make_lha.py" "$stage" "$output_dir/$archive" "$epoch"
(cd "$stage" && find . -type f | LC_ALL=C sort | sed 's|^\./||' |
    while IFS= read -r f; do
        printf '%s  %s  %s\n' "$(sha256sum < "$f" | cut -d' ' -f1)" "$(wc -c < "$f" | tr -d ' ')" "$f"
    done) > "$output_dir/$archive.contents.txt"
if [ -n "${KEEP_STAGE:-}" ]; then
    rm -rf "$KEEP_STAGE"
    cp -a "$stage" "$KEEP_STAGE"
    echo "Unpacked drawer kept in $KEEP_STAGE"
fi
echo "Engine inside: $ENGINE_REPO $ENGINE_TAG ($ENGINE_COMMIT)"
