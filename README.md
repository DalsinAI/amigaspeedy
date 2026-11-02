# Speedy the Rollerskater for AmigaOS 3

Reproducible content-port tooling for running **Speedy the Rollerskater** with
the shared [Amiga OpenSurge](https://github.com/DalsinAI/amigaopensurge)
engine. This repository deliberately does not fork OpenSurge, Allegro, SDL, or
OpenGPU.

## Upstream

- Showcase and download: <https://sonicfangameshq.com/forums/showcase/speedy-the-rollerskater.977/>
- Expected archive SHA-256: `e63bb212793305edef648314ea2ff4686cd249fda33787f045b5b475ecde0673`
- Expected extracted directory: `Speedy the RollerSkater Full Version`
- Original engine: OpenSurge 0.5.2.1 / Allegro 5.2.7

The upstream author explicitly describes the game as free and open source and
asks users to give credit. The original package contains the OpenSurge GPLv3
engine source. Game art, music, names, and trademarks remain attributable to
their respective creators and owners.

## Prepare a port

Install the QPAK-enabled shared Amiga OpenSurge engine at
`DH1:OpenSurgeRC1`, extract the upstream archive, then run:

```sh
./scripts/prepare-amiga-port.sh \
  "/path/to/Speedy the RollerSkater Full Version" \
  ./dist/Speedy
```

The script copies only platform-neutral game content, excludes Windows runtime
files, adds the missing modern metadata, and writes an AmigaDOS `StartGame`
launcher. The launcher calls the shared engine with `--game`, enabling
OpenSurge's built-in 0.5.x compatibility pack. Run it with
`Execute DH1:Speedy/StartGame`.

## Status

See [PORT_STATUS.md](PORT_STATUS.md). The repository contains only original
port automation and metadata; it does not vendor the game archive or engine.

