import pytest

from prts.tools.folder import FolderTool


@pytest.fixture
def sandbox_folder(tmp_path):
    """A temp folder with a couple of files, used across tests."""
    (tmp_path / "sui_entities.txt").write_text(
        "Sui Beast\nLi Sui\nOperator\nRanged/Melee\n"
    )
    (tmp_path / "notes.txt").write_text("Some general operational notes.\n")
    return tmp_path


@pytest.fixture
def folder_tool(sandbox_folder):
    return FolderTool(str(sandbox_folder))
