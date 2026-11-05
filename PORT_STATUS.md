# Port status

- [x] Upstream package acquired and checksum recorded
- [x] Complete OpenSurge game data and bundled engine source confirmed
- [x] Reproducible content-port script added
- [x] Boot tested on Cradle AmigaOS 3 target
- [x] Title screen tested
- [ ] First playable level tested
- [x] Local stored-ZIP release candidate built

Compatibility target: the shared Amiga OpenSurge 0.6.1.3 RC engine. The game
was authored against OpenSurge 0.5.2.1, so any compatibility changes belong in
the shared engine or a small documented content patch, not a private engine
fork.

Cradle test (2026-11-02): title, menu, story and tutorial render correctly;
the first level reached its asset-loading phase but was not yet confirmed
playable. Packaging applies the current `MenuButtonList` entity tags required
by OpenSurge 0.6.1.3. The 213 MiB stored `game.zip` contains 1,074 files and a
fixed-path launcher for the shared engine.

## Standalone RC1 (5 November 2026)

- [x] Standalone LhA with the rc3 engine inside (`scripts/package-standalone.sh`)
- [x] Game data bundled (author's free and open source terms, credit in CREDITS)
- [x] Lab t4-opensurge (5 Nov): drawer unpacked from the LhA into SYS:Games, StartGame run from the drawer with the bundled engine: title screen, main menu, intro story and how-to-play screens
- [x] Clean quit from the game's own menu (logfile ends "tchau!", engine process gone)
- [ ] First level not reached in the lab: the how-to-play scene went on loading for more than a minute and the run was ended there (see notes)
- [ ] Install-Speedy not run in the lab (same script as the other three, without the game-data step)

Lab notes (5 November 2026): the engine finds game.zip beside it and keeps its settings, logfile and compatibility pack in Engine/.userdata/game. The lab host was very loaded (load average 40-70) and its window capture failed at times, so the first level was not reached in the time given; the shared-engine route reached the level's asset loading on 2 November. The LhA is 267 MB because game.zip and the archive are stored, not compressed.
