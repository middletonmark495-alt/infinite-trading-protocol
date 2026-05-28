import os
import json
import anthropic
from typing import Dict, List, Optional


class BaseAgent:
    """Base class for all AI business agents. Handles the Claude tool-use loop."""

    NAME = "base"
    ROLE = "Generic Agent"
    TOOLS: List[Dict] = []

    def __init__(self, tool_registry, state_manager, message_bus, model: str = None):
        self.tool_registry = tool_registry
        self.state = state_manager
        self.bus = message_bus
        self.model = model or os.getenv("SPECIALIST_MODEL", "claude-sonnet-4-6")
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _get_system_prompt(self) -> str:
        raise NotImplementedError

    def run(self, task: str, context: Dict = None, business_id: str = None) -> str:
        """Run the agent on a task, executing tool calls in a loop until done."""
        context = context or {}

        business_context = ""
        if business_id:
            business = self.state.get_business(business_id)
            if business:
                # Trim large fields to keep context manageable
                trimmed = {k: v for k, v in business.items()
                           if k not in ("content_pieces",) and v is not None}
                business_context = f"\n\nBUSINESS STATE:\n{json.dumps(trimmed, indent=2)}"

        messages = [{
            "role": "user",
            "content": f"TASK: {task}{business_context}" +
                       (f"\n\nCONTEXT: {json.dumps(context)}" if context else "")
        }]

        total_tokens = 0
        final_response = ""
        max_iterations = 10

        for _ in range(max_iterations):
            kwargs = {
                "model": self.model,
                "max_tokens": 8192,
                "system": self._get_system_prompt(),
                "messages": messages,
            }
            if self.TOOLS:
                kwargs["tools"] = self.TOOLS

            response = self.client.messages.create(**kwargs)
            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            text_blocks = [b for b in response.content if b.type == "text"]

            if text_blocks:
                final_response = "\n".join(b.text for b in text_blocks)

            if not tool_uses or response.stop_reason == "end_turn":
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tc in tool_uses:
                result = self.tool_registry.execute(self.NAME, tc.name, tc.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result
                })
            messages.append({"role": "user", "content": tool_results})

        self.state.log_agent_activity(
            agent=self.NAME,
            task=task[:300],
            output_summary=final_response[:600],
            business_id=business_id,
            tokens_used=total_tokens
        )

        return final_response
