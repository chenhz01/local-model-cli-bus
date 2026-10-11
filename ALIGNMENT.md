# Alignment Audit (Rules 85-100 / 16 items) — local-model-cli-bus

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Non-security-domain tool. Dry-run-by-default and exec-failure semantics documented in README + FAQ. |
| 2 | Privacy de-identification | PASS | grep `(sk-\|ghp_\|api[_-]?key\s*=\s*['"][A-Za-z0-9])` = 0 hits; no real names/emails; registry uses placeholder binary names and localhost URLs. |
| 3 | Copyright boundary | PASS | No vendor documentation copied; adapter contract written from scratch; registry binds to no vendor private API. LICENSE (MIT) present. |
| 4 | Fact-check labeling | PASS | OpenAI-compat dominance claim labeled Medium + `[estimated]`; no unmeasured performance numbers present. |
| 5 | Confidence grading | PASS | README Confidence block: High (contract implementable, tested) + Medium (generic-flag coverage), each with rationale. |
| 6 | Plan B built-in | PASS | README "Minimal Fallback": spec implementable in any language; built-in stub registry works with zero config. |
| 7 | Timeout preset | PASS | Quickstart: ~1 s per step + full self-test ~15 s, staged path. |
| 8 | Rule conflict arbitration | PASS | README "Design Trade-offs": no vendor lock-in > dry-run safety > simplicity > features. |
| 9 | Version changelog | PASS | CHANGELOG.md: v0.1.0 + v0.1.1 with improvements traced. |
| 10 | Exemption instruction | N/A | Session-level governance rule; static repo N/A. |
| 11 | External knowledge cutoff | PASS | "as of 2026-10-11" stamped in header, launch-plan output, and spec version lines. |
| 12 | Assumptions explicit | PASS | README `[Core Assumptions]`: 4 items (OpenAI-compat dominance, agent exec+probe capability, static registry stability, dry-run-first). |
| 13 | Logic-check trio | PASS | self_test.py: functional 4 / error-path 5 / edge 4 (corrupt registry, empty registry, 100k-char model name, missing-binary exec) — all PASS. |
| 14 | Socratic FAQ | PASS | FAQ "When NOT to use this bus?" with 3 concrete anti-cases; 5 FAQ entries total after round 2. |
| 15 | Pareto iteration | PASS | v0.1.1: README completeness +25% (FAQ 4→5, adapter-extension guide); exit-code correctness fix; tests re-run PASS. |
| 16 | Ultimate fallback (60-word entry) | PASS | Intro paragraph = 43 words, states what/spec/stubs and the lock-in benefit. |

Audit date: 2026-10-11. Auditor: zhengming W5 (self-audit, round 2).
