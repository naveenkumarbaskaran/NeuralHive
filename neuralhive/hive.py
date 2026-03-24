"""Hive — multi-agent orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from neuralhive.agent import Agent, AgentResult
from neuralhive.memory import SharedMemory


@dataclass
class HiveResult:
    """Result of a full hive execution."""
    final_answer: str
    agent_results: list[AgentResult] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_ms: int = 0
    topology_used: str = ""

    @property
    def cost_breakdown(self) -> dict[str, float]:
        return {r.agent_name: r.cost for r in self.agent_results}


@dataclass
class Hive:
    """
    Multi-agent orchestrator.

    Routes queries through agents according to the chosen topology.
    Manages shared memory, fault tolerance, and cost tracking.
    """

    agents: list[Agent]
    topology: Any = None  # Topology instance
    memory: SharedMemory = field(default_factory=SharedMemory)
    max_rounds: int = 5

    async def run(self, query: str) -> HiveResult:
        """Execute a query through the hive."""
        messages = [{"role": "user", "content": query}]

        if self.topology is None:
            # Default: sequential through all agents
            return await self._run_sequential(messages)

        return await self.topology.execute(self.agents, messages, self.memory)

    async def _run_sequential(self, messages: list[dict]) -> HiveResult:
        """Fallback: run all agents sequentially."""
        results: list[AgentResult] = []
        context: dict[str, str] = {}

        for agent in self.agents:
            result = await agent.execute(messages, shared_context=context)
            results.append(result)
            context[agent.name] = result.output
            self.memory.store(agent.name, result.output)

        return HiveResult(
            final_answer=results[-1].output if results else "",
            agent_results=results,
            total_tokens=sum(r.tokens_used for r in results),
            topology_used="sequential",
        )

    def get_agent(self, name: str) -> Agent | None:
        """Get an agent by name."""
        return next((a for a in self.agents if a.name == name), None)

    @property
    def stats(self) -> list[dict]:
        """All agent statistics."""
        return [a.stats for a in self.agents]
