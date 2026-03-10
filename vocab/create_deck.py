#!/usr/bin/env python3
"""
Creates an Anki deck from the Total Vocab.md Obsidian note.

Each card:
  Front: Spanish word / phrase
  Back:  Example sentence with the vocab word highlighted

Usage:
    python3 create_deck.py            # full deck  -> spanish_vocab.apkg
    python3 create_deck.py --preview  # 1 card     -> spanish_preview.apkg

Requirements:
    pip3 install genanki
"""

import re
import sys
import genanki

VOCAB_FILE     = "/Users/lillianpetersen/Library/Mobile Documents/iCloud~md~obsidian/Documents/Spanish/Total Vocab.md"
OUTPUT_FULL    = "spanish_vocab.apkg"
OUTPUT_PREVIEW = "spanish_preview.apkg"

DECK_ID  = 2034561890
MODEL_ID = 2034561892  # bumped so Anki treats this as a new model

CARD_FRONT = """\
<div style="font-family: Arial, sans-serif; text-align: center; padding: 40px 20px;">
  <div style="font-size: 32px; font-weight: bold; color: #1a1a1a;">{{Spanish}}</div>
</div>
"""

CARD_BACK = """\
<div style="font-family: Arial, sans-serif; text-align: center; padding: 30px 20px; max-width: 640px; margin: auto;">
  <div style="font-size: 28px; font-weight: bold; color: #1a1a1a; margin-bottom: 24px;">{{Spanish}}</div>
  <div style="font-size: 20px; color: #444; line-height: 1.7;">{{Sentence}}</div>
</div>
"""

HIGHLIGHT = '<span style="font-weight: bold; color: #2e86c1; text-decoration: underline;">{}</span>'


def highlight_vocab(sentence, vocab):
    """Bold + color the vocab word/phrase wherever it appears in the sentence."""
    # Strip parenthetical hints like "(me ponga al día)" from the vocab key
    key = re.split(r"\s*[\(\[]", vocab)[0].strip()
    if not key:
        return sentence
    highlighted = re.sub(
        re.escape(key),
        lambda m: HIGHLIGHT.format(m.group()),
        sentence,
        flags=re.IGNORECASE,
    )
    return highlighted


def parse_vocab(filepath):
    entries = []
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[2:]:          # skip header row and separator row
        line = line.strip()
        if not line.startswith("|"):
            break
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 3:
            spanish, _, example = parts[0], parts[1], parts[2]
            sentence = highlight_vocab(example, spanish)
            entries.append((spanish, sentence))
    return entries


def build_deck(entries, deck_name):
    model = genanki.Model(
        MODEL_ID,
        "Spanish Vocab",
        fields=[
            {"name": "Spanish"},
            {"name": "Sentence"},
        ],
        templates=[
            {
                "name": "Spanish → Sentence",
                "qfmt": CARD_FRONT,
                "afmt": CARD_BACK,
            }
        ],
        css=".card { background-color: #fafafa; }",
    )

    deck = genanki.Deck(DECK_ID, deck_name)
    for spanish, sentence in entries:
        deck.add_note(genanki.Note(model=model, fields=[spanish, sentence]))
    return deck


def main():
    preview = "--preview" in sys.argv

    entries = parse_vocab(VOCAB_FILE)
    if not entries:
        raise SystemExit("No entries found — check the vocab file path.")

    if preview:
        entries = entries[:1]
        output = OUTPUT_PREVIEW
        deck_name = "Spanish Vocab (Preview)"
    else:
        output = OUTPUT_FULL
        deck_name = "Spanish Vocab"

    deck = build_deck(entries, deck_name)
    genanki.Package(deck).write_to_file(output)

    print(f"Created {len(deck.notes)} card(s) → {output}")
    if preview:
        sp, sentence = entries[0]
        print(f"\n  FRONT: {sp}")
        print(f"  BACK:  {sentence}")
        print("\nImport into Anki: File > Import")


if __name__ == "__main__":
    main()
