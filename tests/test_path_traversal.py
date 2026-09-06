"""
These are the tests that actually matter for safety: an AI model can
propose any filename string it wants, and these guarantee none of them can
ever touch anything outside the one folder the human explicitly granted.
"""

import os

import pytest

TRAVERSAL_ATTEMPTS = [
    "../../../etc/passwd",
    "../secret.txt",
    "..\\..\\windows\\system32\\config",
    "subdir/../../escape.txt",
]


@pytest.mark.parametrize("bad_filename", TRAVERSAL_ATTEMPTS)
def test_read_blocks_traversal(folder_tool, bad_filename):
    result = folder_tool.read_file(bad_filename)
    assert "ERROR" in result


@pytest.mark.parametrize("bad_filename", TRAVERSAL_ATTEMPTS)
def test_write_blocks_traversal(folder_tool, bad_filename):
    result = folder_tool.write_file(bad_filename, "pwned")
    assert "ERROR" in result


@pytest.mark.parametrize("bad_filename", TRAVERSAL_ATTEMPTS)
def test_delete_blocks_traversal(folder_tool, bad_filename):
    result = folder_tool.delete_file(bad_filename)
    assert "ERROR" in result


def test_absolute_path_is_rejected(folder_tool):
    result = folder_tool.read_file("/etc/passwd")
    assert "ERROR" in result


def test_traversal_never_actually_touches_filesystem_outside_folder(folder_tool, tmp_path):
    outside_file = tmp_path.parent / "should_never_be_touched.txt"
    outside_file.write_text("original content")

    folder_tool.write_file(f"../{outside_file.name}", "overwritten by attack")

    assert outside_file.read_text() == "original content"
    outside_file.unlink()
