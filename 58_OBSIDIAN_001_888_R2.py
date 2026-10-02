#!/usr/bin/env python3
"""iPhone/iSH Obsidian batch 001. Read-only; output goes only to terminal.
No network, installations, file writes, moves, renames or deletions.
Presence of a vault is not proof that it is active in the iOS app.
"""
print("OBSIDIAN_001_R2: UCITAVANJE", flush=True)
import os
import json
import pathlib
import collections
import time
import re

P = pathlib.Path


def main():
    if os.geteuid() != 0 or "ish" not in os.uname().release.lower():
        raise SystemExit("STOP: nije potvrdjen iPhone iSH.")
    start = time.monotonic()
    errors, limits, vaults, visited = [], [], set(), set()

    def emit(key, value):
        print(key + "=" + json.dumps(value, ensure_ascii=False), flush=True)

    def safe(p):
        try:
            return p.exists() and p.resolve(strict=True) == p
        except OSError:
            return False

    def problem(e):
        errors.append(str(e))

    def check_time():
        if time.monotonic() - start > 60:
            raise TimeoutError("Vremensko ogranicenje: pregled je djelimican.")

    print("=== OBSIDIAN 888 | BATCH 001 R2 | SAMO CITANJE ===", flush=True)
    expected_mount = "/tmp/ISH_EXPORT_888.w75MRJ"
    mounted = False
    try:
        for line in P("/proc/mounts").read_text().splitlines():
            fields = line.split()
            if len(fields) >= 3:
                mount = re.sub(r"\\([0-7]{3})",
                               lambda m: chr(int(m.group(1), 8)), fields[1])
                if mount == expected_mount and "ios" in fields[2].lower():
                    mounted = True
    except OSError as e:
        raise SystemExit("STOP: mount tabela nije dostupna: " + str(e))
    if not mounted:
        raise SystemExit("STOP: prethodno potvrdjeni iOS prikljucak vise nije dostupan.")
    emit("IOS_MOUNT", expected_mount)
    roots = [P(expected_mount) / name for name in (
        "FREYA_HOME_888", "OBSIDIAN_TITAN_LIVE", "Moj mozak",
        "MAGNUS_CORE_VAULT_888_20260819T113157Z",
    )]

    try:
        for base in dict.fromkeys(roots):
            if not safe(base) or not base.is_dir():
                continue
            emit("DOSTUPNO", str(base))
            for directory, dirs, files in os.walk(
                    str(base), followlinks=False, onerror=problem):
                check_time()
                p = P(directory)
                if str(p) in visited:
                    dirs[:] = []
                    continue
                visited.add(str(p))
                if len(visited) > 3000:
                    raise TimeoutError("Dostignut limit pretrage foldera.")
                depth = len(p.relative_to(base).parts)
                if depth == 0:
                    emit("PODFOLDERI_PRVIH_40", sorted(dirs)[:40])
                if ".obsidian" in dirs and safe(p / ".obsidian"):
                    vaults.add(p)
                    emit("VAULT_PRONADJEN", str(p))
                    dirs[:] = []
                    continue
                if depth >= 3:
                    if dirs:
                        limits.append("Dubina pretrage: " + str(p))
                    dirs[:] = []
                else:
                    dirs[:] = [d for d in dirs if not d.startswith(".")
                               and d not in ("node_modules", "__pycache__")
                               and safe(p / d)]
    except TimeoutError as e:
        limits.append(str(e))

    emit("PRONADJENI_VAULTOVI", len(vaults))
    emit("POTVRDA_AKTIVNOG_VAULTA_U_APLIKACIJI", "JOS_NIJE_DOSTUPNA")
    emit("PREGLED_IZOSTAVLJA", ".obsidian,.trash,.git,node_modules,simbolicke_veze")
    for vault in sorted(vaults)[:8]:
        emit("VAULT", str(vault))
        counts = collections.Counter()
        names = collections.defaultdict(list)
        top, empty = [], []
        complete = True
        initial_errors = len(errors)
        try:
            for directory, dirs, files in os.walk(
                    str(vault), followlinks=False, onerror=problem):
                check_time()
                parent = P(directory)
                dirs[:] = [d for d in dirs
                           if d not in (".obsidian", ".trash", ".Trash", ".git", "node_modules")
                           and safe(parent / d)]
                if parent == vault:
                    top = sorted(dirs)
                for name in files:
                    check_time()
                    p = parent / name
                    if not safe(p) or not p.is_file():
                        counts["preskoceno"] += 1
                        continue
                    try:
                        size = p.stat().st_size
                    except OSError as e:
                        problem(e)
                        continue
                    counts["fajlovi"] += 1
                    if counts["fajlovi"] % 250 == 0:
                        emit("PREGLEDANO_FAJLOVA", counts["fajlovi"])
                    counts["bajtovi"] += size
                    if p.suffix.lower() == ".md":
                        counts["biljeske"] += 1
                        rel = str(p.relative_to(vault))
                        names[p.stem.casefold()].append(rel)
                        if size == 0:
                            empty.append(rel)
                    if counts["fajlovi"] >= 20000:
                        raise TimeoutError("Limit fajlova za ovaj vault.")
        except TimeoutError as e:
            limits.append(str(vault) + ": " + str(e))
            complete = False
        complete = complete and len(errors) == initial_errors
        emit("PREGLED", "ZAVRSEN_OBILAZAK" if complete else "DJELIMICAN")
        emit("BROJEVI", dict(counts))
        emit("GLAVNI_FOLDERI_PRVIH_30", top[:30])
        emit("PRAZNE_BILJESKE", len(empty))
        emit("PRAZNE_PRIMJERI", empty[:10])
        collisions = [v for v in names.values() if len(v) > 1]
        emit("GRUPE_ISTIH_IMENA", len(collisions))
        emit("ISTA_IMENA_NISU_DOKAZ_DUPLIKATA", True)
        emit("PRIMJERI_ISTIH_IMENA", [v[:10] for v in collisions[:5]])
        home = [rel for group in names.values() for rel in group
                if any(w in P(rel).stem.casefold()
                       for w in ("pocet", "počet", "home", "dashboard", "pocak"))]
        emit("POCETNE_STRANICE_PRVIH_20", home[:20])
        for filename in ("app.json", "appearance.json", "core-plugins.json",
                         "community-plugins.json", "daily-notes.json", "templates.json"):
            p = vault / ".obsidian" / filename
            if not safe(p) or not p.is_file():
                emit(filename, "NIJE_DOSTUPAN")
                continue
            try:
                check_time()
                with p.open("rb") as f:
                    raw = f.read(262145)
                if len(raw) > 262144:
                    limits.append(str(p) + ": prevelik za ovaj pregled")
                    emit(filename, "PRESKOCEN_ZBOG_VELICINE")
                    continue
                data = json.loads(raw.decode("utf-8-sig"))
                if isinstance(data, dict):
                    allowed = {
                        "theme", "cssTheme", "baseFontSize", "enabledCssSnippets",
                        "readableLineLength", "showLineNumber", "spellcheck",
                        "newFileLocation", "newFileFolderPath", "attachmentFolderPath",
                        "alwaysUpdateLinks", "useMarkdownLinks", "defaultViewMode",
                        "livePreview", "folder", "format", "template",
                    }
                    if filename == "core-plugins.json":
                        data = {k: v for k, v in data.items() if isinstance(v, bool)}
                    else:
                        data = {k: v for k, v in data.items() if k in allowed}
                if not isinstance(data, (dict, list)):
                    errors.append(filename + ": neocekivan JSON tip")
                    emit(filename, "NEOCEKIVAN_JSON_TIP")
                else:
                    emit(filename, data)
            except (OSError, ValueError, UnicodeError, TimeoutError) as e:
                errors.append(filename + ": " + str(e))
                emit(filename, "NEUSPJESNO_CITANJE")

    if len(vaults) > 8:
        limits.append("Prikazano prvih 8 vaultova.")
    emit("GRESKE", len(errors))
    for item in errors[:10]:
        emit("GRESKA", item)
    emit("OGRANICENJA", len(limits))
    for item in limits[:10]:
        emit("OGRANICENJE", item)
    emit("IZMJENE", 0)
    emit("REZULTAT", "VAULT_NIJE_PRONADJEN_U_PREGLEDANIM_PUTANJAMA" if not vaults
         else "PREGLED_SA_OGRANICENJIMA" if errors or limits else "PREGLED_ZAVRSEN")


if __name__ == "__main__":
    main()
