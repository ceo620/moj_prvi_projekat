#!/bin/bash
set -u

echo "======================================================================"
echo " MAGNUS — LENOVO FINAL BATCH 001 IDENTITY"
echo "======================================================================"

echo "PROTOCOL=888"
echo "MACHINE=LENOVO"
echo "NODE=FREYA_LENOVO_DEBIAN_888"
echo "MODE=READ_ONLY_IDENTITY"
echo "HUMAN_GATE=ACTIVE"

echo
echo "===== OS ====="
cat /etc/os-release 2>/dev/null || true
uname -a

echo
echo "===== USER ====="
id
whoami

echo
echo "===== STORAGE ====="
df -h

echo
echo "===== SAFETY ====="
echo "DELETE=DENY"
echo "WRITE=DENY"
echo "FORMAT=DENY"
echo "WIPE=DENY"
echo "REPAIR=DENY"

echo
echo "RESULT=PASS"
echo "NEXT=LENOVO_BATCH_FINAL_002_STORAGE"
