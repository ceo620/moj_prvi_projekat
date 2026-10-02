# FREYA 24H DEVICE NETWORK PREP

STATUS: PREPARATION_ONLY
RUNTIME: OFF
DAEMONS: OFF
HUMAN_GATE: ACTIVE

GOAL:
All devices will eventually communicate through controlled 24h network layer.

NODES:
1. iPhone Alpine iSH
2. Android Termux
3. Mac Control Tower
4. Lenovo CMU
5. MSI Builder Ocean
6. External disks / archive sources

RULES:
- No daemon activation yet
- No automatic sync yet
- No delete
- No move
- No overwrite
- No remote command execution
- Network must be manifest-first, hash-first, human-approved

COMMUNICATION MODEL:
iPhone/Android -> Mac Control Tower -> Lenovo/MSI
Mac is the control tower.
Other devices send manifests, hashes, health reports, and approved packets.

NEXT:
Build device inventory and network readiness register.
