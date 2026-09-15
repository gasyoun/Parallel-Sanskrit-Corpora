# H4707 — DCS parallel-passage alignments as QA/recall baseline (baseline report)

_Created: 15-09-2026 · Last updated: 15-09-2026_

**Handoff:** [H4707-OxAlpha_Parallel-Sanskrit-Corpora_xwalk-a2-dcs-parallels-qa-baseline_14.09.26](https://github.com/gasyoun/Uprava/blob/main/handoffs/H4707-OxAlpha_Parallel-Sanskrit-Corpora_xwalk-a2-dcs-parallels-qa-baseline_14.09.26.md) · **Executor:** OxAlpha (opencode/z-ai/glm-5.3-flash) · **Census A2** consumer candidate of kosha dataset [`dcs-parallel-passages-full`](https://github.com/gasyoun/kosha/blob/main/data/manifest/datasets.json).

## Mission

Consume `dcs-parallel-passages-full` (DCS parallel-passage alignments, full-size export, CC BY-SA 4.0) as the alignment QA / recall baseline for the parallel-corpora programme of this repository. Deliverables: baseline comparison report (this file) + joined metrics file; recall verified on a frozen sample; edge registered.

## Source & method

- **Input:** VisualDCS [`derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye/`](https://github.com/gasyoun/VisualDCS/tree/main/derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye) — 245 CSVs, one per DCS source-passage id (`<text_id>_<seg_lo>--<seg_hi>.csv`); headerless, `;`-separated, one physical line per source segment; per match: `[tgt_label, tgt_text, verdict, delta?]` with GOOD (verified full match) / PARTLY (partial, term delta like `+ buddha - abhinand`).
- **Builder:** [`tools/build_baseline.py`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/tools/build_baseline.py) — stdlib-only, deterministic (frozen sample seeded `4707`); label-anchored parsing (the export omits some delta fields, which breaks fixed-width grouping — a new group starts wherever a field matches the `<Title>, N: N [N]` label pattern; negative segment ids and dotted chapter numbers in commentary labels are handled).
- **Comparison control:** the superseded 2022 snapshot [`PARA/Polnorazmernye-2022-archive/`](https://github.com/gasyoun/VisualDCS/tree/main/derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye-2022-archive) (flat `!` match flags), per the kosha registry note.

## Headline metrics (measured 15-09-2026)

| Metric | Value |
|---|---|
| Files parsed | 245 / 245 |
| Source segments (physical lines) | 501,231 (kosha registry `rows: 506,787` counts raw file lines incl. ~5.5k blanks — segment count is the precise figure) |
| Candidate parallel matches | **154,033** |
| GOOD (verified full) | 14,557 (9.45%) |
| PARTLY (partial, term delta) | 139,476 (90.55%) |
| Malformed lines | **0** |
| Distinct source works | 145 |
| Distinct target works | 447 |
| Control: 2022-archive unique pair hashes | 115,889 |

## Recall on the frozen sample (verification)

Frozen sample: 200 matches, round-robin over a seeded-shuffled file list (seed 4707), committed at [`data/dcs-parallels-baseline/frozen_sample.csv`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/data/dcs-parallels-baseline/frozen_sample.csv).

| Probe | Result |
|---|---|
| Parser round-trip recall (each frozen match re-found identically by a fresh parse) | **200/200 = 1.00** |
| Archive-overlap recall (frozen pairs also present in the 2022 snapshot, normalized text-pair identity) | **197/200 = 0.985** |
| Hand verification (3 sampled rows re-read against raw CSV bytes: src/tgt text, label, verdict) | 3/3 confirmed |

Re-verify any time:

```
python3 tools/build_baseline.py            # rebuild (PASS required)
python3 tools/build_baseline.py --check    # frozen-sample recall (PASS required)
```

The 3 archive misses are expected drift: the live export carries richer verdicts (GOOD/PARTLY + term deltas) than the 2022 `!`-flag snapshot; some pairs were re-adjudicated between snapshots.

## Baseline usage contract (for future parallel-corpora work)

- **Gold set:** the 14,557 GOOD pairs are the verified-parallel reference set for alignment recall measurement: `recall = |system parallels ∩ GOOD baseline pairs| / |GOOD baseline pairs|`, pair identity = normalized (source_text, target_text) as in `pair_hash()` of the builder.
- **Joined metrics:** [`data/dcs-parallels-baseline/baseline_metrics.csv`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/data/dcs-parallels-baseline/baseline_metrics.csv) — one row per source CSV (dcs_text_id, segments, matches, verdict split, distinct target works, source work title); [`data/dcs-parallels-baseline/baseline_summary.json`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/data/dcs-parallels-baseline/baseline_summary.json) — global rollup + frozen-sample recall numbers.
- The full 59 MB dataset itself stays in VisualDCS (git-tracked there); this repo commits only the small derived baseline artifacts (~60 KB).

## Changed / Unchanged / Checks / Risks / Inspect

- **Changed:** new `tools/build_baseline.py` + `data/dcs-parallels-baseline/` (metrics CSV, summary JSON, frozen sample) + this report; README gains a real content section; CHANGELOG started. Edge registered: `VisualDCS → Parallel-Sanskrit-Corpora` in [Uprava interlinks_edges.tsv](https://github.com/gasyoun/Uprava/blob/main/interlinks_edges.tsv); kosha dataset row flips to consumed.
- **Unchanged:** VisualDCS dataset files (read-only consumption); kosha registry row identity; the 2022 archive (untouched control).
- **Checks:** `python3 tools/build_baseline.py` → PASS (0 malformed, verdicts clean); `python3 tools/build_baseline.py --check` → PASS (round-trip 1.00).
- **Risks:** export is a pre-2026 dump with irregular group widths (handled label-anchored, 0 residual malformed); GOOD/PARTLY verdicts are machine-derived from the original DCS alignment tooling, not human gold — treat GOOD as weak gold until a human spot-check wave; ~447 target works include commentary sub-labels joined under their base title.
- **Inspect:** open `baseline_summary.json` first, then `frozen_sample.csv` rows vs `VisualDCS/…/Polnorazmernye/<file>` line `line_no`.

_Гасунс_
