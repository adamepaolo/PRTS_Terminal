from prts.tools import ToolRegistry


def test_empty_registry_has_no_addendum_and_no_context():
    registry = ToolRegistry()
    assert registry.system_prompt_addendum() == ""
    assert registry.auto_context("anything") is None


def test_registry_parses_reply_via_registered_tool(folder_tool):
    registry = ToolRegistry([folder_tool])
    tool, call = registry.parse("TOOL:LIST_FILES")
    assert tool is folder_tool
    assert call.kind == "LIST_FILES"


def test_registry_returns_none_for_unrecognized_reply(folder_tool):
    registry = ToolRegistry([folder_tool])
    tool, call = registry.parse("just a normal answer")
    assert tool is None
    assert call is None


def test_registry_aggregates_system_prompt_from_all_tools(folder_tool):
    registry = ToolRegistry([folder_tool])
    addendum = registry.system_prompt_addendum()
    assert "TOOL:LIST_FILES" in addendum


def test_registry_aggregates_auto_context_from_all_tools(folder_tool):
    registry = ToolRegistry([folder_tool])
    context = registry.auto_context("hello")
    assert "sui_entities.txt" in context
