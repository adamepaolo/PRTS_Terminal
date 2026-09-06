def test_parses_list_files(folder_tool):
    call = folder_tool.parse("TOOL:LIST_FILES")
    assert call is not None
    assert call.kind == "LIST_FILES"


def test_parses_read_file(folder_tool):
    call = folder_tool.parse("TOOL:READ_FILE:sui_entities.txt")
    assert call.kind == "READ_FILE"
    assert call.arg == "sui_entities.txt"


def test_parses_delete_file(folder_tool):
    call = folder_tool.parse("TOOL:DELETE_FILE:notes.txt")
    assert call.kind == "DELETE_FILE"
    assert call.arg == "notes.txt"


def test_parses_write_file_with_multiline_content(folder_tool):
    reply = "TOOL:WRITE_FILE:newfile.txt\nline one\nline two"
    call = folder_tool.parse(reply)
    assert call.kind == "WRITE_FILE"
    assert call.arg == "newfile.txt"
    assert call.content == "line one\nline two"


def test_parses_append_file_with_multiline_content(folder_tool):
    reply = "TOOL:APPEND_FILE:log.txt\nnew entry"
    call = folder_tool.parse(reply)
    assert call.kind == "APPEND_FILE"
    assert call.content == "new entry"


def test_tolerates_preamble_before_command(folder_tool):
    """Smaller/local models sometimes narrate before the actual command."""
    reply = "Sure Doctor, let me check.\nTOOL:LIST_FILES"
    call = folder_tool.parse(reply)
    assert call is not None
    assert call.kind == "LIST_FILES"


def test_normal_reply_is_not_mistaken_for_a_tool_call(folder_tool):
    reply = "Doctor, PRTS is online and ready to assist."
    assert folder_tool.parse(reply) is None


def test_confirmation_required_for_mutating_actions(folder_tool):
    write_call = folder_tool.parse("TOOL:WRITE_FILE:x.txt\ncontent")
    delete_call = folder_tool.parse("TOOL:DELETE_FILE:x.txt")
    read_call = folder_tool.parse("TOOL:READ_FILE:x.txt")

    assert folder_tool.requires_confirmation(write_call) is True
    assert folder_tool.requires_confirmation(delete_call) is True
    assert folder_tool.requires_confirmation(read_call) is False
