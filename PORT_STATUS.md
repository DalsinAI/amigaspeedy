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

## Standalone RC2 (6 November 2026): SHA-256 check in the Installer

- [x] Tools/SHA256 (port/sha256, built by scripts/build-sha256.sh with os32-gcc16-open6; 6612 bytes, same bytes on every build) in the drawer, Licences/SHA256.txt beside the other licences
- [x] Lab t4-opensurge: Tools/SHA256 gives OK/0 for the right hash, FAILED/10 for a wrong one, 20 for a missing file; inside an Installer script `(run ... (safe))` returns those codes
- [x] All three downloads (AS2R zip, Aishi & Reimu zip, Sonic The Last Hope.rar) check OK on the Amiga, 18-25 s each in the lab
- [x] Installer texts kept under 512 characters per literal: Installer 47.19 refused Install-SonicTLH's longer first message ("Symbol or String too long")
- [x] Install-Speedy run by hand from its icon (every requester clicked, no pre-answered copy): Intermediate user, "Check the SHA-256 of game.zip ...?" -> Check it, "The SHA-256 of game.zip matches the one the archive was made with", Work:Games accepted, drawer copied, "Speedy the Rollerskater standalone-rc2 is installed in Work:Games/Speedy". `Tools/SHA256 CHECK=game.zip.sha256` on the installed copy: game.zip OK
- [x] StartGame in the installed drawer (Shell: CD Work:Games/Speedy, Execute StartGame): title, main menu, PLAY, the opening cutscene and how-to-play, then the first level (levels/beach1.lev) playing: Speedy on the beach, HUD timer running, moved right and jumped; Esc brought up "Do you really want to quit?", No, then back to the title and the window's close gadget: logfile ends "tchau!", engine process gone
- [ ] The StartGame icon did not start the game from the lab's Workbench (GFOpenBench preview): its default tool C:IconX is not a file in this lab's C: (IconX is only resident there); CREDITS opened from its icon. Starting from a Shell works. Not changed in this rc
- Host load during the test: load average 80-118 on 12 cores (no quieter moment came in 30 minutes of waiting); the game was still responsive enough to play the first level
