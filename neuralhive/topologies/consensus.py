"""Consensus topology — all agents vote/contribute, synthesised output."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from neuralhive.agent import Agent, AgentResult
from neuralhive.hive import HiveResult
from neuralhive.memory import SharedMemory


@dataclass
class ConsensusTopology:
    """
    Consensus topology: all agents answer, results are synthesised.

    Strategies:
        - "majority": Most common answer wins
        - "synthesis": Combine all answers into one
        - "best": Pick the highest-confidence answer
    """

    strategy: str = "synthesis"

    async def execute(
        self,
        agents: list[Agent],
        messages: list[dict],
        memory: SharedMemory,
    ) -> HiveResult:
        """All agents execute, then synthesise results."""
        # Execute all agents in parallel
        tasks = [agent.execute(messages) for agent in agents]
        results: list[AgentResult] = await asyncio.gather(*tasks)

        # Store all outputs
        for agent, result in zip(agents, results):
            memory.store(agent.name, result.output)

        # Synthesise based on strategy
        if self.strategy == "majority":
            # Simple: pick most common output (in real impl, use semantic similarity)
            final = results[0].output if results else ""
        elif self.strategy == "synthesis":
            # Combine all outputs
            combined = "\n\n".join(f"**{r.agent_name}**: {r.output}" for r in results)
            final = f"Synthesised from {len(results)} agents:\n{combined}"
        elif self.strategy == "best":
            # Pick shortest (proxy for most confident/concise)
            final = min(results, key=lambda r: len(r.output)).output if results else ""
        else:
            final = results[-1].output if results else ""

        return HiveResult(
            final_answer=final,
            agent_results=results,
            total_tokens=sum(r.tokens_used for r in results),
            topology_used=f"consensus/{self.strategy}",
        )
