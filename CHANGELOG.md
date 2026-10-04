# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- feat(aligner): SA-RU sentence aligner tool layer + honest-negative evaluation (H6070) — sandhi-aware IAST tokenizer, monotonic DP aligner with an IAST→Cyrillic name-transliteration bridge + Gale-Church length term, evaluation harness over SamudraManthanam verse-aligned JSONL with a frozen 60-verse BhG sample. Measured: micro block structure correct; global-stream precision 0.03–0.10, RU→verse-group retrieval accuracy@1 0.13 — the ≥0.9 goal named-stopped at the 8-try budget; diagnosis and bilingual-lexicon repair path in H6070_SA_RU_ALIGNER_EVALUATION_04-10-2026.md.
- H4707 (15-09-2026): DCS parallel-passage QA/recall baseline — deterministic
  builder `tools/build_baseline.py` over kosha dataset
  `dcs-parallel-passages-full` (VisualDCS `PARA/Polnorazmernye/`, 245 files),
  joined metrics `data/dcs-parallels-baseline/baseline_metrics.csv`, summary
  `baseline_summary.json`, frozen 200-row sample (seed 4707); frozen-sample
  parser round-trip recall 1.00, archive-overlap recall 0.985 vs the 2022
  snapshot; dated report `H4707_DCS_PARALLELS_QA_BASELINE_15-09-2026.md`.
- Edge registered: `VisualDCS → Parallel-Sanskrit-Corpora` (Uprava
  `interlinks_edges.tsv`); kosha dataset row flipped to consumed.
