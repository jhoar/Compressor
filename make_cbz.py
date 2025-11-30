#!/usr/bin/env python3
"""
Create .cbz (zip) archives from deepest sub-directories (leaf directories).

Behavior:
 - A "leaf" directory is a directory that contains files and has no
   descendant directory that contains files. (If a directory has files and
   also a child directory with files, it is not a leaf.)
 - For each leaf directory, create an archive named <DirectoryName>.cbz
   containing the files directly in that directory at the archive root.
 - If a name collision happens in the output folder, append _1, _2, ...

Designed to be cross-platform and run with Python 3.6+.
"""

from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path
from typing import List


def find_leaf_dirs(root: Path, include_empty: bool = False) -> List[Path]:
    """Return a list of directories under root that are "leaf" directories.

    A directory is a leaf if the total number of files under it equals the
    number of files directly in it (i.e., no files in descendant subdirs).
    If include_empty is True, directories with zero files are considered.
    """
    leafs: List[Path] = []
    if not root.exists():
        raise FileNotFoundError(f"Root path {root!s} does not exist")

    for dirpath, dirnames, filenames in os.walk(root):
        cur_dir = Path(dirpath)
        direct_files_count = len([f for f in filenames if not f.startswith('.')])
        if direct_files_count == 0 and not include_empty:
            # skip directories that have no files directly unless include_empty
            continue

        # Count all files under this directory (including itself)
        total_files = 0
        for _root, _dirs, _files in os.walk(cur_dir):
            total_files += len([f for f in _files if not f.startswith('.')])

        if total_files == direct_files_count:
            # no files in descendant directories => leaf
            leafs.append(cur_dir)

    return leafs


def make_cbz_for_dir(src_dir: Path, dest_dir: Path) -> Path:
    """Create a .cbz file for src_dir inside dest_dir and return the path."""
    base_name = src_dir.name or "root"
    candidate = dest_dir / f"{base_name}.cbz"
    counter = 1
    while candidate.exists():
        candidate = dest_dir / f"{base_name}_{counter}.cbz"
        counter += 1

    # Ensure destination directory exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Files directly in src_dir (ignore hidden files by default)
    files = [p for p in src_dir.iterdir() if p.is_file() and not p.name.startswith('.')]

    # Create the zip
    compression = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(candidate, mode='w', compression=compression) as zf:
        for f in files:
            # Put files at archive root with their basename
            zf.write(f, arcname=f.name)

    return candidate


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create .cbz archives from leaf directories")
    parser.add_argument('-r', '--root', type=Path, default=Path('.'), help='Root path to search')
    parser.add_argument('-o', '--output', type=Path, default=None, help='Optional output directory for all .cbz files. If omitted each archive will be written into the parent directory of the leaf folder.')
    parser.add_argument('--include-empty', action='store_true', help='Include empty directories (create empty archives)')
    parser.add_argument('--dry-run', action='store_true', help='Print actions without creating archives')
    parser.add_argument('--verbose', action='store_true', help='Print files that will be archived and size details')
    args = parser.parse_args(argv)

    root = args.root.resolve()
    output = args.output.resolve() if args.output else None

    if not root.exists():
        print(f"Root path '{root}' does not exist", file=sys.stderr)
        return 2

    # If an explicit output directory was provided, ensure it exists. If not,
    # archives will be written into each leaf's parent directory.
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)

    leafs = find_leaf_dirs(root, include_empty=args.include_empty)
    if not leafs:
        print(f"No leaf directories with files found under '{root}'. Nothing to do.")
        return 0

    created = []
    for d in leafs:
        # Determine destination directory: either the provided output or the parent of the leaf
        dest_dir = output if output is not None else d.parent

        # If dry-run, just print
        # Determine files and sizes for verbose/dry-run output
        files = [p for p in d.iterdir() if p.is_file() and not p.name.startswith('.')]
        total_bytes = sum([p.stat().st_size for p in files]) if files else 0

        if args.dry_run:
            print(f"Would create archive for: {d} -> {dest_dir / (d.name + '.cbz')}")
            if args.verbose:
                print(f"  Files ({len(files)}):")
                for f in files:
                    print(f"    - {f.name} ({f.stat().st_size} bytes)")
                print(f"  Total bytes: {total_bytes}")
            continue

        if args.verbose:
            print(f"Creating archive for: {d} -> {dest_dir / (d.name + '.cbz')}")
            print(f"  Files ({len(files)}):")
            for f in files:
                print(f"    - {f.name} ({f.stat().st_size} bytes)")
            print(f"  Total bytes: {total_bytes}")
        try:
            dest = make_cbz_for_dir(d, dest_dir)
            print(f"Created: {dest}  (from {d})")
            created.append(dest)
        except Exception as exc:
            print(f"Failed to create archive for {d}: {exc}", file=sys.stderr)

    if output is not None:
        print(f"Done. Created {len(created)} .cbz file(s) in '{output}'")
    else:
        print(f"Done. Created {len(created)} .cbz file(s) alongside their source parent folders")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
