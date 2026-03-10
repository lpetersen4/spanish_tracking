#!/usr/bin/env python3
"""
Process Spanish class notes: generate example sentences, update Total Vocab.md,
and create an Anki deck with only the new cards.

Usage:
    python3 process_class_notes.py                     # process all unprocessed notes (default)
    python3 process_class_notes.py "03.09.2026.md"    # process a specific note
    python3 process_class_notes.py --all              # reprocess all notes (re-checks for new vocab)

Processed notes are tracked in processed_notes.txt so they are not re-run next time.

Requirements:
    pip3 install genanki
    claude CLI must be installed and authenticated
"""

import re
import sys
import subprocess
import genanki
import hashlib
from pathlib import Path

VAULT = Path("/Users/lillianpetersen/Library/Mobile Documents/iCloud~md~obsidian/Documents/Spanish")
CLASS_NOTES_DIR = VAULT / "Class Notes"
TOTAL_VOCAB_FILE = VAULT / "Total Vocab.md"
OUTPUT_DIR = Path("/Users/lillianpetersen/spanish-vocab")

DECK_ID  = 2034561890
MODEL_ID = 2034561892
PROCESSED_FILE = OUTPUT_DIR / "processed_notes.txt"


# ── Card templates ────────────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def note_id_for(word: str) -> int:
    """Stable numeric ID derived from the Spanish word."""
    return int(hashlib.md5(word.lower().encode()).hexdigest(), 16) % (10**10)


def highlight_vocab(sentence: str, vocab: str) -> str:
    key = re.split(r"\s*[\(\[]", vocab)[0].strip()
    if not key:
        return sentence
    return re.sub(
        re.escape(key),
        lambda m: HIGHLIGHT.format(m.group()),
        sentence,
        flags=re.IGNORECASE,
    )


def load_processed_notes(filepath: Path) -> set[str]:
    """Return set of already-processed note filenames."""
    if not filepath.exists():
        return set()
    return {line.strip() for line in filepath.read_text().splitlines() if line.strip()}


def mark_note_processed(filepath: Path, note_name: str) -> None:
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(note_name + "\n")


def load_existing_vocab(filepath: Path) -> set[str]:
    """Return a set of lowercase Spanish words already in Total Vocab.md."""
    existing = set()
    if not filepath.exists():
        return existing
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines[2:]:  # skip header + separator
        line = line.strip()
        if not line.startswith("|"):
            break
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if parts:
            existing.add(parts[0].lower())
    return existing


def parse_class_note(filepath: Path) -> list[tuple[str, str]]:
    """Return list of (vocab, translation) from a class note table."""
    entries = []
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    in_table = False
    past_header = False
    for line in lines:
        line = line.strip()
        if not line:
            if in_table:
                break
            continue
        if line.startswith("|") and "Vocab" in line and "Translation" in line:
            in_table = True
            continue
        if in_table and not past_header:
            past_header = True  # skip separator row
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                entries.append((parts[0], parts[1]))
    return entries


def generate_sentence(vocab: str, translation: str) -> str:
    """Use the claude CLI to generate a natural example sentence."""
    prompt = (
        f"Generate one short, natural Spanish example sentence using the word or phrase \"{vocab}\" "
        f"(meaning: {translation}). "
        "The learner is B2 level and focused on Argentine Spanish — use River Plate dialect, vos instead of tú, and Argentine vocabulary and phrasing where natural. "
        "Reply with ONLY the sentence, nothing else — no explanation, no translation, no quotes."
    )
    try:
        # Unset CLAUDECODE so the CLI can run outside of a Claude Code session
        import os
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku"],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        sentence = result.stdout.strip()
        if sentence:
            return sentence
        if result.stderr.strip():
            print(f"    [claude error]: {result.stderr.strip()[:120]}")
    except subprocess.TimeoutExpired:
        print(f"    [timeout generating sentence for '{vocab}']")
    except FileNotFoundError:
        print("    [claude CLI not found — install it or add to PATH]")
    return ""


def append_to_total_vocab(filepath: Path, new_entries: list[tuple[str, str, str]]) -> None:
    """Append new (vocab, translation, sentence) rows to Total Vocab.md."""
    with open(filepath, "a", encoding="utf-8") as f:
        for vocab, translation, sentence in new_entries:
            # Pad columns to match existing style (rough alignment)
            f.write(f"| {vocab:<43} | {translation:<59} | {sentence:<80} |\n")


def build_anki_deck(new_entries: list[tuple[str, str, str]], deck_name: str) -> genanki.Deck:
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
    for vocab, _translation, sentence in new_entries:
        highlighted = highlight_vocab(sentence, vocab)
        note = genanki.Note(
            model=model,
            fields=[vocab, highlighted],
            guid=note_id_for(vocab),
        )
        deck.add_note(note)
    return deck


# ── Main ──────────────────────────────────────────────────────────────────────

def process_note(note_path: Path, existing_vocab: set[str]) -> list[tuple[str, str, str]]:
    """Process one class note, return list of new (vocab, translation, sentence) added."""
    print(f"\nProcessing: {note_path.name}")
    raw_entries = parse_class_note(note_path)
    if not raw_entries:
        print("  No vocab table found.")
        return []

    new_entries = []
    skipped = []
    for vocab, translation in raw_entries:
        if vocab.lower() in existing_vocab:
            skipped.append(vocab)
            continue
        print(f"  Generating sentence for: {vocab}")
        sentence = generate_sentence(vocab, translation)
        if not sentence:
            print(f"    [skipping '{vocab}' — could not generate sentence]")
            continue
        new_entries.append((vocab, translation, sentence))
        existing_vocab.add(vocab.lower())

    if skipped:
        print(f"  Skipped (already in Total Vocab): {', '.join(skipped)}")
    return new_entries


def main():
    args = sys.argv[1:]
    process_all = "--all" in args
    args = [a for a in args if a != "--all"]

    all_notes = sorted(CLASS_NOTES_DIR.glob("*.md"))
    if not all_notes:
        raise SystemExit("No class notes found in Class Notes/")

    processed = load_processed_notes(PROCESSED_FILE)

    # Determine which notes to process
    if args:
        note_files = [CLASS_NOTES_DIR / a for a in args]
    elif process_all:
        note_files = all_notes
    else:
        # Default: all notes not yet processed
        note_files = [n for n in all_notes if n.name not in processed]
        if not note_files:
            print("All class notes have already been processed. Use --all to reprocess.")
            return

    # Load existing vocab to avoid duplicates
    existing_vocab = load_existing_vocab(TOTAL_VOCAB_FILE)
    print(f"Loaded {len(existing_vocab)} existing vocab words from Total Vocab.md")
    print(f"Notes to process: {[n.name for n in note_files]}")

    # Process each note
    all_new: list[tuple[str, str, str]] = []
    for note_path in note_files:
        if not note_path.exists():
            print(f"Warning: {note_path} not found, skipping.")
            continue
        new_entries = process_note(note_path, existing_vocab)
        all_new.extend(new_entries)
        if not process_all:
            mark_note_processed(PROCESSED_FILE, note_path.name)

    if not all_new:
        print("\nNo new vocab words to add.")
        return

    # Append to Total Vocab.md
    append_to_total_vocab(TOTAL_VOCAB_FILE, all_new)
    print(f"\nAdded {len(all_new)} new word(s) to Total Vocab.md")

    # Create Anki deck with new cards only
    output_path = OUTPUT_DIR / "spanish_new_cards.apkg"
    deck = build_anki_deck(all_new, "Spanish Vocab")
    genanki.Package(deck).write_to_file(str(output_path))
    print(f"Created Anki deck ({len(all_new)} card(s)) → {output_path}")
    print("\nImport into Anki: File > Import")

    # Summary
    print("\nNew words added:")
    for vocab, translation, sentence in all_new:
        print(f"  • {vocab} — {translation}")
        print(f"    {sentence}")


if __name__ == "__main__":
    main()
