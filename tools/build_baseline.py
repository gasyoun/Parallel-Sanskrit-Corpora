#!/usr/bin/env python3
"""H4707 — DCS parallel-passage alignments as QA/recall baseline.

Consumes the kosha-registered dataset `dcs-parallel-passages-full`
(VisualDCS derived-data/Paralleli-v-tekstah-korpusa-SRC/PARA/Polnorazmernye/,
245 CSV files, one per DCS source-passage id) and emits, into
data/dcs-parallels-baseline/:

  baseline_metrics.csv   joined per-source-text metrics (segments, matches,
                         verdict distribution, distinct target works)
  baseline_summary.json  global rollup + frozen-sample recall numbers
  frozen_sample.csv      deterministic frozen sample of matches (seed 4707)
                         — the recall probe set; re-check with --check

File format (headerless, ';' separated, one physical line per source
segment): [src_label, src_seg, src_text] then repeated 4-field groups
[tgt_label, tgt_text, verdict, delta].  Live export verdicts: GOOD / PARTLY
(+ term delta); the superseded PARA/Polnorazmernye-2022-archive/ snapshot
uses a flat '!' flag.

Usage:
  python3 tools/build_baseline.py            # build baseline artifacts
  python3 tools/build_baseline.py --check    # recompute frozen-sample recall
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VISUAL_DCS = REPO.parent / "VisualDCS"
LIVE_DIR = VISUAL_DCS / "derived-data" / "Paralleli-v-tekstah-korpusa-SRC" / "PARA" / "Polnorazmernye"
ARCHIVE_DIR = VISUAL_DCS / "derived-data" / "Paralleli-v-tekstah-korpusa-SRC" / "PARA" / "Polnorazmernye-2022-archive"
OUT_DIR = REPO / "data" / "dcs-parallels-baseline"

SAMPLE_N = 200
SEED = 4707

LABEL_RE = re.compile(r"^(.*),\s*(\d+(?:\.\d+)?):\s*(-?\d+)(?:\s+(-?\d+))?\s*$")


def norm_text(s: str) -> str:
    """Normalize a Sanskrit passage string for pair identity."""
    s = " ".join(s.split())
    return s.strip(" |").rstrip("|").strip()


def parse_label(label: str):
    """'Divyāvadāna Divyāv, 13: 13 1' -> ('Divyāvadāna Divyāv', '13', '13', 1)."""
    m = LABEL_RE.match(label.strip())
    if not m:
        return (label.strip(), None, None, None)
    title, work, chap, seg = m.group(1), m.group(2), m.group(3), m.group(4)
    return (title, work, chap, int(seg) if seg is not None else None)


def parse_file(path: Path):
    """Yield match dicts from one export CSV; return also per-file counters.

    The export is not perfectly regular: some match groups omit the trailing
    delta field, which shifts naive fixed-width grouping.  We therefore walk
    label-anchored: a new group starts wherever a field matches the
    '<Title>, N: N [N]' label pattern, and the remaining fields of the group
    are [tgt_text, verdict, delta?] with empties skipped between verdict and
    delta.
    """
    matches = []
    n_segments = 0
    n_malformed = 0
    with path.open(encoding="utf-8", newline="") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue
            fields = line.split(";")
            while fields and fields[-1] == "":
                fields.pop()
            if len(fields) < 3:
                n_malformed += 1
                continue
            src_label, src_seg, src_text = fields[0], fields[1], fields[2]
            n_segments += 1
            # source label must match the label pattern, else the line is junk
            if not LABEL_RE.match(src_label.strip()):
                n_malformed += 1
                continue
            # collect group starts: fields matching the target-label pattern
            starts = [i for i in range(3, len(fields)) if LABEL_RE.match(fields[i].strip())]
            for gi, start in enumerate(starts):
                end = starts[gi + 1] if gi + 1 < len(starts) else len(fields)
                body = [f for f in fields[start + 1 : end] if True]
                if not body:
                    n_malformed += 1
                    continue
                tgt_label = fields[start]
                tgt_text = body[0]
                verdict = body[1].strip() if len(body) > 1 else ""
                delta = body[2] if len(body) > 2 else ""
                if verdict == "" and len(body) > 2:
                    # [text, '', delta] shape — keep delta
                    delta = body[2]
                matches.append(
                    {
                        "file": path.name,
                        "line_no": line_no,
                        "src_label": src_label,
                        "src_seg": src_seg,
                        "src_text": src_text,
                        "tgt_label": tgt_label,
                        "tgt_text": tgt_text,
                        "verdict": verdict,
                        "delta": delta,
                    }
                )
    return matches, n_segments, n_malformed


def pair_hash(m) -> str:
    return hashlib.md5(
        (norm_text(m["src_text"]) + "\x00" + norm_text(m["tgt_text"])).encode("utf-8")
    ).hexdigest()


def load_live():
    files = sorted(LIVE_DIR.glob("*.csv"))
    all_matches = []
    per_file = {}
    for p in files:
        matches, n_seg, n_bad = parse_file(p)
        all_matches.extend(matches)
        verdicts = Counter(m["verdict"] for m in matches)
        tgt_titles = {parse_label(m["tgt_label"])[0] for m in matches}
        per_file[p.name] = {
            "file": p.name,
            "dcs_text_id": int(p.name.split("_", 1)[0]),
            "segments": n_seg,
            "matches": len(matches),
            "malformed_lines": n_bad,
            "verdict_good": verdicts.get("GOOD", 0),
            "verdict_partly": verdicts.get("PARTLY", 0),
            "verdict_other": sum(v for k, v in verdicts.items() if k not in ("GOOD", "PARTLY")),
            "distinct_target_works": len(tgt_titles),
            "src_title": parse_label(matches[0]["src_label"])[0] if matches else "",
        }
    return files, all_matches, per_file


def load_archive_pair_hashes():
    if not ARCHIVE_DIR.is_dir():
        return None
    hashes = set()
    for p in sorted(ARCHIVE_DIR.glob("*.csv")):
        matches, _, _ = parse_file(p)
        for m in matches:
            hashes.add(pair_hash(m))
    return hashes


def freeze_sample(all_matches):
    rng = random.Random(SEED)
    by_file = defaultdict(list)
    for idx, m in enumerate(all_matches):
        by_file[m["file"]].append(idx)
    file_order = sorted(by_file)
    rng.shuffle(file_order)
    picked, cursor = [], {f: 0 for f in file_order}
    # Round-robin over shuffled files: stratified, deterministic.
    while len(picked) < min(SAMPLE_N, len(all_matches)):
        progressed = False
        for f in file_order:
            if len(picked) >= SAMPLE_N:
                break
            idxs = by_file[f]
            if cursor[f] < len(idxs):
                picked.append(idxs[cursor[f]])
                cursor[f] += 1
                progressed = True
        if not progressed:
            break
    return [all_matches[i] for i in picked]


FIELDS = [
    "file", "line_no", "src_label", "src_seg", "src_text",
    "tgt_label", "tgt_text", "verdict", "delta",
]


def write_sample(path: Path, sample):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for m in sample:
            w.writerow({k: m[k] for k in FIELDS})


def recall_check(sample, archive_hashes):
    """Two-way recall on the frozen sample.

    parser_roundtrip: every frozen match is re-found identically by a fresh
    parse of its source file (baseline extraction recall).
    archive_overlap: frozen pairs whose normalized (src,tgt) text pair also
    exists in the superseded 2022 snapshot (drift/overlap recall).
    """
    roundtrip_hits = 0
    for m in sample:
        fresh, _, _ = parse_file(LIVE_DIR / m["file"])
        found = any(
            f["line_no"] == m["line_no"]
            and f["src_seg"] == m["src_seg"]
            and f["tgt_label"] == m["tgt_label"]
            and f["verdict"] == m["verdict"]
            for f in fresh
        )
        roundtrip_hits += 1 if found else 0
    arch_hits = 0
    if archive_hashes is not None:
        for m in sample:
            arch_hits += 1 if pair_hash(m) in archive_hashes else 0
    return {
        "sample_n": len(sample),
        "parser_roundtrip_recall": roundtrip_hits / len(sample) if sample else None,
        "parser_roundtrip_hits": roundtrip_hits,
        "archive_overlap_recall": (arch_hits / len(sample)) if (sample and archive_hashes is not None) else None,
        "archive_overlap_hits": arch_hits,
    }


def main() -> int:
    check_only = "--check" in sys.argv
    sample_path = OUT_DIR / "frozen_sample.csv"

    if check_only:
        if not sample_path.exists():
            print("FAIL: frozen_sample.csv missing — run without --check first")
            return 1
        with sample_path.open(encoding="utf-8", newline="") as fh:
            sample = list(csv.DictReader(fh))
        for m in sample:
            m["line_no"] = int(m["line_no"])
        archive_hashes = load_archive_pair_hashes()
        r = recall_check(sample, archive_hashes)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        ok = r["parser_roundtrip_recall"] == 1.0
        print(("PASS" if ok else "FAIL") + ": frozen-sample parser round-trip recall")
        return 0 if ok else 1

    if not LIVE_DIR.is_dir():
        print(f"FAIL: dataset dir missing: {LIVE_DIR}")
        return 1

    files, all_matches, per_file = load_live()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # joined metrics file: one row per source-passage CSV
    metrics_path = OUT_DIR / "baseline_metrics.csv"
    cols = list(next(iter(per_file.values())).keys())
    with metrics_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for name in sorted(per_file):
            w.writerow(per_file[name])

    sample = freeze_sample(all_matches)
    write_sample(sample_path, sample)

    archive_hashes = load_archive_pair_hashes()
    r = recall_check(sample, archive_hashes)

    verdicts = Counter(m["verdict"] for m in all_matches)
    src_titles = {v["src_title"] for v in per_file.values() if v["src_title"]}
    tgt_titles = {parse_label(m["tgt_label"])[0] for m in all_matches}
    summary = {
        "dataset_id": "dcs-parallel-passages-full",
        "handoff": "H4707",
        "generated": "15-09-2026",
        "source_dir": str(LIVE_DIR.relative_to(VISUAL_DCS)),
        "files": len(files),
        "source_segments": sum(v["segments"] for v in per_file.values()),
        "matches_total": len(all_matches),
        "verdicts": dict(verdicts),
        "distinct_source_works": len(src_titles),
        "distinct_target_works": len(tgt_titles),
        "malformed_lines": sum(v["malformed_lines"] for v in per_file.values()),
        "archive_dir": str(ARCHIVE_DIR.relative_to(VISUAL_DCS)) if ARCHIVE_DIR.is_dir() else None,
        "archive_pair_hashes": len(archive_hashes) if archive_hashes is not None else None,
        "frozen_sample": {"n": len(sample), "seed": SEED, "strategy": "round-robin over seeded-shuffled files"},
        "recall_on_frozen_sample": r,
    }
    (OUT_DIR / "baseline_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    ok = r["parser_roundtrip_recall"] == 1.0 and summary["malformed_lines"] == 0
    print(("PASS" if ok else "FAIL") + ": baseline build")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
