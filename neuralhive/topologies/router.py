"""Router topology — single dispatch to best-fit agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neuralhive.agent import Agent, AgentResult
from neuralhive.hive import HiveResult
from neuralhive.memory import SharedMemory


@dataclass
class RouterTopology:
    """
    Router topology: dispatches query to a single best-fit agent.

    Uses keyword matching or LLM-based routing to select the best agent.
    """

    routing_rules: dict[str, list[str]] = field(default_factory=dict)

    def _select_agent(self, query: str, agents: list[Agent]) -> Agent:
        """Select best agent based on routing rules or keyword match."""
        query_lower = query.lower()

        # Rule-based routing
        for agent_name, keywords in self.routing_rules.items():
            if any(kw in query_lower for kw in keywords):
                match = next((a for a in agents if a.name == agent_name), None)
                if match:
                    return match

        # Fallback: match against agent system prompts
        for agent in agents:
            prompt_words = agent.system_prompt.lower().split()
            if any(word in query_lower for word in prompt_words[:10]):
                return agent

        # Default: first agent
        return agents[0]

    async def execute(
        self,
        agents: list[Agent],
        messages: list[dict],
        memory: SharedMemory,
    ) -> HiveResult:
        """Route to single agent."""
        query = messages[-1].get("content", "") if messages else ""
        selected = self._select_agent(query, agents)

        result = await selected.execute(messages)
        memory.store(selected.name, result.output)

        return HiveResult(
            final_answer=result.output,
            agent_results=[result],
            total_tokens=result.tokens_used,
            topology_used=f"router→{selected.name}",
        )
