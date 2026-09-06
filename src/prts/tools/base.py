"""
Base interface every PRTS tool implements.

A "tool" is anything that gives PRTS a capability beyond plain chat --
folder access today, potentially web search, shell commands, a calendar,
etc. later. Adding a new tool means writing a new BaseTool subclass and
registering it in cli.py; nothing else in the chat loop needs to change.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolCall:
    """A parsed request from the model to use a tool."""
    tool_name: str
    kind: str
    arg: Optional[str] = None
    content: Optional[str] = None


class BaseTool:
    """Subclass this to add a new capability to PRTS."""

    name = "base"

    def system_prompt_block(self) -> str:
        """Text appended to the system prompt describing this tool's protocol."""
        raise NotImplementedError

    def parse(self, reply_text: str) -> Optional[ToolCall]:
        """Return a ToolCall if reply_text requests this tool, else None."""
        raise NotImplementedError

    def auto_context(self, user_input: str) -> Optional[str]:
        """
        Optional: return grounding context to inject automatically every
        turn, independent of whether the model correctly requests a tool
        call. This is what keeps smaller/local models from hallucinating
        instead of using the tool protocol. Return None if not applicable.
        """
        return None

    def requires_confirmation(self, call: ToolCall) -> bool:
        """Whether this action must be confirmed by the human before running."""
        return False

    def describe_action(self, call: ToolCall) -> str:
        """Human-readable description shown before confirmation / execution."""
        return f"{self.name}: {call.kind}"

    def execute(self, call: ToolCall) -> str:
        """Actually perform the action and return a result string for the model."""
        raise NotImplementedError
