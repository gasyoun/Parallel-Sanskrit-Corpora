# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- H4707 (15-09-2026): DCS parallel-passage QA/recall baseline — deterministic
  builder `tools/build_baseline.py` over kosha dataset
  `dcs-parallel-passages-full` (VisualDCS `PARA/Polnorazmernye/`, 245 files),
  joined metrics `data/dcs-parallels-baseline/baseline_metrics.csv`, summary
  `baseline_summary.json`, frozen 200-row sample (seed 4707); frozen-sample
  parser round-trip recall 1.00, archive-overlap recall 0.985 vs the 2022
  snapshot; dated report `H4707_DCS_PARALLELS_QA_BASELINE_15-09-2026.md`.
- Edge registered: `VisualDCS → Parallel-Sanskrit-Corpora` (Uprava
  `interlinks_edges.tsv`); kosha dataset row flipped to consumed.
