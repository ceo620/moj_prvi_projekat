#!/usr/bin/env python3
"""Read the mounted ARS vault; create one diagnostic ZIP outside it.
No vault writes, network, installations, deletion or source script execution.
Wiki-link findings are candidates, not proof of broken links.
"""
import os
import sys
import time
import json
import stat
import hashlib
import posixpath
import re
import zipfile
from pathlib import Path
from collections import defaultdict


def emit(key, value):
    print(key + "=" + str(value), flush=True)


def scan(root):
    started = time.monotonic()
    notes, inventory, excerpts, configs = {}, [], {}, {}
    issues, skipped = [], []
    total_read = 0
    excluded = {".obsidian", ".trash", ".Trash", ".git", "node_modules"}

    def check():
        if time.monotonic() - started > 90:
            raise RuntimeError("Limit 90 sekundi u pregledu; nalaz je djelimican.")

    def read(p, limit=1048576):
        nonlocal total_read
        check()
        if p.resolve(strict=True) != p:
            raise ValueError("Simbolicka veza nije dozvoljena")
        before = p.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError("Nije obican fajl ili prelazi limit citanja")
        if total_read + before.st_size > 33554432:
            raise RuntimeError("Limit ukupnog citanja 32 MiB")
        with p.open("rb") as f:
            data = f.read(limit + 1)
        total_read += len(data)
        after = p.stat()
        if len(data) > limit or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("Fajl se promijenio tokom citanja ili prelazi limit")
        return data

    def walk_error(e):
        issues.append(str(e))

    try:
        for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
            check()
            parent = Path(directory)
            dirs[:] = sorted(d for d in dirs if d not in excluded and not (parent / d).is_symlink())
            for name in sorted(files):
                check()
                p = parent / name
                rel = p.relative_to(root).as_posix()
                try:
                    s = p.lstat()
                    if not stat.S_ISREG(s.st_mode):
                        skipped.append(rel)
                        continue
                    row = {"path": rel, "bytes": s.st_size, "mtime_ns": s.st_mtime_ns}
                    inventory.append(row)
                    if len(inventory) > 10000:
                        raise RuntimeError("Limit 10000 fajlova")
                    if p.suffix.lower() != ".md":
                        continue
                    raw = read(p)
                    row["sha256"] = hashlib.sha256(raw).hexdigest()
                    text = raw.decode("utf-8-sig")
                    notes[rel] = text
                    if rel in ("00 Pocetna.md", "00_POCETAK_OPORAVKA_888.md") or p.parent == root / "RAD":
                        excerpts[rel] = {"sha256": row["sha256"], "text": text}
                    if len(notes) % 100 == 0:
                        emit("PROCITANO_BILJESKI", len(notes))
                except (OSError, ValueError, UnicodeError) as e:
                    issues.append(rel + ": " + str(e))
    except RuntimeError as e:
        issues.append(str(e))

    emit("FAZA", "POSTAVKE_I_POSTOJECI_STIL")
    settings = [root / ".obsidian" / name for name in (
        "app.json", "appearance.json", "core-plugins.json", "community-plugins.json",
        "daily-notes.json", "templates.json", "bookmarks.json", "hotkeys.json")]
    snippets = root / ".obsidian" / "snippets"
    try:
        if snippets.is_dir() and snippets.resolve(strict=True) == snippets:
            css = sorted(snippets.glob("*.css"))
            if len(css) > 30:
                issues.append("Pregled CSS ogranicen na prvih 30 fajlova")
            settings += css[:30]
        for p in settings:
            if not p.exists():
                continue
            try:
                raw = read(p, 524288)
                text = raw.decode("utf-8-sig")
                entry = {"sha256": hashlib.sha256(raw).hexdigest(), "text": text}
                if p.suffix == ".json":
                    entry["parsed"] = json.loads(text)
                configs[p.relative_to(root).as_posix()] = entry
            except (OSError, ValueError, UnicodeError, RuntimeError) as e:
                issues.append(str(p.relative_to(root)) + ": " + str(e))
    except OSError as e:
        issues.append("CSS: " + str(e))

    emit("FAZA", "PROVJERA_INTERNIH_VEZA")
    targets = defaultdict(set)
    for row in inventory:
        rel = row["path"]
        keys = [rel, posixpath.basename(rel)]
        if rel.lower().endswith(".md"):
            keys += [rel[:-3], posixpath.basename(rel)[:-3]]
        for key in keys:
            targets[key].add(rel)
    unresolved, ambiguous = [], []
    wiki_count = 0
    for source, text in notes.items():
        # Conservative candidate extraction: exclude fenced and inline code.
        clean = re.sub(r"(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1\s*$", "", text)
        clean = re.sub(r"`[^`\n]*`", "", clean)
        for match in re.finditer(r"\[\[([^\]\n]+)\]\]", clean):
            wiki_count += 1
            target = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
            if not target or "://" in target:
                continue
            local = posixpath.normpath(posixpath.join(posixpath.dirname(source), target))
            hits = set(targets.get(target, set())) | set(targets.get(local, set()))
            entry = {"source": source, "target": target}
            if not hits:
                unresolved.append(entry)
            elif len(hits) > 1:
                entry["candidates"] = sorted(hits)
                ambiguous.append(entry)
    by_hash, by_name = defaultdict(list), defaultdict(list)
    for row in inventory:
        if "sha256" in row:
            by_hash[row["sha256"]].append(row["path"])
            by_name[posixpath.basename(row["path"]).casefold()].append(row["path"])
    report = {
        "root": str(root), "vault_writes": 0,
        "complete_within_scope": not issues,
        "scope": "Notes and file metadata; selected core settings and up to 30 CSS snippets. No archives or plugin data read.",
        "link_check_scope": "Heuristic wiki-link target candidates only; Markdown links, heading/block anchors, Unicode/case variants are not fully validated. Findings are not automatic repair or deletion instructions.",
        "files": len(inventory), "notes_read": len(notes), "wiki_links": wiki_count,
        "empty_notes": [p for p, t in notes.items() if not t.strip()],
        "same_content_note_groups": [v for v in by_hash.values() if len(v) > 1],
        "same_name_note_groups": [v for v in by_name.values() if len(v) > 1],
        "link_targets_to_review": unresolved, "ambiguous_links_to_review": ambiguous,
        "errors_and_limits": issues, "skipped_nonregular": skipped,
        "inventory": inventory,
    }
    return report, excerpts, configs


def main():
    emit("OBSIDIAN_002", "START")
    if os.geteuid() != 0 or "ish" not in os.uname().release.lower():
        raise RuntimeError("Nije potvrdjen iPhone iSH")
    root = Path("/mnt/ARS_RAD_888")
    mounts = Path("/proc/mounts").read_text().splitlines()
    if not any(len(f) >= 3 and f[1] == str(root) and "ios" in f[2].lower()
               for f in (line.split() for line in mounts)):
        raise RuntimeError("ARS_RAD_888 nije povezan kao iOS mount")
    for p in (root, root / ".obsidian", root / "RAD", root / "1_ARS_METAL"):
        if not p.is_dir() or p.resolve(strict=True) != p:
            raise RuntimeError("Nedostaje ocekivani folder: " + str(p))
    home = root / "00 Pocetna.md"
    if not home.is_file() or home.resolve(strict=True) != home:
        raise RuntimeError("Nedostaje postojeca pocetna biljeska")
    emit("FAZA", "CITANJE_BILJESKI")
    report, excerpts, configs = scan(root)
    emit("FAZA", "PAKOVANJE_NALAZA")
    stamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    destination = Path("/root") / ("OBSIDIAN_002_NALAZ_" + stamp + "_" + str(os.getpid()) + ".zip")
    with zipfile.ZipFile(str(destination), "x", compression=zipfile.ZIP_STORED) as z:
        for name, obj in (("IZVJESTAJ.json", report), ("RADNE_BILJESKE.json", excerpts), ("POSTAVKE.json", configs)):
            z.writestr(name, json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8"))
    with zipfile.ZipFile(str(destination), "r") as z:
        if z.testzip() is not None:
            raise RuntimeError("ZIP provjera nije prosla")
    emit("BILJESKE", report["notes_read"])
    emit("VEZE_ZA_PROVJERU", len(report["link_targets_to_review"]))
    emit("GRESKE_I_OGRANICENJA", len(report["errors_and_limits"]))
    emit("IZMJENE_U_OBSIDIANU", 0)
    emit("ZIP", destination)
    emit("ZIP_BAJTOVA", destination.stat().st_size)
    emit("REZULTAT", "NALAZ_SA_OGRANICENJIMA" if report["errors_and_limits"] else "NALAZ_SPREMAN")
    emit("SLJEDECE", "Posalji ovaj ZIP u chat iz Datoteke > iSH > root")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        emit("STOP", error)
        sys.exit(1)
