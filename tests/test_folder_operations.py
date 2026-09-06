import os

import pytest

from prts.tools.folder import FolderTool


def test_folder_tool_rejects_missing_directory(tmp_path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(NotADirectoryError):
        FolderTool(str(missing))


def test_list_files_shows_all_entries(folder_tool):
    listing = folder_tool.list_files()
    assert "sui_entities.txt" in listing
    assert "notes.txt" in listing


def test_list_files_on_empty_folder(tmp_path):
    tool = FolderTool(str(tmp_path))
    assert "empty" in tool.list_files().lower()


def test_read_existing_file_returns_real_content(folder_tool):
    content = folder_tool.read_file("sui_entities.txt")
    assert "Sui Beast" in content
    assert "Li Sui" in content


def test_read_missing_file_returns_error(folder_tool):
    result = folder_tool.read_file("does_not_exist.txt")
    assert "ERROR" in result


def test_write_creates_new_file(folder_tool, sandbox_folder):
    result = folder_tool.write_file("created.txt", "hello world")
    assert "successfully" in result
    assert (sandbox_folder / "created.txt").read_text() == "hello world"


def test_write_overwrites_existing_file(folder_tool, sandbox_folder):
    folder_tool.write_file("notes.txt", "brand new content")
    assert (sandbox_folder / "notes.txt").read_text() == "brand new content"


def test_append_adds_to_end_of_file(folder_tool, sandbox_folder):
    original = (sandbox_folder / "notes.txt").read_text()
    folder_tool.write_file("notes.txt", " + more", append=True)
    assert (sandbox_folder / "notes.txt").read_text() == original + " + more"


def test_write_rejects_oversized_content(folder_tool):
    huge = "x" * 30000
    result = folder_tool.write_file("big.txt", huge)
    assert "ERROR" in result
    assert "too long" in result


def test_delete_removes_file(folder_tool, sandbox_folder):
    result = folder_tool.delete_file("notes.txt")
    assert "successfully" in result
    assert not (sandbox_folder / "notes.txt").exists()


def test_delete_missing_file_returns_error(folder_tool):
    result = folder_tool.delete_file("nope.txt")
    assert "ERROR" in result
