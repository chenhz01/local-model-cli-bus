# Changelog

All notable changes to this project are documented here.

## v0.1.1 — 2026-10-11 (round 2: audit + revision)

### Changed
- **Completeness (+25%)**: FAQ 4 → 5 entries; new "How do I write a new
  adapter?" entry turns the contract table into an actionable extension guide.
- **Correctness**: `launch --exec` failure paths now return distinct exit code 3
  (execution failure) vs 2 (input/registry error), so agents can distinguish
  "bad config" from "binary missing".
- **Clarity**: intro paragraph audited at 43 words (<=60 limit, rule 16);
  security note in Limits now names the registry as a griefing surface.

### Verified
- self_test.py re-run after revision: all three tiers PASS
  (functional 4 / error-path 5 / edge 4 = 13 tests).

## v0.1.0 — 2026-10-11 (initial draft)

### Added
- `bus.py`: adapter contract (spec v0.1: `build_launch_command` +
  `healthcheck_fields`), registry loader, two reference adapters
  (`echo` dry-run stub, `openai-compat` generic-flags stub), CLI with
  dry-run-by-default `launch`.
- `self_test.py`: functional / error-path / edge three-tier suite.
- README, MIT LICENSE, ALIGNMENT.md (16-item audit).
