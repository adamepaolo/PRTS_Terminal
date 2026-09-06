"""
Grants PRTS access to exactly one local folder: list, read, write, append,
and delete files in it. Every access is checked against the resolved real
path so subfolders/parent-directory traversal/absolute paths outside the
folder are all rejected -- the check happens in Python before any file is
touched, it is never just trusted from the model's own output.

Uses a simple text-based protocol (TOOL:LIST_FILES, TOOL:READ_FILE:<name>,
etc.) rather than each LLM provider's native function-calling schema, so it
works identically across every backend.

Because smaller/local models are not always reliable about using an
explicit protocol correctly (they may narrate "I checked the folder"
without emitting the actual command), `auto_context()` also proactively
grounds the model each turn with the real folder listing and the real
content of any file mentioned by name in the Doctor's message. This is
what actually prevents hallucinated file names/content, independent of
whether the model ever uses the protocol at all.
"""

import os
import re
from typing import Optional

from .base import BaseTool, ToolCall

MAX_FILE_CHARS = 6000     # cap on how much of a file's content we feed back
MAX_WRITE_CHARS = 20000   # cap on how much content a single write/append may contain

TOOL_INSTRUCTIONS_TEMPLATE = """

You have been granted access to exactly one local folder: "{folder}".

Before you answer, the Doctor's system automatically shows you the folder's
real file listing, and the real contents of any file whose name is
mentioned in the Doctor's message, as an "[Automatic folder context]" note.
Trust that note completely -- it reflects the actual filesystem. NEVER
invent file names or file contents that were not shown to you in that note
or in an actual tool result below. If you are not sure a file exists, say
so or use TOOL:LIST_FILES to check -- do not guess.

If you need something not already shown to you, use this exact text
protocol. Your ENTIRE reply must be ONLY the command below, nothing else --
no commentary, no markdown, no explanation:

  TOOL:LIST_FILES
      -> lists the folder's contents

  TOOL:READ_FILE:<filename>
      -> reads one file's contents

  TOOL:WRITE_FILE:<filename>
  <content...>
      -> creates the file, or overwrites it if it already exists. Put the
         command on the first line and the full new file content on the
         line(s) after it.

  TOOL:APPEND_FILE:<filename>
  <content...>
      -> adds content to the end of an existing file (creates it if it
         doesn't exist yet). Same format as WRITE_FILE.

  TOOL:DELETE_FILE:<filename>
      -> permanently deletes a file

Rules:
- WRITE_FILE, APPEND_FILE, and DELETE_FILE always require the Doctor's
  explicit confirmation in the terminal before anything happens. You will
  be told whether the action was approved or declined.
- Only propose a WRITE_FILE, APPEND_FILE, or DELETE_FILE action when the
  Doctor's message actually asked you to create, edit, or remove
  something. Never do this proactively or as a side effect of an
  unrelated request.
- Use exact filenames only; no path traversal, no subfolders.
- After any tool call, you'll get a result and can respond normally or
  issue another tool call.
"""


class FolderTool(BaseTool):
    name = "folder"

    def __init__(self, folder_path: str):
        resolved = os.path.realpath(os.path.expanduser(folder_path))
        if not os.path.isdir(resolved):
            raise NotADirectoryError(
                f"--folder path does not exist or is not a directory: {resolved}"
            )
        self.allowed_dir = resolved

    # -- path safety -----------------------------------------------------

    def _resolve(self, filename: str) -> str:
        if not filename:
            raise PermissionError("No filename given.")
        if os.path.isabs(filename) or ".." in filename.replace("\\", "/").split("/"):
            raise PermissionError(f"Access to '{filename}' is not permitted.")
        candidate = os.path.realpath(os.path.join(self.allowed_dir, filename))
        if candidate != self.allowed_dir and not candidate.startswith(self.allowed_dir + os.sep):
            raise PermissionError(f"Access to '{filename}' is outside the granted folder.")
        return candidate

    # -- raw operations ---------------------------------------------------

    def list_files(self) -> str:
        try:
            entries = sorted(os.listdir(self.allowed_dir))
        except Exception as e:
            return f"[ERROR listing folder: {e}]"
        if not entries:
            return "(the folder is empty)"
        lines = []
        for name in entries:
            full = os.path.join(self.allowed_dir, name)
            kind = "DIR " if os.path.isdir(full) else "FILE"
            lines.append(f"{kind}  {name}")
        return "\n".join(lines)

    def read_file(self, filename: str) -> str:
        try:
            path = self._resolve(filename)
        except PermissionError as e:
            return f"[ERROR: {e}]"
        if not os.path.isfile(path):
            return f"[ERROR: '{filename}' is not a file in the granted folder]"
        try:
            with open(path, "r", errors="replace") as f:
                content = f.read(MAX_FILE_CHARS + 1)
        except Exception as e:
            return f"[ERROR reading file: {e}]"
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + "\n...[truncated]"
        return content

    def write_file(self, filename: str, content: str, append: bool = False) -> str:
        if len(content) > MAX_WRITE_CHARS:
            return f"[ERROR: content too long ({len(content)} chars, limit {MAX_WRITE_CHARS})]"
        try:
            path = self._resolve(filename)
        except PermissionError as e:
            return f"[ERROR: {e}]"
        if os.path.isdir(path):
            return f"[ERROR: '{filename}' is a directory, not a file]"
        mode = "a" if append else "w"
        try:
            with open(path, mode, newline="") as f:
                f.write(content)
        except Exception as e:
            return f"[ERROR writing file: {e}]"
        verb = "Appended to" if append else "Wrote"
        return f"[{verb} '{filename}' successfully ({len(content)} chars)]"

    def delete_file(self, filename: str) -> str:
        try:
            path = self._resolve(filename)
        except PermissionError as e:
            return f"[ERROR: {e}]"
        if not os.path.isfile(path):
            return f"[ERROR: '{filename}' is not a file in the granted folder]"
        try:
            os.remove(path)
        except Exception as e:
            return f"[ERROR deleting file: {e}]"
        return f"[Deleted '{filename}' successfully]"

    # -- BaseTool interface -----------------------------------------------

    def system_prompt_block(self) -> str:
        return TOOL_INSTRUCTIONS_TEMPLATE.format(folder=self.allowed_dir)

    def parse(self, reply_text: str) -> Optional[ToolCall]:
        """
        Scan the reply line-by-line for a TOOL: command rather than
        requiring the whole reply to match exactly -- smaller/local models
        sometimes add stray commentary around the command. Stays strict
        about the command syntax itself while tolerating that.
        """
        lines = reply_text.split("\n")
        for i, line in enumerate(lines):
            s = line.strip()
            if s == "TOOL:LIST_FILES":
                return ToolCall(self.name, "LIST_FILES")
            m = re.match(r"^TOOL:READ_FILE:(.+)$", s)
            if m:
                return ToolCall(self.name, "READ_FILE", arg=m.group(1).strip())
            m = re.match(r"^TOOL:DELETE_FILE:(.+)$", s)
            if m:
                return ToolCall(self.name, "DELETE_FILE", arg=m.group(1).strip())
            m = re.match(r"^TOOL:WRITE_FILE:(.+)$", s)
            if m:
                return ToolCall(self.name, "WRITE_FILE", arg=m.group(1).strip(),
                                 content="\n".join(lines[i + 1:]))
            m = re.match(r"^TOOL:APPEND_FILE:(.+)$", s)
            if m:
                return ToolCall(self.name, "APPEND_FILE", arg=m.group(1).strip(),
                                 content="\n".join(lines[i + 1:]))
        return None

    def auto_context(self, user_input: str) -> Optional[str]:
        try:
            entries = sorted(os.listdir(self.allowed_dir))
        except Exception as e:
            return f"[Automatic folder context]\n[ERROR listing folder: {e}]"

        files = [e for e in entries if os.path.isfile(os.path.join(self.allowed_dir, e))]
        listing = ", ".join(files) if files else "(no files)"
        parts = ["[Automatic folder context -- not written by the Doctor]",
                  f"Files actually present in the granted folder: {listing}"]

        lowered = user_input.lower()
        matched = []
        for fname in files:
            base = os.path.splitext(fname)[0].lower().replace("_", " ").replace("-", " ")
            if fname.lower() in lowered or (base and base in lowered):
                matched.append(fname)

        for fname in matched:
            parts.append(f"\nContents of '{fname}':\n{self.read_file(fname)}")

        parts.append(
            "\nOnly reference the file names and content shown above, or use "
            "the TOOL: protocol to look at something else. Do not invent "
            "file names or contents beyond what is shown here."
        )
        return "\n".join(parts)

    def requires_confirmation(self, call: ToolCall) -> bool:
        return call.kind in ("WRITE_FILE", "APPEND_FILE", "DELETE_FILE")

    def describe_action(self, call: ToolCall) -> str:
        if call.kind == "WRITE_FILE":
            exists = os.path.isfile(os.path.join(self.allowed_dir, call.arg))
            return f"{'overwrite' if exists else 'create'} '{call.arg}'"
        if call.kind == "APPEND_FILE":
            return f"append to '{call.arg}'"
        if call.kind == "DELETE_FILE":
            return f"permanently DELETE '{call.arg}' (cannot be undone)"
        if call.kind == "READ_FILE":
            return f"read '{call.arg}'"
        return "check the folder listing"

    def execute(self, call: ToolCall) -> str:
        if call.kind == "LIST_FILES":
            return self.list_files()
        if call.kind == "READ_FILE":
            return self.read_file(call.arg)
        if call.kind == "WRITE_FILE":
            return self.write_file(call.arg, call.content or "", append=False)
        if call.kind == "APPEND_FILE":
            return self.write_file(call.arg, call.content or "", append=True)
        if call.kind == "DELETE_FILE":
            return self.delete_file(call.arg)
        return f"[ERROR: unknown folder tool action '{call.kind}']"
