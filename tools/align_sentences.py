#!/usr/bin/env python3
"""Monotonic sentence aligner with a transliteration bridge (H6070).

Aligns two ordered sentence streams (Sanskrit IAST vs Russian Cyrillic) by
dynamic programming over merge blocks 1:1, 1:2, 2:1, 2:2 plus skips (0:1,
1:0). The two scripts share no characters, so lexical similarity comes from
an IAST→Cyrillic transliteration of proper names and loan shapes
(dhṛtarāṣṭra → дхритараштра ↔ «Дхритараштра») combined with a Gale-Church
style sentence-length log-ratio. Deterministic: no randomness, no network.

Score of a block = w_lex * lexical_overlap + w_len * length_fit - skip_cost,
maximised over the whole grid by DP.
"""
from __future__ import annotations

import math
import re
import unicodedata

# --- IAST → Cyrillic: the anchor bridge (approximate, names-first) ---------
_TRANS = [
    ("kh", "кх"), ("gh", "гх"), ("ch", "чх"), ("jh", "джх"), ("ṭh", "тх"),
    ("ḍh", "дх"), ("th", "тх"), ("dh", "дх"), ("ph", "пх"), ("bh", "бх"),
    ("kṣ", "кш"), ("jñ", "джн"), ("ai", "ай"), ("au", "ау"), ("ṛ", "ри"),
    ("ṝ", "ри"), ("ḷ", "л"), ("ā", "а"), ("ī", "и"), ("ū", "у"),
    ("a", "а"), ("i", "и"), ("u", "у"), ("e", "е"), ("o", "о"),
    ("k", "к"), ("g", "г"), ("ṅ", "н"), ("c", "ч"), ("j", "дж"), ("ñ", "нь"),
    ("ṭ", "т"), ("ḍ", "д"), ("ṇ", "н"), ("t", "т"), ("d", "д"), ("n", "н"),
    ("p", "п"), ("b", "б"), ("m", "м"), ("y", "й"), ("r", "р"), ("l", "л"),
    ("v", "в"), ("ś", "ш"), ("ṣ", "ш"), ("s", "с"), ("h", "х"),
    ("ṃ", "м"), ("ḥ", "х"),
]

_RU_STRIP = "«»\"'()[]?!,:;0123456789—–"
_RU_SPLIT = re.compile(r"[\s,;:!?«»()]+")
_LENS = 1.0  # Gale-Church style scale for the length term


def transliterate_iast(token: str) -> str:
    out = []
    i = 0
    t = unicodedata.normalize("NFC", token).casefold()
    while i < len(t):
        for src, dst in _TRANS:
            if t.startswith(src, i):
                out.append(dst)
                i += len(src)
                break
        else:
            i += 1  # unknown char (shouldn't happen in IAST) — drop
    return "".join(out)


def ru_tokens(sentence: str) -> set[str]:
    toks = set()
    for raw in _RU_SPLIT.split(
        unicodedata.normalize("NFC", sentence).casefold().translate(
            str.maketrans("", "", _RU_STRIP))
    ):
        if len(raw) >= 4:
            toks.add(raw)
    return toks


_RU_SENT_RE = re.compile(r"[.!?…]+[»\)]?\s*")


def sentences_ru(text: str) -> list[str]:
    """RU sentence spans for alignment — sentence-final punctuation only
    (commas stay inside sentences; verse-internal commas are the norm)."""
    parts = [p.strip(" «»\t") for p in _RU_SENT_RE.split(
        unicodedata.normalize("NFC", text))]
    return [p for p in parts if p]


def lexical_overlap(sa_tokens: list[str], ru_sentence: str) -> float:
    """Jaccard of transliterated SA content tokens vs RU content tokens."""
    ru = ru_tokens(ru_sentence)
    if not ru:
        return 0.0
    sa_t = {transliterate_iast(t) for t in sa_tokens if len(t) >= 3}
    if not sa_t:
        return 0.0
    # fuzzy containment: a translit token counts as shared when one side
    # contains the other (Russian renderings truncate/extend endings)
    shared = 0
    for s in sa_t:
        for r in ru:
            if s in r or r in s:
                shared += 1
                break
    return shared / len(sa_t | ru)


def length_fit(n_sa: int, n_ru: int) -> float:
    """Gaussian log-ratio score: 1.0 when lengths match, decaying otherwise."""
    if n_sa == 0 or n_ru == 0:
        return -1.0
    z = math.log((n_sa + 1) / (n_ru + 1)) / _LENS
    return math.exp(-0.5 * z * z)


def align(sa: list[list[str]], ru: list[str], ru_raw: list[str] | None = None,
          w_lex: float = 1.0, w_len: float = 1.0, skip_cost: float = 0.05,
          max_merge: int = 2) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    """Monotonic DP alignment. `sa` = pre-tokenized SA sentences; `ru` = RU
    sentence strings. Returns blocks ((sa_idx, ...), (ru_idx, ...)) covering
    every index exactly once (skips appear as an empty opposite side)."""
    ru_raw = ru_raw or ru
    n, m = len(sa), len(ru)

    def block_score(sa_is: tuple[int, ...], ru_is: tuple[int, ...]) -> float:
        toks = [t for i in sa_is for t in sa[i]]
        text = " ".join(ru_raw[i] for i in ru_is)
        return (w_lex * lexical_overlap(toks, text)
                + w_len * length_fit(sum(len(sa[i]) for i in sa_is),
                                     sum(len(ru_raw[i].split()) for i in ru_is)))

    # dp[i][j] = best score aligning sa[:i] with ru[:j]
    NEG = -1e9
    dp = [[NEG] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple[int, int, tuple[int, ...], tuple[int, ...]]]] = [
        [None] * (m + 1) for _ in range(n + 1)]  # type: ignore[assignment]
    dp[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            cur = dp[i][j]
            if cur == NEG:
                continue
            for a in range(1, max_merge + 1):  # merge sizes on SA side
                for b in range(1, max_merge + 1):  # on RU side
                    if i + a > n or j + b > m:
                        continue
                    s = cur + block_score(tuple(range(i, i + a)),
                                          tuple(range(j, j + b)))
                    if s > dp[i + a][j + b]:
                        dp[i + a][j + b] = s
                        back[i + a][j + b] = (i, j, tuple(range(i, i + a)),
                                             tuple(range(j, j + b)))
            if i < n and dp[i + 1][j] < cur - skip_cost:  # SA-only
                dp[i + 1][j] = cur - skip_cost
                back[i + 1][j] = (i, j, (i,), ())
            if j < m and dp[i][j + 1] < cur - skip_cost:  # RU-only
                dp[i][j + 1] = cur - skip_cost
                back[i][j + 1] = (i, j, (), (j,))

    blocks: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    i, j = n, m
    while (i, j) != (0, 0):
        pi, pj, sa_is, ru_is = back[i][j]
        blocks.append((sa_is, ru_is))
        i, j = pi, pj
    blocks.reverse()
    return blocks
