"""
Aggregates all active tools for one PRTS session: builds the combined
system-prompt addendum, routes a model reply to whichever tool claims it,
and collects auto-context from every tool each turn.
"""

from typing import List, Optional, Tuple

from .base import BaseTool, ToolCall


class ToolRegistry:
    def __init__(self, tools: Optional[List[BaseTool]] = None):
        self.tools: List[BaseTool] = tools or []

    def system_prompt_addendum(self) -> str:
        return "".join(t.system_prompt_block() for t in self.tools)

    def parse(self, reply_text: str) -> Tuple[Optional[BaseTool], Optional[ToolCall]]:
        for tool in self.tools:
            call = tool.parse(reply_text)
            if call is not None:
                return tool, call
        return None, None

    def auto_context(self, user_input: str) -> Optional[str]:
        parts = [c for c in (t.auto_context(user_input) for t in self.tools) if c]
        return "\n\n".join(parts) if parts else None
