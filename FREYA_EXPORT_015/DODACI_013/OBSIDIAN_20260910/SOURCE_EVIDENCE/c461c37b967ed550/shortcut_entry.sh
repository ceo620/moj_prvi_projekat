#!/bin/sh
set -eu
BRIDGE="/root/FREYA_IPHONE_ISH_NODE_888/SHORTCUTS_BRIDGE_888"
CMD="${1:-STATUS}"
case "$CMD" in
 STATUS|PING|PREPARE_HANDOFF)
   exec "$BRIDGE/03_COMMANDS/router.sh" "$CMD"
   ;;
 PREPARE_ANDROID_CANARY)
   exec "$BRIDGE/03_COMMANDS/android_canary_handoff.sh"
   ;;
 *)
   echo "PROTOCOL=888"
   echo "ENTRYPOINT=FREYA_888"
   echo "COMMAND=$CMD"
   echo "RESULT=DENY_UNKNOWN_COMMAND"
   exit 64
   ;;
esac
