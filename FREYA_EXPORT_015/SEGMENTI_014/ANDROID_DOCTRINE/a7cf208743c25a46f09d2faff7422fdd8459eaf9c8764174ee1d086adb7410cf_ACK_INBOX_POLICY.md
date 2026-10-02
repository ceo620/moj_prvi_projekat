# Android ACK Inbox Policy

## Directory states

- `00_INCOMING_PARTIAL`: incomplete local transfer objects only.
- `01_INCOMING_READY`: complete objects awaiting strict validation.
- `02_VALIDATED`: objects that passed schema, hash and package binding checks.
- `03_APPLIED`: reserved for a future separately approved ACK application step.
- `04_CONFIRMED`: reserved for a future separately approved confirmation step.
- `90_QUARANTINE`: invalid, conflicting or unsafe objects.
- `99_ARCHIVE`: immutable historical objects after separately approved closure.

## Mandatory controls

- Default deny and fail closed.
- Human Gate remains active.
- Atomic no-replace state transitions are required.
- ACK and sidecar hashes must match before any state transition.
- Duplicate ACK IDs with different hashes must be quarantined.
- Existing files must never be overwritten.
- No file deletion is authorized.
- No network, scheduler, cron or service is authorized by this installation.
