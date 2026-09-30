#!/bin/bash
set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

TARGET="/mnt/c/Users/titangrid.info/Desktop/FREYA_150_FROM_MAC_REVIEW_ONLY – kopija"
CHAIN="$TARGET/_FREYA_CHAIN_WAKE"
IN="$HOME/FREYA_BUILDER/01_INBOX/FROM_MAC"

MAC_IP="192.168.1.109"
MAC_PORT="8765"
PKG="FREYA_MAC_DISK_ANDROID_TO_LENOVO_PACKET_20260702_001724.tar.gz"
SHA="$PKG.sha256"

mkdir -p "$CHAIN/logs" "$CHAIN/reports" "$CHAIN/registers" "$CHAIN/state" "$CHAIN/device_orders"
echo "$$" > "$CHAIN/FREYA_CHAIN_WAKE.pid"

while true; do
  TS="$(date '+%Y-%m-%d %H:%M:%S')"
  RUN="$(date '+%Y%m%d_%H%M%S')"
  R="$CHAIN/reports/CHAIN_WAKE_TICK_$RUN"
  mkdir -p "$R"

  MAC_PING="NO"
  MAC_HTTP="NO"
  MAC_PACKET="NO"
  ANDROID_GATE="WAITING_FOR_MAC"
  IPHONE_GATE="WAITING_FOR_ANDROID"

  # 1. Lenovo tries to see Mac
  if ping -c 1 -W 1 "$MAC_IP" >/dev/null 2>&1; then
    MAC_PING="YES"
  fi

  if curl -fsI --connect-timeout 2 --max-time 4 "http://$MAC_IP:$MAC_PORT/$PKG" >/dev/null 2>&1; then
    MAC_HTTP="YES"
  fi

  # 2. If Mac HTTP is reachable, try packet pull safely
  if [ "$MAC_HTTP" = "YES" ]; then
    mkdir -p "$IN"
    cd "$IN" || exit 1
    curl -fL --connect-timeout 5 --max-time 30 "http://$MAC_IP:$MAC_PORT/$PKG" -o "$PKG.tmp" >/dev/null 2>&1 || true
    curl -fL --connect-timeout 5 --max-time 30 "http://$MAC_IP:$MAC_PORT/$SHA" -o "$SHA.tmp" >/dev/null 2>&1 || true

    if [ -f "$PKG.tmp" ] && [ -f "$SHA.tmp" ]; then
      EXPECTED="$(awk '{print $1}' "$SHA.tmp" 2>/dev/null || true)"
      ACTUAL="$(sha256sum "$PKG.tmp" 2>/dev/null | awk '{print $1}' || true)"
      if [ -n "$EXPECTED" ] && [ -n "$ACTUAL" ] && [ "$EXPECTED" = "$ACTUAL" ]; then
        mv "$PKG.tmp" "$PKG"
        mv "$SHA.tmp" "$SHA"
        MAC_PACKET="YES_SHA_OK"
        ANDROID_GATE="READY_THROUGH_MAC_PACKET"
      else
        MAC_PACKET="SHA_FAIL"
        rm -f "$PKG.tmp" "$SHA.tmp"
      fi
    fi
  else
    rm -f "$IN/$PKG.tmp" "$IN/$SHA.tmp" 2>/dev/null || true
  fi

  # 3. Android and iPhone are not forced; they receive order cards
  if [ "$ANDROID_GATE" = "READY_THROUGH_MAC_PACKET" ]; then
    IPHONE_GATE="WAITING_ANDROID_OPERATOR_CONFIRMATION"
  fi

  cat > "$CHAIN/device_orders/01_LENOVO_ORDER.md" <<ORDER
NODE=LENOVO_WSL_DELTA
ROLE=CHAIN_COMMANDER
STATUS=ACTIVE
LAST_TICK=$TS
ACTION=CHECK_MAC_GATE_AND_PULL_PACKET_IF_SHA_SAFE
ORDER

  cat > "$CHAIN/device_orders/02_MAC_ORDER.md" <<ORDER
NODE=MAC_CONTROL_TOWER
ROLE=PROVIDE_PACKET_TO_LENOVO
MAC_IP=$MAC_IP
MAC_PORT=$MAC_PORT
PING=$MAC_PING
HTTP=$MAC_HTTP
PACKET_STATUS=$MAC_PACKET
NEEDED_ACTION_IF_NOT_REACHABLE=KEEP_MAC_ON_SAME_NETWORK_AND_ALLOW_PYTHON_HTTP_SERVER
LAST_TICK=$TS
ORDER

  cat > "$CHAIN/device_orders/03_ANDROID_ORDER.md" <<ORDER
NODE=ANDROID_TERMUX
ROLE=RELAY_HASH_MANIFEST
STATUS=$ANDROID_GATE
NEEDED_ACTION=WAIT_FOR_MAC_PACKET_OR_PREPARE_ANDROID_PACKET_FOR_MAC
LAST_TICK=$TS
ORDER

  cat > "$CHAIN/device_orders/04_IPHONE_ORDER.md" <<ORDER
NODE=IPHONE_ALPINE
ROLE=VISIBLE_EVIDENCE_SOURCE
STATUS=$IPHONE_GATE
NEEDED_ACTION=WAIT_FOR_ANDROID_RELAY_OR_EXPORT_VISIBLE_EVIDENCE_TO_ANDROID
LAST_TICK=$TS
ORDER

  cat > "$CHAIN/FREYA_CHAIN_CONTROL_PANEL.md" <<PANEL
FREYA CHAIN CONTROL PANEL

LAST_TICK=$TS
PID=$$

CHAIN:
LENOVO -> MAC -> ANDROID -> IPHONE

CURRENT:
LENOVO=ACTIVE
MAC_PING=$MAC_PING
MAC_HTTP=$MAC_HTTP
MAC_PACKET=$MAC_PACKET
ANDROID_GATE=$ANDROID_GATE
IPHONE_GATE=$IPHONE_GATE

RULES:
RUNTIME=BLOCKED
UNKNOWN_SCRIPT_EXECUTION=BLOCKED
DELETE=BLOCKED
UNPACK=BLOCKED
INDEX_ONLY_AFTER_SHA_OK=YES
HUMAN_GATE=ACTIVE

NEXT:
If MAC_HTTP=NO, Mac and Lenovo are not reachable on same route.
If MAC_PACKET=YES_SHA_OK, Lenovo may register packet and index only.
PANEL

  echo "$TS	CHAIN_TICK	MAC_PING=$MAC_PING	MAC_HTTP=$MAC_HTTP	MAC_PACKET=$MAC_PACKET	ANDROID=$ANDROID_GATE	IPHONE=$IPHONE_GATE" >> "$CHAIN/registers/FREYA_CHAIN_WAKE_TICKS.tsv"

  sleep 60
done
