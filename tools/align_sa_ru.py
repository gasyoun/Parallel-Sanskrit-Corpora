#!/usr/bin/env python3
"""SA-RU sentence alignment over SamudraManthanam verse-aligned JSONL (H6070).

Task: flatten the verse-aligned corpus into two ordered sentence streams
(Sanskrit sentences by daṇḍa, Russian sentences by punctuation), run the
monotonic aligner, and score against the verse-group gold: a predicted pair
is correct iff both sides come from the same verse group.

Input: one or more canonical-JSONL files (rows id/work/passage/seg/lang/text;
verse group = rows sharing `group`, one seg=sa + one seg=ru row each).

Usage:
    python3 tools/align_sa_ru.py <corpus.jsonl...> [--out DIR] [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_sentences as al  # noqa: E402
from sandhi_tokenize import sentences_sa, tokenize  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "data" / "sa-ru-alignment"


def load_streams(jsonl_paths: list[Path]):
    """(sa_sents, ru_sents, gold_pairs) — flattened streams + same-group gold."""
    sa_sents: list[str] = []
    ru_sents: list[str] = []
    gold: set[tuple[int, int]] = set()
    for path in jsonl_paths:
        groups: dict[str, dict[str, dict]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            groups.setdefault(row["group"], {})[row["seg"]] = row
        for gname in groups:  # insertion order = reading order
            g = groups[gname]
            sa_row, ru_row = g.get("sa"), g.get("ru")
            if not sa_row or not ru_row:
                continue
            sa_parts = sentences_sa(sa_row["text"])
            ru_parts = al.sentences_ru(ru_row["text"])
            i0, j0 = len(sa_sents), len(ru_sents)
            for p in sa_parts:
                sa_sents.append(p)
            for p in ru_parts:
                ru_sents.append(p)
            for i in range(i0, len(sa_sents)):
                for j in range(j0, len(ru_sents)):
                    gold.add((i, j))
    return sa_sents, ru_sents, gold


def evaluate(sa_sents, ru_sents, gold, max_merge=2):
    sa_tok = [tokenize(s) for s in sa_sents]
    blocks = al.align(sa_tok, ru_sents, max_merge=max_merge)
    pred = {(i, j) for sa_is, ru_is in blocks
            for i in sa_is for j in ru_is}
    tp = len(pred & gold)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall else 0.0)
    # accuracy per mission goal: share of predicted PAIRS that are correct
    return {"pairs_predicted": len(pred), "pairs_gold": len(gold),
            "pairs_correct": tp, "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4),
            "accuracy": round(precision, 4), "max_merge": max_merge,
            "n_sa_sentences": len(sa_sents),
            "n_ru_sentences": len(ru_sents)}, blocks


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true",
                    help="re-run and compare against the frozen summary")
    args = ap.parse_args()

    sa_sents, ru_sents, gold = load_streams(args.corpus)
    metrics, blocks = evaluate(sa_sents, ru_sents, gold)

    summary_path = args.out / "summary.json"
    if args.check:
        frozen = json.loads(summary_path.read_text(encoding="utf-8"))
        if frozen == metrics:
            print("CHECK PASS — metrics identical to frozen summary")
            return 0
        print(f"CHECK FAIL\n  frozen : {frozen}\n  now    : {metrics}")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    pred_path = args.out / "predictions.csv"
    with open(pred_path, "w", encoding="utf-8") as fh:
        fh.write("sa_idx,ru_idx,sa_text,ru_text,in_gold\n")
        for sa_is, ru_is in blocks:
            for i in sa_is:
                for j in ru_is:
                    ok = "1" if (i, j) in gold else "0"
                    fh.write(f'{i},{j},"{sa_sents[i][:80]}","'
                             f'{ru_sents[j][:80]}",{ok}\n')
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"wrote {pred_path} and {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
