#!/usr/bin/env python3
"""Sandhi-aware IAST tokenizer for SA-RU sentence alignment (H6070).

Splits Sanskrit (IAST) text into alignment tokens: Unicode-NFC, lowercased,
daṇḍa/avagraha/punctuation stripped, and the high-frequency enclitic/sandhi
fusions (ca, eva, na, va, hi, sma) split off where they are glued to a host
word by sandhi. The splitter is deliberately conservative — it only separates
a clitic when the remainder is a plausible standalone word (>=2 chars) —
because alignment scoring consumes the tokens as a bag: a missed split costs
one shared token, a wrong split corrupts both sides. Character-level sandhi
(the vowel/consonant fusion itself) is NOT undone here; the scorer's
transliteration bridge plus char-level fuzz absorbs it.

CLI: python3 tools/sandhi_tokenize.py < text  (one token per line)
"""
from __future__ import annotations

import re
import sys
import unicodedata

CLITICS = ("ca", "eva", "na", "va", "hi", "sma")
# Sandhi shape a host+clitic fusion can take at the seam: the clitic may lose
# its initial vowel (c' after -o/-a: "kurukṣetre ca" vs "māmakāś ca").
_SEAM = {
    "ca": ("c", "ca", "cca"),
    "eva": ("ev", "eva"),
    "na": ("n", "na"),
    "va": ("v", "va"),
    "hi": ("h", "hi"),
    "sma": ("sm", "sma"),
}
_SPLIT_RE = re.compile(r"[\s,;:!?'\"()\[\]0-9–—-]+")
_STRIP = "।॥॰.'\"«»()[]?!,:;0123456789"


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def split_clitic(word: str) -> list[str]:
    """Split one sandhi-glued word into host + clitic where the shape fits."""
    for clit in CLITICS:
        for seam in _SEAM[clit]:
            for vowel in ("a", "ā", "i", "ī", "u", "ū", "e", "o"):
                suffix = vowel + clit if seam == clit[0] else seam
                if word.endswith(suffix) and len(word) - len(suffix) >= 2:
                    host = word[: len(word) - len(suffix)]
                    return [host, clit]
    return [word]


def tokenize(text: str) -> list[str]:
    """Alignment tokens for an IAST sentence (normalized, clitic-split)."""
    out: list[str] = []
    for raw in _SPLIT_RE.split(normalize(text.translate(str.maketrans("", "", _STRIP)))):
        if not raw or raw in (".", ".."):
            continue
        out.extend(split_clitic(raw.strip("।॥")))
    return out


_LABEL_RE = re.compile(r"^[A-Za-z]{1,4}?\s*[\d\s.,:;-]*\d[\d\s.,:;-]*$")


def sentences_sa(text: str) -> list[str]:
    """Sentence spans by daṇḍa/double-daṇḍa, dropping verse-label junk
    (e.g. the trailing 'BhG 1.1' source stamp — ASCII, no IAST diacritics)."""
    parts = [p.strip() for p in re.split(r"[।॥]+", text) if p.strip()]
    kept = [p for p in parts
            if not _LABEL_RE.match(p) and p.strip(". ")]
    return kept or ([text.strip()] if text.strip() else [])


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        for tok in tokenize(line):
            sys.stdout.write(tok + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
