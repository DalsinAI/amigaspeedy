#!/usr/bin/env python3
"""Install-DRAWER and the Workbench icons, from port/installer.json and port/icons/icons.json.

    python3 tools/make_installer.py AMICRADLE [--date YYYY-MM-DD]

AMICRADLE is a checkout of DalsinAI/amicradle: its scripts/port_installer.py
writes the house Installer script (CPU, FPU and GFOpenGPU checks, the parent
drawer, copying the drawer) and scripts/port_icons.py the GlowIcons. The
results are committed in port/ so packaging needs no AmiCradle checkout.

When installer.json has a "data" section (a game whose own files may not be
redistributed), a step is added after the drawer is copied: it asks the
player for the archive or the folder they downloaded themselves, checks it
(the archive's size; the folder's name and the sizes of a few of its files),
and copies the game's files into DRAWER/Game, leaving out the Windows
program files. A zip archive is unpacked with AmiCradle's GFOpenCompress;
an archive the Amiga cannot unpack (RAR) is unpacked by the player first.
A game.zip made on another computer by scripts/prepare-amiga-port.sh is
taken as it is. With "patch_menu" the old MenuButtonList declaration is
brought up to OpenSurge 0.6.1 by Tools/PatchMenu.rexx (ARexx).

The download's SHA-256 can be checked on the Amiga too: the drawer carries
Tools/SHA256 (port/sha256, built by scripts/build-sha256.sh), and when it is
there the Installer asks (default yes) whether to check the archive before
it is unpacked. A player who gives an unpacked folder (always so for a RAR
archive) is asked whether they still have the archive: if so its SHA-256 is
checked, if not the folder is checked by the sizes of its files only.

A game whose data ships in the archive ("selfcheck": a file in the drawer
and the sha256sum list package-standalone.sh writes beside it) gets a check
of that file before anything is copied.
MIT, Copyright (c) 2026 AmiCradle Team.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = ROOT / "port"


def q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


CHECKER = "Tools/SHA256"


def sha_check(w, indent: str, name_var: str, label: str, page: str) -> None:
    """Lines that check #sha256 against the file in name_var with Tools/SHA256."""
    i = indent
    w(f"{i}(working {q('Checking the SHA-256 of ' + label + '. On a 68040 this takes a few minutes.')})")
    w(f"{i}(set #sha-rc (run (cat \"\\\"\" #checker \"\\\" \\\"\" {name_var} \"\\\" EXPECT=\" #sha256 \" >NIL:\") (safe)))")
    w(f"{i}(if (<> #sha-rc 0)")
    w(f"{i}    (abort (cat {name_var} {q(' is not the ' + label + ' this port was made for: its SHA-256 is not ')} #sha256 "
      f"{q('. It was damaged in the download or is another version. Download it again from ' + page)})))")
    w(f"{i}(message (cat {q('The SHA-256 of ')} {name_var} {q(' matches:')} \"\\n\\n\" #sha256))")


def ask_archive(w, indent: str, d: dict, me: str) -> None:
    """askfile for the archive, then its existence and size."""
    i, page = indent, d["page"]
    w(f"{i}(set #arc")
    w(f"{i}    (askfile")
    w(f"{i}        (prompt {q('Choose ' + d['archive'] + ', as you downloaded it.')})")
    w(f"{i}        (help @askfile-help)")
    w(f"{i}        (default \"RAM:\")))")
    w(f"{i}(if (<> (exists #arc (noreq)) 1)")
    w(f"{i}    (abort (cat {q('There is no file ')} #arc \".\")))")
    w(f"{i}(if (<> (getsize #arc) #archive-size)")
    w(f"{i}    (abort (cat #arc {q(' is ')} (getsize #arc) {q(' bytes, not the ' + str(d['archive_size']) + ' of ' + d['archive'] + '. Download it again from ' + page)})))")


def self_check(s: dict, c: dict) -> str:
    """Before anything is copied: a bundled file against the list packaged beside it."""
    name = s["name"]
    f, lst = c["file"], c["list"]
    o = []
    w = o.append
    w("; ---------------------------------------------------------------- the archive's own check")
    w(f"; package-standalone.sh writes {lst} (a sha256sum list) beside {f}: with")
    w(f"; {CHECKER} the Installer checks {f} before anything is copied")
    w(f"(set #checker (tackon #from {q(CHECKER)}))")
    w(f"(set #sumlist (tackon #from {q(lst)}))")
    w("(if (and (= (exists #checker (noreq)) 1) (= (exists #sumlist (noreq)) 1))")
    w("    (if")
    w("        (askbool")
    w(f"            (prompt {q('Check the SHA-256 of ' + f + ', ' + name + chr(39) + 's data in this archive, before it is installed?')})")
    w(f"            (help {q('The archive carries the SHA-256 of ' + f + ' in ' + lst + '. ' + CHECKER + ' reads ' + f + ' and compares, which finds an archive damaged in the download or while it was unpacked. On a 68040 it takes a minute or two. Skip it if the archive was checked already.')})")
    w("            (choices \"Check it\" \"Skip the check\")")
    w("            (default 1))")
    w("        (")
    w(f"            (working {q('Checking the SHA-256 of ' + f + '.')})")
    w("            (set #sha-rc (run (cat \"\\\"\" #checker \"\\\" CHECK=\\\"\" #sumlist \"\\\" >NIL:\") (safe)))")
    w("            (if (<> #sha-rc 0)")
    w(f"                (abort {q(f + ' in this archive is damaged: its SHA-256 is not the one in ' + lst + '. Download the archive again and unpack all of it. Nothing has been installed.')}))")
    w(f"            (message {q('The SHA-256 of ' + f + ' matches the one the archive was made with.')})")
    w("        )")
    w("    )")
    w(")")
    w("")
    return "\n".join(o) + "\n"


def data_step(s: dict, d: dict) -> str:
    name, drawer, me = s["name"], s["drawer"], s["script"]
    root, page = d["root"], d["page"]
    unzip = bool(d.get("unzip"))
    o = []
    w = o.append
    w("")
    w("; ---------------------------------------------------------------- the game's own files")
    w(f"; {name}'s own files are not in this archive: the player gives the Installer")
    w("; the archive or the folder they downloaded themselves, and the game drawer is")
    w("; built from it here, on this Amiga.")
    w(f"(set #root {q(root)})")
    w(f"(set #archive {q(d['archive'])})")
    w(f"(set #archive-size {d['archive_size']})")
    w(f"(set #game (tackon #dest \"Game\"))")
    w("(set #gamezip (tackon #dest \"game.zip\"))")
    w("(set #have (or (= (exists (tackon #game \"languages\") (noreq)) 2) (= (exists #gamezip (noreq)) 1)))")
    w(f"(set #sha256 {q(d['sha256'])})")
    w(f"; {CHECKER} (port/sha256 in the port's repository) checks the download's SHA-256")
    w(f"(set #checker (tackon #from {q(CHECKER)}))")
    w("(set #can-check (= (exists #checker (noreq)) 1))")
    intro = (f"{name}'s own files are not part of this archive and are not given out with it. "
             f"Download the game yourself from its page:\n\n{page}\n\n"
             f"The file there is called {d['archive']} ({d['archive_size']} bytes; SHA-256 {d['sha256']}).")
    if unzip:
        intro += "\n\nThe Installer checks its size, and can check its SHA-256 too."
    else:
        intro += ("\n\nIt is a RAR archive, which AmigaOS cannot unpack: unpack it first and give the "
                  "Installer the folder. The folder is checked by the sizes of some of its files; if you "
                  "still have the archive, the Installer can check its SHA-256 as well.")
    choices = []
    if unzip:
        choices.append(("archive", f"The archive I downloaded ({d['archive']})"))
    choices.append(("folder", f"The folder I unpacked it into (called {root})"))
    choices.append(("zip", "A game.zip made by prepare-amiga-port.sh"))
    choices.append(("skip", "Keep the game files already installed"))
    w(f"(message {q(intro)})")
    w(f"(set #how")
    w("    (askchoice")
    w(f"        (prompt {q('Where are ' + name + chr(39) + 's own files, from ' + d['archive'] + '?')})")
    howhelp = ("The Installer copies the game's files into the Game drawer inside "
               f"{drawer}, beside the OpenSurge engine that comes with this archive. ")
    if unzip:
        howhelp += ("The archive is unpacked with SYS:Utilities/GFOpenCompress. Without it, unpack the "
                    "archive with any unzip tool and choose the folder instead. ")
    else:
        howhelp += (f"The archive is a RAR archive, which AmigaOS cannot unpack by itself: unpack it "
                    f"with UnRAR (Aminet) or on another computer, copy the {root} folder to the Amiga, "
                    "and choose that folder. ")
    howhelp += ("prepare-amiga-port.sh (in the port's repository) makes a game.zip on another computer "
                "from the same download. Keep: leaves what an earlier run installed.")
    w(f"        (help {q(howhelp)})")
    w("        (choices " + " ".join(q(c[1]) for c in choices) + ")")
    keep_index = len(choices) - 1
    w(f"        (default (if #have {keep_index} 0))))")
    idx = {c[0]: i for i, c in enumerate(choices)}
    w(f"(if (and (= #how {keep_index}) (not #have))")
    w(f"    (abort (cat {q('No game files are installed yet, so there is nothing to keep. Run ' + me + ' again and choose your download. The engine is installed in ')} #dest \".\")))")
    w("(set #src \"\")")
    if unzip:
        w(f"(if (= #how {idx['archive']})")
        w("    (")
        ask_archive(w, "        ", d, me)
        w("        (if #can-check")
        w("            (if")
        w("                (askbool")
        w(f"                    (prompt {q('Check the SHA-256 of ' + d['archive'] + ' before it is unpacked?')})")
        w(f"                    (help {q('Its size is right. ' + CHECKER + ' (in this archive) reads the whole file and compares its SHA-256 with ' + d['sha256'] + ', the one of the download this port was made for. That finds a damaged download or another version of the game. On a 68040 it takes a few minutes. Skip it if you checked the file on another computer.')})")
        w("                    (choices \"Check it\" \"Skip the check\")")
        w("                    (default 1))")
        w("                (")
        sha_check(w, "                    ", "#arc", d["archive"], page)
        w("                )")
        w("            )")
        w("        )")
        w("        (if (<> (exists \"SYS:Utilities/GFOpenCompress\" (noreq)) 1)")
        w(f"            (abort {q('SYS:Utilities/GFOpenCompress, which unpacks the archive, is not on this Amiga. Unpack ' + d['archive'] + ' with an unzip tool, then run ' + me + ' again and choose the ' + root + ' folder.')}))")
        w("        (set #unpack (tackon #dest \"Unpack\"))")
        w("        (if (= (exists #unpack (noreq)) 2)")
        w("            (delete #unpack (all) (optional \"force\")))")
        w("        (makedir #unpack)")
        w(f"        (working {q('Unpacking ' + d['archive'] + '. This takes a few minutes.')})")
        w("        (run (cat \"SYS:Utilities/GFOpenCompress x \\\"\" #arc \"\\\" \\\"\" #unpack \"\\\" >NIL:\"))")
        w("        (set #src (tackon #unpack #root))")
        w("    )")
        w(")")
    w(f"(if (= #how {idx['folder']})")
    w("    (")
    w("        (set #src")
    w("            (askdir")
    w(f"                (prompt {q('Choose the folder called ' + root + ', unpacked from ' + d['archive'] + '.')})")
    w("                (help @askdir-help)")
    w("                (default \"RAM:\")))")
    w("        (if (and (<> (fileonly #src) #root) (= (exists (tackon #src #root) (noreq)) 2))")
    w("            (set #src (tackon #src #root)))")
    w("        (if (<> (fileonly #src) #root)")
    w(f"            (abort (cat #src {q(' is not the ' + root + ' folder. Choose the folder that unpacking ' + d['archive'] + ' made.')})))")
    folder_prompt = (f"The folder's files are checked by their sizes, which finds a folder that is incomplete "
                     f"or from another version. Do you still have {d['archive']}? If you do, the Installer "
                     "can check its SHA-256 as well.")
    folder_help = (f"{CHECKER} (in this archive) reads {d['archive']} and compares its SHA-256 with "
                   f"{d['sha256']}, the one of the download this port was made for. ")
    if not unzip:
        folder_help += ("The Amiga cannot unpack the RAR archive itself, so the game's files are always "
                        "copied from the folder; the archive is only checked. ")
    folder_help += ("If you no longer have the archive, choose Sizes only: the folder is then checked by "
                    "the sizes of a few of its files, not by a SHA-256.")
    w("        (if #can-check")
    w("            (if")
    w("                (askbool")
    w(f"                    (prompt {q(folder_prompt)})")
    w(f"                    (help {q(folder_help)})")
    w("                    (choices \"Check the archive\" \"Sizes only\")")
    w("                    (default 1))")
    w("                (")
    ask_archive(w, "                    ", d, me)
    sha_check(w, "                    ", "#arc", d["archive"], page)
    w("                )")
    w("            )")
    w("        )")
    w("    )")
    w(")")
    w(f"(if (<> #src \"\")")
    w("    (")
    for path, size in d["checks"]:
        w(f"        (if (<> (exists (tackon #src {q(path)}) (noreq)) 1)")
        w(f"            (abort (cat #src {q(' has no ' + path + '. It is not a complete copy of ' + d['archive'] + '; unpack it again.')})))")
        w(f"        (if (<> (getsize (tackon #src {q(path)})) {size})")
        w(f"            (abort (cat {q(path + ' in ')} #src {q(' is not the one in ' + d['archive'] + ' (' + str(size) + ' bytes). Download the game again from ' + page)})))")
    w("        (if (= (exists #gamezip (noreq)) 1)")
    w("            (delete #gamezip (optional \"force\")))")
    w("        (if (= (exists #game (noreq)) 2)")
    w("            (delete #game (all) (optional \"force\")))")
    w("        (copyfiles")
    w(f"            (prompt {q('Copying ' + name + chr(39) + 's files into the Game drawer')})")
    w("            (help @copyfiles-help)")
    w("            (source #src)")
    w("            (dest #game)")
    w(f"            (pattern {q('~(' + '|'.join(d['exclude']) + ')')})")
    w("            (optional \"force\"))")
    if d.get("surge_cfg"):
        w("        ; the game predates surge.cfg: add the port's (its title and screen size)")
        w("        (if (<> (exists (tackon #game \"surge.cfg\") (noreq)) 1)")
        w("            (copyfiles")
        w("                (help @copyfiles-help)")
        w("                (source (tackon #dest \"Tools/surge.cfg\"))")
        w("                (dest #game)")
        w("                (optional \"force\")))")
    if d.get("patch_menu"):
        w("        ; OpenSurge 0.6.1 asks for MenuButtonList to be declared an entity")
        w("        (if (<> @pretend 1)")
        w("            (")
        w("                (run \"SYS:System/RexxMast >NIL:\")")
        w("                (run \"SYS:Rexxc/WaitForPort REXX\")")
        w("                ; RX takes a quoted first word as a program's text, not its name: so")
        w("                ; the script is run from T:, whose name has no spaces in it")
        w("                (copyfiles (source (tackon #dest \"Tools/PatchMenu.rexx\")) (dest \"T:\") (optional \"force\"))")
        w("                (run (cat \"SYS:Rexxc/RX T:PatchMenu.rexx \\\"\" (tackon #game \"scripts/ui/menubuttonlist.ss\") \"\\\"\"))")
        w("                (delete \"T:PatchMenu.rexx\" (optional \"force\"))")
        w("            )")
        w("        )")
    if unzip:
        w("        (if (= (exists (tackon #dest \"Unpack\") (noreq)) 2)")
        w("            (delete (tackon #dest \"Unpack\") (all) (optional \"force\")))")
    w("    )")
    w(")")
    w(f"(if (= #how {idx['zip']})")
    w("    (")
    w("        (set #zip")
    w("            (askfile")
    w(f"                (prompt {q('Choose the game.zip that prepare-amiga-port.sh made from ' + d['archive'] + '.')})")
    w("                (help @askfile-help)")
    w("                (default \"RAM:\")))")
    w("        (if (<> (exists #zip (noreq)) 1)")
    w(f"            (abort (cat {q('There is no file ')} #zip \".\")))")
    w("        (if (= (exists #game (noreq)) 2)")
    w("            (delete #game (all) (optional \"force\")))")
    w("        (copyfiles")
    w("            (help @copyfiles-help)")
    w("            (source #zip)")
    w("            (dest #dest)")
    w("            (newname \"game.zip\")")
    w("            (optional \"force\"))")
    w("    )")
    w(")")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("amicradle", type=Path)
    ap.add_argument("--date")
    args = ap.parse_args()
    sys.path.insert(0, str(args.amicradle / "scripts"))
    import port_icons
    import port_installer

    today = datetime.date.fromisoformat(args.date) if args.date else None
    spec_path = PORT / "installer.json"
    raw = json.loads(spec_path.read_text(encoding="utf-8"))
    s = port_installer.load(spec_path)
    text = port_installer.script(s, today)
    data = raw.get("data")
    if data:
        anchor = "(set @default-dest #dest)\n"
        if anchor not in text:
            raise SystemExit("port_installer's script has changed: no (set @default-dest #dest)")
        text = text.replace(anchor, data_step(s, data) + "\n" + anchor, 1)
    selfcheck = raw.get("selfcheck")
    if selfcheck:
        anchor = "; where: the parent drawer\n"
        if anchor not in text:
            raise SystemExit("port_installer's script has changed: no '; where: the parent drawer'")
        text = text.replace(anchor, self_check(s, selfcheck) + anchor, 1)
    (PORT / s["script"]).write_bytes(text.encode("latin-1"))
    icons = PORT / "icons"
    out = port_installer.icon(s, spec_path.parent, icons)
    if data:      # the data step asks questions, so a Novice must still be asked
        meta = port_installer.port_icons.amiga_icon.read_icon(out.read_bytes())
        types = [t.replace("MINUSER=NOVICE", "MINUSER=AVERAGE") for t in meta["toolTypes"]]
        art = port_icons.Picture.load(spec_path.parent / s["badge"])
        m = {"type": port_icons.TYPES["project"], "defaultTool": s["installer"], "toolTypes": types,
             "toolWindow": None, "stack": port_installer.STACK, "x": port_icons.amiga_icon.NO_POSITION,
             "y": port_icons.amiga_icon.NO_POSITION, "drawer": None}
        port_icons._write(out, m, port_icons.frames("installer", art))
    for p in [PORT / s["script"], out] + port_icons.build(icons / "icons.json", icons):
        print(f"{p.relative_to(ROOT)}: {p.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
