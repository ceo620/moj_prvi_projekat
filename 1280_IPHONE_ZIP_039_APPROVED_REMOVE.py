#!/usr/bin/env python3
"""039: exact five-file removal only after explicit approval.
No default action. Requires --approval ODOBRAVAM_039_PET_ZIPOVA.
Revalidates pinned evidence, all seven retained files, all five ZIPs, startup
and current process references. Logs each removal and inventories /root.
"""
import errno
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import time
ROOT = "/root/FREYA_RAD_888"
PRIOR = ROOT + "/REZULTATI/IPHONE_ZIP_038_bifqbn7e/REPORT.json"
PRIOR_SHA = "a344d2d47da0c27f2816779d60501a1e4cbe7d3b9cf9b803d7332dec2a3409af"
TRANSIENT = {errno.ENOENT, errno.EIO, errno.EINTR, errno.EAGAIN}
APPROVAL = "ODOBRAVAM_039_PET_ZIPOVA"
EXPECTED = {
 "/root/ZA_CHAT_014_UPLOAD.zip": (10158121, "e924444cb8151aae9dcd7b2f3af5fb0e835c80c83c3001f883abc143a749dc28"),
 "/root/ZA_CHAT_015_UPLOAD.zip": (41710, "120c2b23eb6d2a3e6a12dee06aa645e60f0596cb6b5ffc83b404ad2b907fd040"),
 "/root/ZA_CHAT_016_UPLOAD.zip": (35524, "c6c2fea11e180d74b16e89442675b2c5950b6399872d6f37322f1b2d0a11d696"),
 "/root/ZA_CHAT_018_UPLOAD.zip": (34900, "eeab8ae3b097cb840a3dfb63db10efb209cbe03a27495b260a4933005d5bd8a0"),
 "/root/ZA_CHAT_019_UPLOAD.zip": (5538, "64db0f7e1e6d795059206452f410019b56517a4cfe3fb1e31f94bfe1a262bcd5"),
}
STARTUP_FILES = ["/etc/inittab", "/etc/profile", "/etc/crontabs/root", "/etc/crontab",
                 "/etc/rc.local", "/root/.profile", "/root/.ashrc", "/root/.bashrc", "/root/.zshrc"]
STARTUP_DIRS = ["/etc/init.d", "/etc/local.d", "/etc/periodic", "/etc/profile.d", "/etc/crontabs"]


class Hold(Exception):
    pass

def signature(st):
    # ctime is not a content test on this iSH installation.
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)

def open_regular(path):
    if not path.startswith("/") or any(x in ("", ".", "..") for x in path.split("/")[1:]):
        raise Hold("PUTANJA")
    for attempt in range(3):
        directory = None
        try:
            directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            pieces = path.split("/")[1:]
            for piece in pieces[:-1]:
                nxt = os.open(piece, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=directory)
                os.close(directory)
                directory = nxt
            fd = os.open(pieces[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=directory)
            stream = os.fdopen(fd, "rb")
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                stream.close()
                raise Hold("NIJE_OBICAN_FAJL")
            return stream
        except OSError as error:
            if attempt == 2 or error.errno not in TRANSIENT:
                raise
            time.sleep(0.2)
        finally:
            if directory is not None:
                os.close(directory)

def small(path, limit):
    with open_regular(path) as stream:
        before = os.fstat(stream.fileno())
        if before.st_size > limit:
            raise Hold("LIMIT_CITANJA")
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    if len(data) != before.st_size or signature(before) != signature(after):
        raise Hold("NESTABILNO_CITANJE")
    return data

def error_code(error):
    if isinstance(error, Hold):
        return str(error)
    if isinstance(error, OSError):
        return "OS_ERRNO_" + str(error.errno)
    return type(error).__name__

def atomic_new(path, data):
    digest = hashlib.sha256(data).hexdigest()
    try:
        existing = small(path, len(data) + 1)
    except FileNotFoundError:
        existing = None
    if existing is not None:
        if len(existing) != len(data) or hashlib.sha256(existing).hexdigest() != digest:
            raise Hold("POSTOJECE_ODREDISTE_RAZLICITO")
        return False
    fd, temporary = tempfile.mkstemp(prefix=".038_", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if small(temporary, len(data) + 1) != data:
            raise Hold("PRIVREMENI_FAJL_READBACK")
        # Publish the newly written bytes without replacing any existing name.
        # This temporary publication link is not counted as a backup.
        os.link(temporary, path)
    finally:
        os.unlink(temporary)
    if small(path, len(data) + 1) != data:
        raise Hold("KONACNI_FAJL_READBACK")
    return True

def startup_check(needles):
    paths = set(STARTUP_FILES)
    errors, hits = [], []
    checked = 0
    for root in STARTUP_DIRS:
        if not os.path.lexists(root):
            continue
        if os.path.realpath(root) != root or not stat.S_ISDIR(os.lstat(root).st_mode):
            errors.append({"path": root, "reason": "STARTUP_DIRECTORY_INDIRECT"})
            continue
        device = os.lstat(root).st_dev
        def onerror(error):
            errors.append({"path": error.filename, "reason": error_code(error)})
        for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
            for name in list(dirs):
                p = os.path.join(directory, name)
                if os.path.islink(p) or os.lstat(p).st_dev != device:
                    dirs.remove(name)
                    errors.append({"path": p, "reason": "STARTUP_DIRECTORY_SYMLINK"})
            paths.update(os.path.join(directory, name) for name in files)
    for path in sorted(paths):
        if not os.path.lexists(path):
            continue
        try:
            data = small(path, 1024*1024)
            checked += 1
            found = sorted(label for label, needle in needles.items() if needle in data)
            # Wildcard-based invocation of audit tooling is not treated as absent.
            generic = (b"IPHONE_ZIP_" in data or b"ZA_CHAT_" in data)
            if found or generic:
                hits.append({"path": path, "references": found, "family_reference": generic})
        except (Hold, OSError) as error:
            errors.append({"path": path, "reason": error_code(error)})
    return {"files_checked": checked, "hits": hits, "errors": errors,
            "scope": STARTUP_FILES + STARTUP_DIRS}

def process_check(needles):
    hits, errors = [], []
    count = 0
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == os.getpid():
            continue
        base = "/proc/" + pid
        try:
            with open(base + "/cmdline", "rb") as stream:
                command = stream.read(262145)
            if len(command) > 262144:
                errors.append({"pid": pid, "reason": "CMDLINE_LIMIT"})
                continue
            found = sorted(label for label, needle in needles.items() if needle in command)
            del command  # No command lines or other arguments are emitted or saved.
            if found:
                hits.append({"pid": pid, "source": "cmdline", "references": found})
            count += 1
            for name in os.listdir(base + "/fd"):
                try:
                    target = os.readlink(base + "/fd/" + name).encode()
                    found = sorted(label for label, needle in needles.items() if needle in target)
                    if found:
                        hits.append({"pid": pid, "source": "open_fd", "references": found})
                except FileNotFoundError:
                    pass  # File descriptors may close while enumerated.
        except FileNotFoundError:
            if os.path.exists(base):
                errors.append({"pid": pid, "reason": "PROCESS_INTERFACE_UNAVAILABLE"})
        except OSError as error:
            errors.append({"pid": pid, "reason": error_code(error)})
    return {"processes_checked": count, "hits": hits, "errors": errors,
            "scope": "current_process_arguments_and_open_fds", "command_lines_disclosed": False}


def verify_content(stream, size, digest):
    before = os.fstat(stream.fileno())
    if before.st_size != size:
        raise Hold("VELICINA")
    stream.seek(0)
    h, count = hashlib.sha256(), 0
    while True:
        block = stream.read(1024*1024)
        if not block:
            break
        count += len(block)
        if count > size:
            raise Hold("SADRZAJ_PORASTAO")
        h.update(block)
        if size > 64*1024*1024 and count % (32*1024*1024) == 0:
            print("PRED_BRISANJE_IZVOR_MIB=" + str(count // (1024*1024)), flush=True)
    after = os.fstat(stream.fileno())
    if count != size or h.hexdigest() != digest or signature(before) != signature(after):
        raise Hold("SHA256_ILI_STABILNOST")
    return list(signature(after))


def verify_path_binding(path, stream):
    if os.path.realpath(path) != path:
        raise Hold("PUTANJA_PREUSMJERENA")
    current = os.lstat(path)
    if not stat.S_ISREG(current.st_mode) or signature(current) != signature(os.fstat(stream.fileno())):
        raise Hold("VEZA_PUTANJE_PROMIJENJENA")


def remove_exact(parent_fd, path, stream, parent_path="/root"):
    if path not in EXPECTED or os.path.dirname(path) != parent_path:
        raise Hold("IZVAN_ODOBRENJA")
    root_now = os.lstat(parent_path)
    root_fd = os.fstat(parent_fd)
    if not stat.S_ISDIR(root_now.st_mode) or (root_now.st_dev, root_now.st_ino) != (root_fd.st_dev, root_fd.st_ino):
        raise Hold("ROOT_PROMJENA")
    current = os.stat(os.path.basename(path), dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISREG(current.st_mode) or signature(current) != signature(os.fstat(stream.fileno())):
        raise Hold("ZIP_IDENTITET_PRED_BRISANJE")
    os.unlink(os.path.basename(path), dir_fd=parent_fd)
    try:
        os.stat(os.path.basename(path), dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise Hold("PUTANJA_PONOVO_POSTOJI_POSLIJE_UNLINK")


def inventory():
    with open("/proc/mounts", "rb") as stream:
        raw = stream.read(1024*1024 + 1)
    if len(raw) > 1024*1024:
        raise Hold("MOUNTS_LIMIT")
    decode = lambda text: re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), text)
    mounts = {decode(line.split()[1]) for line in raw.decode().splitlines() if len(line.split()) >= 3}
    if "/" not in mounts:
        raise Hold("MOUNTS_NEPOTPUNO")
    device = os.lstat("/root").st_dev
    paths, errors, excluded = [], [], []
    start = time.monotonic()
    def onerror(error):
        errors.append({"path": error.filename, "reason": error_code(error)})
    for folder, dirs, files, fd in os.fwalk("/root", topdown=True, follow_symlinks=False, onerror=onerror):
        if time.monotonic() - start > 180:
            errors.append({"reason": "INVENTAR_LIMIT"})
            break
        kept = []
        for name in dirs:
            path = os.path.join(folder, name)
            try:
                st = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if path in mounts or st.st_dev != device:
                    excluded.append(path)
                elif stat.S_ISDIR(st.st_mode):
                    kept.append(name)
            except OSError as error:
                errors.append({"path": path, "reason": error_code(error)})
        dirs[:] = kept
        for name in files:
            if not name.lower().endswith(".zip"):
                continue
            path = os.path.join(folder, name)
            try:
                st = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISREG(st.st_mode) and st.st_dev == device and path not in mounts:
                    paths.append({"path": path, "bytes": st.st_size})
            except OSError as error:
                errors.append({"path": path, "reason": error_code(error)})
    return {"scope": "/root", "selector": "regular files with case-insensitive .zip suffix",
            "cross_mounts": False, "follow_symlinks": False, "complete": not errors,
            "paths": sorted(paths, key=lambda x: x["path"]), "errors": errors, "excluded_mounts": excluded}


def emit_event(stream, event):
    stream.write(json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def main():
    if sys.argv[1:] != ["--approval", APPROVAL]:
        raise Hold("POTREBNO_EKSPLICITNO_ODOBRENJE_039_PET_ZIPOVA")
    print("BATCH=IPHONE_ZIP_039; APPROVED_SCOPE=FIVE_EXACT_ZIP_PATHS", flush=True)
    if os.geteuid() != 0 or small("/etc/alpine-release", 256).strip() != b"3.14.3":
        raise Hold("OKRUZENJE")
    data = small(PRIOR, 8*1024*1024)
    if hashlib.sha256(data).hexdigest() != PRIOR_SHA:
        raise Hold("038_REPORT_SHA256")
    prior = json.loads(data)
    plans = prior["candidate_package"]
    if len(plans) != 5 or {p["path"] for p in plans} != set(EXPECTED):
        raise Hold("ODOBRENI_SPISAK")
    for plan in plans:
        if plan["holds"] or (plan["bytes"], plan["sha256"]) != EXPECTED[plan["path"]]:
            raise Hold("PAKET_NE_ODGOVARA")
    for key in ("startup", "processes"):
        if prior[key]["hits"] or prior[key]["errors"]:
            raise Hold("038_AKTIVNE_REFERENCE")
    if prior["excluded_links"]["direct_target_hits"] or prior["excluded_links"]["errors"]:
        raise Hold("038_SYMLINK_REFERENCE")
    names = [os.path.basename(p) for p in EXPECTED] + [os.path.basename(t["path"]) for t in prior["tools"]]
    needles = {name: os.fsencode(name) for name in names}
    archives, sources = {}, {}
    root_fd = None
    try:
        for plan in plans:
            for source in plan["sources"]:
                path = source["path"]
                if path in EXPECTED:
                    raise Hold("ZIP_NE_MOZE_BITI_JEDINI_IZVOR")
                if path not in sources:
                    stream = open_regular(path)
                    sources[path] = stream
                    identity = verify_content(stream, source["bytes"], source["sha256"])
                    if identity != source["identity_now"]:
                        raise Hold("IZVOR_IDENTITET_NE_ODGOVARA_ODOBRENJU")
                    verify_path_binding(path, stream)
        if len(sources) != 7:
            raise Hold("BROJ_OCUVANIH_IZVORA")
        print("SEDAM_OCUVANIH_IZVORA_SHA256=PASS", flush=True)
        for plan in plans:
            stream = open_regular(plan["path"])
            archives[plan["path"]] = stream
            identity = verify_content(stream, plan["bytes"], plan["sha256"])
            if identity != plan["identity_now"]:
                raise Hold("ZIP_IDENTITET_NE_ODGOVARA_ODOBRENJU")
            verify_path_binding(plan["path"], stream)
        print("PET_ODOBRENIH_ZIPOVA_SHA256=PASS", flush=True)
        startup, processes = startup_check(needles), process_check(needles)
        if startup["hits"] or startup["errors"] or processes["hits"] or processes["errors"]:
            raise Hold("AKTIVNA_REFERENCA_ILI_NEPOTPUNA_PROVJERA")
        root_fd = os.open("/root", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parent = ROOT + "/REZULTATI"
        if os.path.realpath(parent) != parent:
            raise Hold("EVIDENCIJA_SYMLINK")
        folder = tempfile.mkdtemp(prefix="IPHONE_ZIP_039_", dir=parent)
        result = {"batch": "IPHONE_ZIP_039", "approval": APPROVAL, "authority": "Danijela Djurovic Keskin",
                  "approved_report": PRIOR, "approved_report_sha256": PRIOR_SHA,
                  "approved_package": plans, "startup": startup, "processes": processes,
                  "deleted": [], "errors": [], "off_device_copy": False,
                  "all_sources_sha256": "PASS", "all_archives_sha256": "PASS",
                  "dependency_basis": "038 reviewed historical audit references; no active references in checked scopes"}
        with open(folder + "/EVENTS.jsonl", "x", encoding="utf-8") as journal:
            os.fchmod(journal.fileno(), 0o600)
            emit_event(journal, {"event": "PREPARED", "approved_report_sha256": PRIOR_SHA,
                                 "paths": list(EXPECTED), "all_content_hashes": "PASS"})
            try:
                for plan in plans:
                    for path, stream in sources.items():
                        verify_path_binding(path, stream)
                    stream = archives[plan["path"]]
                    # Full current content check of this exact approved archive
                    # immediately before unlink; do not accept metadata alone.
                    verify_content(stream, plan["bytes"], plan["sha256"])
                    emit_event(journal, {"event": "UNLINK_INTENT", "path": plan["path"], "sha256": plan["sha256"]})
                    remove_exact(root_fd, plan["path"], stream)
                    result["deleted"].append({"path": plan["path"], "sha256": plan["sha256"], "bytes": plan["bytes"]})
                    emit_event(journal, {"event": "UNLINK_CONFIRMED", "path": plan["path"]})
                    stream.close()
                    print("OBRISANO=" + plan["path"], flush=True)
            except (Hold, OSError) as error:
                result["errors"].append(error_code(error))
                emit_event(journal, {"event": "HOLD", "reason": error_code(error)})
        try:
            result["final_inventory"] = inventory()
        except (Hold, OSError) as error:
            result["final_inventory"] = {"scope": "/root", "complete": False, "errors": [error_code(error)]}
        result["logical_zip_bytes_removed"] = sum(row["bytes"] for row in result["deleted"])
        result["physical_bytes_reclaimed"] = "NOT_DETERMINED"
        result["remaining_known_missing_archives"] = "THREE HISTORICAL PATHS; NOT DELETED BY THIS ACTION"
        result["overall_zip_zero_goal"] = "NOT_COMPLETE"
        output = folder + "/REPORT.json"
        raw = json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2).encode() + b"\n"
        atomic_new(output, raw)
        print("OBRISANO_U_039=" + str(len(result["deleted"])) + "/5", flush=True)
        print("UKLONJENO_LOGICKIH_BAJTOVA=" + str(result["logical_zip_bytes_removed"]), flush=True)
        inv = result["final_inventory"]
        print("ZAVRSNI_INVENTAR_POTPUN=" + str(inv["complete"]), flush=True)
        if "paths" in inv:
            print("PREOSTALO_ZIP_PUTANJA_ROOT=" + str(len(inv["paths"])), flush=True)
        print("GRESKE=" + json.dumps(result["errors"] + inv.get("errors", [])), flush=True)
        print("REPORT=" + output + "\nREPORT_SHA256=" + hashlib.sha256(raw).hexdigest(), flush=True)
        print("SLJEDECE=VRATI_IZLAZ; PREOSTALE_ARHIVE_NIJESU_ODOBRENE_ZA_BRISANJE", flush=True)
    finally:
        for stream in list(archives.values()) + list(sources.values()):
            stream.close()
        if root_fd is not None:
            os.close(root_fd)


if __name__ == "__main__":
    try:
        main()
    except (Hold, OSError, ValueError, KeyError) as error:
        print("HOLD=" + error_code(error), flush=True)
        raise SystemExit(2)
