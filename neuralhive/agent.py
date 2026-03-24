"""Agent definition — single specialist in the hive."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AgentResult:
    """Result of a single agent execution."""
    agent_name: str
    output: str
    tokens_used: int = 0
    cost: float = 0.0
    duration_ms: int = 0
    error: str | None = None
    tools_called: list[str] = field(default_factory=list)


@dataclass
class Agent:
    """
    A specialist agent in the hive.

    Each agent has its own system prompt, tools, and model configuration.
    Agents are stateless — the Hive manages conversation context.
    """

    name: str
    system_prompt: str = "You are a helpful assistant."
    tools: list[Callable] = field(default_factory=list)
    model: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout: int = 25

    # Runtime state (managed by Hive)
    _total_tokens: int = field(default=0, repr=False)
    _total_cost: float = field(default=0.0, repr=False)
    _calls: int = field(default=0, repr=False)

    async def execute(
        self,
        messages: list[dict[str, str]],
        shared_context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Execute this agent with the given messages.

        In production, this calls litellm.acompletion.
        """
        # Build full message list
        full_messages = [{"role": "system", "content": self.system_prompt}]

        # Inject shared context if available
        if shared_context:
            context_str = "\n".join(f"[{k}]: {v}" for k, v in shared_context.items())
            full_messages.append({
                "role": "system",
                "content": f"Context from other agents:\n{context_str}",
            })

        full_messages.extend(messages)

        # Simulate execution (real impl: litellm.acompletion)
        self._calls += 1
        estimated_tokens = sum(len(m.get("content", "")) // 4 for m in full_messages)
        self._total_tokens += estimated_tokens

        return AgentResult(
            agent_name=self.name,
            output=f"[{self.name}] Response to: {messages[-1].get('content', '')[:50]}...",
            tokens_used=estimated_tokens,
        )

    @property
    def stats(self) -> dict[str, Any]:
        """Agent usage statistics."""
        return {
            "name": self.name,
            "calls": self._calls,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
            "avg_tokens_per_call": self._total_tokens // max(1, self._calls),
        }
