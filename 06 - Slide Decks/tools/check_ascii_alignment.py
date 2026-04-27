#!/usr/bin/env python3
"""Verify box-drawing alignment in HTML slide decks with ASCII art.

Usage:
    python check_ascii_alignment.py <file.html> [start_line] [end_line]

Strips HTML tags to get rendered text, then checks that all box-drawing
border characters (│ ┼ ┤ ├ ┌ ┐ └ ┘) fall on consistent column positions
across a range of lines.

If start/end lines are omitted, scans the entire file for blocks of
consecutive lines containing box-drawing characters.
"""
import re
import sys

BORDER_CHARS = set("│┼┤├┌┐└┘")


def strip_html(line):
    """Remove HTML tags and decode common entities → rendered text."""
    rendered = re.sub(r"<[^>]+>", "", line.rstrip("\n"))
    for ent, ch in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                     ("&middot;", "\u00b7"), ("&nbsp;", " ")]:
        rendered = rendered.replace(ent, ch)
    return rendered


def find_border_cols(rendered):
    """Return set of column positions that contain a border character."""
    return {j for j, ch in enumerate(rendered) if ch in BORDER_CHARS}


def detect_blocks(lines):
    """Find contiguous ranges of lines containing box-drawing chars."""
    blocks, start = [], None
    for i, line in enumerate(lines):
        has = any(ch in BORDER_CHARS for ch in strip_html(line))
        if has and start is None:
            start = i
        elif not has and start is not None:
            blocks.append((start, i - 1))
            start = None
    if start is not None:
        blocks.append((start, len(lines) - 1))
    return blocks


def check_block(lines, start, end):
    """Check alignment of a block of lines. Returns True if all OK."""
    # Collect ALL border positions across the block
    all_positions = set()
    per_line = {}
    for i in range(start, end + 1):
        rendered = strip_html(lines[i])
        cols = find_border_cols(rendered)
        per_line[i] = (rendered, cols)
        all_positions |= cols

    if not all_positions:
        return True

    # The "frame" columns are those that appear on the top/bottom borders
    # (first and last lines of the block).
    first_cols = per_line[start][1] if start in per_line else set()
    last_cols = per_line[end][1] if end in per_line else set()
    frame_cols = first_cols & last_cols  # columns present on both borders

    if not frame_cols:
        frame_cols = first_cols | last_cols

    ok = True
    print(f"\n--- Block: lines {start+1}-{end+1} ---")
    print(f"Frame columns: {sorted(frame_cols)}")
    print()

    for i in range(start, end + 1):
        rendered, cols = per_line[i]
        missing = frame_cols - cols
        extra = cols - frame_cols
        length = len(rendered)

        status = "\u2713" if not missing else f"MISSING cols {sorted(missing)}"
        extra_str = f"  (internal: {sorted(extra)})" if extra else ""
        print(f"  Line {i+1:4d} len={length:3d} {status}{extra_str}")

        if missing:
            ok = False

    return ok


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = sys.argv[1]
    with open(path) as f:
        lines = f.readlines()

    if len(sys.argv) >= 4:
        start = int(sys.argv[2]) - 1  # 1-indexed → 0-indexed
        end = int(sys.argv[3]) - 1
        ok = check_block(lines, start, end)
    else:
        blocks = detect_blocks(lines)
        if not blocks:
            print("No box-drawing characters found.")
            sys.exit(0)
        ok = True
        for s, e in blocks:
            if not check_block(lines, s, e):
                ok = False

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
