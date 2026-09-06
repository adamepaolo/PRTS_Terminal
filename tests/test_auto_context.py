"""
Regression tests for the fix to a real bug: llama3 hallucinated file names
and content instead of using the TOOL: protocol. auto_context() grounds the
model with real folder state every turn, independent of protocol use.
"""


def test_auto_context_always_lists_real_files(folder_tool):
    context = folder_tool.auto_context("hello")
    assert "sui_entities.txt" in context
    assert "notes.txt" in context


def test_auto_context_includes_content_when_filename_mentioned(folder_tool):
    context = folder_tool.auto_context("check sui_entities.txt for me")
    assert "Sui Beast" in context


def test_auto_context_matches_on_spaced_out_basename(folder_tool):
    """'sui entities' (spaces) should still match sui_entities.txt (underscore)."""
    context = folder_tool.auto_context("what does the sui entities file say")
    assert "Sui Beast" in context


def test_auto_context_does_not_include_unrelated_file_content(folder_tool):
    context = folder_tool.auto_context("check sui_entities.txt")
    assert "Sui Beast" in context
    assert "operational notes" not in context.lower()


def test_auto_context_warns_model_against_inventing_files(folder_tool):
    context = folder_tool.auto_context("anything")
    assert "invent" in context.lower()
