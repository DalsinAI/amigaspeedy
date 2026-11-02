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

