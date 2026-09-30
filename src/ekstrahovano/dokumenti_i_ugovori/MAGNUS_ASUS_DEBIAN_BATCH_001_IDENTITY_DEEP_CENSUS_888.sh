#!/usr/bin/env bash

set -Eeuo pipefail

echo "============================================================"
echo " MAGNUS — PROTOCOL 888 — ASUS DEBIAN BATCH 001"
echo " IDENTITY DEEP CENSUS — READ ONLY"
echo "============================================================"

START_UTC="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$HOME/FREYA_ASUS_DEBIAN_888/16_REPORTS/BATCH_001_$START_UTC"

mkdir -p "$OUT"

{
echo "PROTOCOL=888"
echo "AGENT=MAGNUS"
echo "MACHINE=ASUS"
echo "NODE=FREYA_ASUS_DEBIAN_888"
echo "BATCH=001"
echo "MODE=READ_ONLY_DISCOVERY"
echo "START_UTC=$START_UTC"
echo "HOSTNAME=$(hostname)"
echo "USER=$(whoami)"
echo "UID=$(id -u)"
echo "GID=$(id -g)"
echo "HOME=$HOME"
echo "SHELL=${SHELL:-unknown}"
} > "$OUT/IDENTITY.env"

echo "--- OS ---"
cat /etc/os-release 2>/dev/null | tee "$OUT/os_release.txt" || true
uname -a | tee "$OUT/kernel.txt"

echo "--- USER ---"
id | tee "$OUT/id.txt"
groups | tee "$OUT/groups.txt"

echo "--- ARCH ---"
uname -m | tee "$OUT/architecture.txt"

echo "--- WSL CHECK ---"
{
if grep -qi microsoft /proc/version 2>/dev/null; then
echo "WSL_STATUS=YES"
else
echo "WSL_STATUS=NO_OR_UNKNOWN"
fi
} | tee "$OUT/wsl_status.txt"

echo "--- WINDOWS INTEROP ---"
{
if [ -d /mnt/c ]; then
echo "WINDOWS_INTEROP=YES"
ls -la /mnt/c | head -20
else
echo "WINDOWS_INTEROP=NO"
fi
} | tee "$OUT/windows_interop.txt"

echo "--- ZA_POTPISIVANJE ---"
{
TARGET="/mnt/c/Users/ceo/OneDrive/Desktop/ZA_POTPISIVANJE"
if [ -d "$TARGET" ]; then
echo "ZA_POTPISIVANJE=PROVEN"
echo "PATH=$TARGET"
else
echo "ZA_POTPISIVANJE=NOT_PROVEN"
fi
} | tee "$OUT/za_potpisivanje.txt"

echo "--- FILESYSTEM ---"
df -h | tee "$OUT/df_h.txt"
df -i | tee "$OUT/inodes.txt"
mount | tee "$OUT/mounts.txt"

echo "--- MEMORY CPU ---"
free -h | tee "$OUT/memory.txt"
nproc | tee "$OUT/cpu_count.txt"

echo "--- NETWORK READ ONLY ---"
ip addr 2>/dev/null | tee "$OUT/network.txt" || true

echo "--- HOME CONTENT ---"
find "$HOME" -maxdepth 1 -mindepth 1 -printf "%f\n" 2>/dev/null | tee "$OUT/home_top.txt"

echo "--- ROOT CANDIDATES ---"
find "$HOME" -maxdepth 3 \
\( -iname "*FREYA*" -o -iname "*ASUS*" -o -iname "*MAGNUS*" -o -iname "*FACTORY*" \) \
2>/dev/null | tee "$OUT/root_candidates.txt"

echo "--- SCRIPT COUNTS ---"
{
echo "BASH=$(find "$HOME" -type f -name "*.sh" 2>/dev/null | wc -l)"
echo "PYTHON=$(find "$HOME" -type f -name "*.py" 2>/dev/null | wc -l)"
echo "POWERSHELL=$(find "$HOME" -type f -name "*.ps1" 2>/dev/null | wc -l)"
echo "ARCHIVES=$(find "$HOME" -type f \( -name "*.zip" -o -name "*.tar.gz" -o -name "*.tgz" \) 2>/dev/null | wc -l)"
} | tee "$OUT/file_counts.txt"

echo "--- LARGE DIRECTORIES ---"
du -xh "$HOME" 2>/dev/null | sort -h | tail -30 | tee "$OUT/large_directories.txt"

echo "--- CANDIDATE SEARCH ---"
find "$HOME" \
\( -iname "*SSOT*" -o -iname "*MANIFEST*" -o -iname "*AGENT*" -o -iname "*QUEUE*" -o -iname "*DOCUMENT*" -o -iname "*READY*" \) \
2>/dev/null | tee "$OUT/candidates.txt"

echo "--- PERMISSION ANOMALIES READ ONLY ---"
find "$HOME" -type f -perm /111 2>/dev/null | head -100 | tee "$OUT/executable_files.txt"

echo "============================================================"
echo "RESULT=PASS"
echo "REPORT_DIR=$OUT"
echo "NEXT_RECOMMENDED_BATCH=BATCH_002_CANONICAL_ROOT_DISCOVERY"
echo "============================================================"

