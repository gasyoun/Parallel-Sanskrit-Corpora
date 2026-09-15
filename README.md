# Parallel-Sanskrit-Corpora

_Created: 14-06-2026 · Last updated: 15-09-2026_

Parallel Sanskrit corpora aligned with European-language translations.

## Status — first derived layer landed (H4707)

The repository now holds its **first derived content**: the DCS parallel-passage
QA/recall baseline (kosha dataset `dcs-parallel-passages-full`, census consumer A2):

- [`H4707_DCS_PARALLELS_QA_BASELINE_15-09-2026.md`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/H4707_DCS_PARALLELS_QA_BASELINE_15-09-2026.md) — baseline comparison report (154,033 candidate parallels across 245 DCS source files; GOOD 14,557 / PARTLY 139,476; recall verified on a frozen 200-row sample).
- [`tools/build_baseline.py`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/tools/build_baseline.py) — deterministic builder (`python3 tools/build_baseline.py` to rebuild, `--check` to re-verify the frozen sample).
- [`data/dcs-parallels-baseline/`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/tree/master/data/dcs-parallels-baseline) — joined metrics CSV + summary JSON + frozen sample.

The 59 MB source dataset lives in
[`VisualDCS/…/PARA/Polnorazmernye/`](https://github.com/gasyoun/VisualDCS/tree/main/derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye);
only small derived artifacts are committed here. Sentence-/verse-aligned
Sanskrit↔European-language corpus data is still to come; the GOOD baseline
pairs are the recall reference set for that future alignment work.

## Repository scaffolding

- [`LICENSE`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/LICENSE) — MIT License, © 2019 Mārcis Gasūns.
- [`.github/dependabot.yml`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/.github/dependabot.yml) — Dependabot configuration.
- [`.github/workflows/dependabot-auto-merge.yml`](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/.github/workflows/dependabot-auto-merge.yml) — auto-merge workflow for Dependabot PRs.

## Intended scope

The repository is reserved for **sentence- or verse-aligned Sanskrit source text paired
with translations into European languages** (parallel/bitext corpora suitable for
alignment, translation-studies, and lexicographic work). When data lands here, this
README will document the corpus sources, alignment format, and per-language coverage.

## Related repositories

Sanskrit corpus and parallel-text work in the wider [`gasyoun`](https://github.com/gasyoun)
and [`sanskrit-lexicon`](https://github.com/sanskrit-lexicon) ecosystem that this
repository is intended to complement:

- [`SanskritCorpora`](https://github.com/gasyoun/SanskritCorpora)
- [`SanskritRussian`](https://github.com/gasyoun/SanskritRussian)
- [`dcs-conllu`](https://github.com/gasyoun/dcs-conllu)
- [`spoken-sanskrit-corpus`](https://github.com/gasyoun/spoken-sanskrit-corpus)
- [`telegram-sanskrit-corpus`](https://github.com/gasyoun/telegram-sanskrit-corpus)
- [`SanskritLexicography`](https://github.com/gasyoun/SanskritLexicography) — the Russian-translation and lexicography research workspace.

## License

Released under the [MIT License](https://github.com/gasyoun/Parallel-Sanskrit-Corpora/blob/master/LICENSE).

_Dr. Mārcis Gasūns_
