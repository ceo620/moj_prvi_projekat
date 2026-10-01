# LILITH — SIGNAL_RESEARCH — PROTOCOL 888

Status: STAGING ONLY. Not production. Not activated.

Purpose:
Extract and classify signals only from explicitly approved local input.

Input:
- stdin JSON only
- exact object with one `content` string
- no directory discovery
- no arbitrary file reads

Model:
- Ollama local
- llama3.1:latest
- loopback endpoint only

Security:
- external network denied
- external send denied
- file writes denied
- RED disk writes denied
- SSOT writes denied
- automatic signature denied
- automatic send denied
- autostart denied
- background daemon denied

Dry-run execution requires the literal Human Gate token:

APPROVE_LILITH_LOCAL_DRY_RUN

No production authority is granted by this staging package.
