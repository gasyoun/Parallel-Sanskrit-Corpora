#!/usr/bin/env python3
"""Tests for the H6070 SA-RU aligner parts — pure, no network, no siblings.

Run: python3 tests/test_aligner.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import align_sentences as al  # noqa: E402
from sandhi_tokenize import sentences_sa, tokenize  # noqa: E402

FAILS: list[str] = []


def check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'} :: {name}")
    if not cond:
        FAILS.append(name)


def test_transliteration():
    check("dhṛtarāṣṭra", al.transliterate_iast("dhṛtarāṣṭra") == "дхритараштра")
    check("kurukṣetra", al.transliterate_iast("kurukṣetra") == "курукшетра")
    check("sañjaya", al.transliterate_iast("sañjaya") == "саньджайа")
    check("pāṇḍava", al.transliterate_iast("pāṇḍava") == "пандава")


def test_tokenizer():
    toks = tokenize("Dharmakṣetre kurukṣetre samavetā yuyutsavaḥ")
    check("lowercased", "dharmakṣetre" in toks)
    check("clitic split", "ca" in tokenize("dharmakṣetreca"))
    sents = sentences_sa(
        "dhṛtarāṣṭra uvāca । dharmakṣetre kurukṣetre ॥ BhG 1.1॥")
    check("danda split", len(sents) == 2)
    check("label dropped", all("BhG" not in s for s in sents))


def test_lexical_bridge():
    s = al.lexical_overlap(tokenize("dhṛtarāṣṭra uvāca"),
                           "Дхритараштра сказал: «О Санджая!")
    check("name bridges scripts", s >= 0.25)


def test_dp_micro():
    """Three pādas + two RU sentences in order — the canonical verse shape."""
    sa = [tokenize(t) for t in [
        "dhṛtarāṣṭra uvāca",
        "dharmakṣetre kurukṣetre samavetā yuyutsavaḥ",
        "māmakāḥ pāṇḍavāścaiva kimakurvata sañjaya",
    ]]
    ru = ["Дхритараштра сказал: «О Санджая!",
          "Что сделали в жажде войны мои сыновья и сыновья Панду?"]
    blocks = al.align(sa, ru)
    # expected: (0,)↔(0,), (1,2)↔(1,) — merge block absorbs the pāda pair
    shape = [(a, b) for a, b in blocks if a and b]
    check("two blocks", len(shape) == 2)
    check("merge block present", any(len(a) == 2 for a, b in shape))
    check("no cross order", shape[0][0][0] == 0 and shape[0][1][0] == 0)


def test_eval_harness():
    """Group-derived gold on a synthetic two-verse stream."""
    fixture = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / \
        "bhagavadgita_sample60.jsonl"
    if not fixture.is_file():
        check("fixture present (skipped)", True)
        return
    import align_sa_ru as A
    sa, ru, gold = A.load_streams([fixture])
    check("streams non-empty", len(sa) > 50 and len(ru) > 50)
    check("gold cross-product sane", 0 < len(gold) < len(sa) * len(ru))


def main() -> int:
    test_transliteration()
    test_tokenizer()
    test_lexical_bridge()
    test_dp_micro()
    test_eval_harness()
    if FAILS:
        print(f"\n{len(FAILS)} FAILED: {FAILS}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
