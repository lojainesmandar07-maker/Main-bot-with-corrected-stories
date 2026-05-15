# The Nexus Release Audit Notes (2026-03-22)

This repository was audited for release-readiness across code quality, UX, admin UX, data integrity, and personality test quality.

## Verdict
- Status: **Not Ready**
- Primary blocker: multiplayer stories are loaded with string IDs but event commands require integer story IDs.

## Critical blockers (summary)
1. Multiplayer command `/حدث` expects `story_id: int`, while MP story files use string IDs (`mp_*`), so admin startup by ID is broken.
2. Personality test sessions are stored in-memory and never cleaned on completion/timeout, causing users to be stuck as "active".
3. Config is split between JSON (`data/config.json`) and SQLite (`nexus_config`), creating inconsistent admin setup behavior.
4. Several admin flows still require raw IDs (story/ending/role) and are too fragile for moderators.

## Evidence commands run
- `python validate_story.py`
- `python -m compileall -q .`
- custom python script to inspect story loading and mode distribution
- custom python script to profile personality-test score bias

