import os
from pathlib import Path
import shutil

import pytest

import find_unpadded_sequences as fus


def touch(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x")


def test_extract_number_token():
    assert fus.extract_number_token('img001') == (1, '001')
    assert fus.extract_number_token('frame_12_extra') == (12, '12')
    assert fus.extract_number_token('no_digits') is None


def test_analyze_dir_detects_unpadded(tmp_path):
    # create leaf dir
    d = tmp_path / 'leaf'
    d.mkdir()
    # create unpadded sequence: 1,2,10
    files = ['img1.jpg', 'img2.jpg', 'img10.jpg']
    for f in files:
        touch(d / f)

    res = fus.analyze_dir(d, min_files=2)
    assert res is not None
    assert res['min'] == 1
    assert res['max'] == 10
    # desired width should be 2 (since max is 10)
    assert res['desired_width'] == len(str(res['max']))


def test_make_new_name_and_perform_renames(tmp_path):
    d = tmp_path / 'leaf2'
    d.mkdir()
    files = ['img1.jpg', 'img2.jpg', 'img10.jpg']
    paths = []
    for f in files:
        p = d / f
        touch(p)
        paths.append(p)

    # build mapping
    mappings = []
    width = 2
    for p in paths:
        newp = fus.make_new_name(p, width)
        mappings.append((p, newp))

    # dry-run should not perform renames
    succ, fail = fus.perform_renames(mappings, dry_run=True)
    assert (succ, fail) == (0, 0)
    for p in paths:
        assert p.exists()

    # perform actual renames
    succ, fail = fus.perform_renames(mappings, dry_run=False)
    assert fail == 0
    assert succ == len(mappings)

    # expected new names
    expected = { (d / 'img01.jpg'), (d / 'img02.jpg'), (d / 'img10.jpg') }
    actual = set([p for p in d.iterdir() if p.is_file()])
    assert expected == actual
