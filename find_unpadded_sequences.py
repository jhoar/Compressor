#!/usr/bin/env python3
"""
Scan leaf directories and identify those that contain sequential numeric files
whose filenames are not zero-padded (or inconsistently padded) so that
lexicographic ordering differs from numeric ordering.

Usage:
  python find_unpadded_sequences.py -r .

This prints directories that likely need zero-padding (recommended width is
the width of the largest number in the sequence).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


NUM_RE = re.compile(r"(\d+)")


def extract_number_token(name: str) -> Optional[Tuple[int, str]]:
    """Return (int_value, token_str) for the last numeric token in the name,
    or None if no numeric token found.
    """
    m = NUM_RE.findall(name)
    if not m:
        return None
    s = m[-1]
    return int(s), s


def is_leaf_dir(d: Path) -> bool:
    """A directory is a leaf if none of its subdirectories contain files."""
    if not d.is_dir():
        return False
    for sub in d.iterdir():
        if sub.is_dir():
            # If this subdirectory (or any nested dir) has any file, d is not leaf
            for p in sub.rglob('*'):
                if p.is_file():
                    return False
    return True


def analyze_dir(d: Path, min_files: int = 2):
    files = [p for p in sorted(d.iterdir()) if p.is_file() and not p.name.startswith('.')]
    if len(files) < min_files:
        return None

    entries = []  # tuples (path, int_value, token_str)
    for p in files:
        res = extract_number_token(p.stem)
        if res is None:
            continue
        val, token = res
        entries.append((p, val, token))

    if len(entries) < min_files:
        return None

    # Sort orders
    lex_order = [e[0].name for e in sorted(entries, key=lambda x: x[0].name)]
    numeric_order = [e[0].name for e in sorted(entries, key=lambda x: (x[1], x[0].name))]

    nums = [e[1] for e in entries]
    min_n, max_n = min(nums), max(nums)

    # Are numbers consecutive?
    expected_count = max_n - min_n + 1
    unique_nums = sorted(set(nums))
    consecutive = (expected_count == len(unique_nums) and unique_nums == list(range(min_n, max_n + 1)))

    if not consecutive:
        return None

    # Determine padding consistency
    token_lengths = [len(e[2]) for e in entries]
    desired_width = len(str(max_n))
    fully_padded = (len(set(token_lengths)) == 1 and token_lengths[0] == desired_width)

    # If lexicographic order differs from numeric order and not fully padded => report
    if lex_order != numeric_order and not fully_padded:
        return {
            'dir': str(d),
            'count': len(entries),
            'min': min_n,
            'max': max_n,
            'desired_width': desired_width,
            'token_lengths_sample': sorted(set(token_lengths)),
            'lex_order_sample': lex_order[:10],
            'numeric_order_sample': numeric_order[:10],
        }

    return None


def find_problem_dirs(root: Path, min_files: int = 2) -> List[dict]:
    root = root.resolve()
    results = []
    # Include root itself and all subdirectories
    dirs = [p for p in [root] + [p for p in root.rglob('*') if p.is_dir()]]

    for d in dirs:
        if not is_leaf_dir(d):
            continue
        res = analyze_dir(d, min_files=min_files)
        if res:
            results.append(res)

    return results


def make_new_name(old: Path, width: int) -> Path:
    """Return new Path for old by zero-padding the last numeric token in the stem."""
    stem = old.stem
    m = NUM_RE.findall(stem)
    if not m:
        return old
    last = m[-1]
    padded = last.zfill(width)
    # replace last occurrence of the digit sequence
    new_stem = re.sub(r"(\d+)(?!.*\d)", padded, stem)
    return old.with_name(new_stem + old.suffix)


def perform_renames(mapping: List[Tuple[Path, Path]], dry_run: bool = True, force: bool = False) -> Tuple[int, int]:
    """Perform renames given a list of (src, dst) tuples. Returns (succeeded, failed)."""
    succeeded = 0
    failed = 0
    # sanity checks
    dsts = [dst for _src, dst in mapping]
    if len(dsts) != len(set(dsts)):
        raise RuntimeError("Duplicate destination filenames detected; aborting to avoid data loss.")

    # Check for existing files that are not in the source set
    srcs = set([src.resolve() for src, _ in mapping])
    for _src, dst in mapping:
        if dst.exists() and dst.resolve() not in srcs and not force:
            raise RuntimeError(f"Destination {dst} already exists and --force not given")

    if dry_run:
        print("Dry-run mapping (no changes):")
        for src, dst in mapping:
            print(f"{src} -> {dst}")
        return 0, 0

    # Perform two-phase rename to avoid collisions: src -> temp, then temp -> final
    import uuid

    temp_map = []
    try:
        for src, dst in mapping:
            temp = src.with_name(src.name + f".renametmp-{uuid.uuid4().hex}")
            src.rename(temp)
            temp_map.append((temp, dst))

        for temp, dst in temp_map:
            if dst.exists() and dst.resolve() not in srcs and not force:
                raise RuntimeError(f"Destination {dst} exists; aborting")
            # Ensure parent exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            temp.rename(dst)
            succeeded += 1

    except Exception as exc:
        print(f"Rename failed: {exc}", file=sys.stderr)
        failed = len(mapping) - succeeded
        # Attempt best-effort rollback: rename any remaining temp files back to original names is hard
        # so we provide information and exit with failure.
        return succeeded, failed

    return succeeded, failed


def main(argv=None):
    parser = argparse.ArgumentParser(description='Find leaf dirs with unpadded numeric sequences and optionally rename')
    parser.add_argument('-r', '--root', type=Path, default=Path('.'), help='Root path to search')
    parser.add_argument('--min-files', type=int, default=2, help='Minimum numeric files to consider')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--rename', action='store_true', help='Rename files to zero-padded names')
    parser.add_argument('--width', type=int, default=None, help='Optional width to pad numbers to (default: width of largest number)')
    parser.add_argument('--dry-run', action='store_true', help='When renaming, only print mapping')
    parser.add_argument('--force', action='store_true', help='Allow overwriting existing files when renaming')
    args = parser.parse_args(argv)

    root = args.root
    results = find_problem_dirs(root, min_files=args.min_files)
    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    if not results:
        print('No unpadded sequential numeric sequences found')
        return 0

    if not args.rename:
        print('Directories with unpadded sequential numeric filenames (need zero-padding):')
        for r in results:
            print(f"- {r['dir']}: {r['count']} files, range {r['min']}-{r['max']}, suggested width={r['desired_width']}")
            print('  sample lex order :', ', '.join(r['lex_order_sample']))
            print('  sample numeric   :', ', '.join(r['numeric_order_sample']))
            print('')
        return 0

    # Rename mode
    all_mappings = []
    for r in results:
        d = Path(r['dir'])
        # Recompute entries in case of omitted files
        files = [p for p in sorted(d.iterdir()) if p.is_file() and not p.name.startswith('.')]
        entries = []
        for p in files:
            res = extract_number_token(p.stem)
            if res is None:
                continue
            val, token = res
            entries.append((p, val, token))
        if not entries:
            continue
        max_n = max([e[1] for e in entries])
        width = args.width if args.width is not None else len(str(max_n))

        mappings = []
        for src, val, token in entries:
            dst = make_new_name(src, width)
            if src.resolve() != dst.resolve():
                mappings.append((src, dst))

        if mappings:
            print(f"Directory: {d} -> will rename {len(mappings)} files (width={width})")
            for s, t in mappings[:10]:
                print(f"  {s.name} -> {t.name}")
            if len(mappings) > 10:
                print(f"  ... and {len(mappings)-10} more")
            all_mappings.extend(mappings)

    if not all_mappings:
        print('No files require renaming')
        return 0

    try:
        succeeded, failed = perform_renames(all_mappings, dry_run=args.dry_run, force=args.force)
    except Exception as exc:
        print(f"Pre-check failed: {exc}", file=sys.stderr)
        return 2

    print(f"Renaming complete. succeeded={succeeded}, failed={failed}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
