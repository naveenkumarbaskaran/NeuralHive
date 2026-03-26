"""Supervisor topology — boss agent delegates to specialists."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neuralhive.agent import Agent, AgentResult
from neuralhive.hive import HiveResult
from neuralhive.memory import SharedMemory


@dataclass
class SupervisorTopology:
    """
    Supervisor topology: a boss agent decides which specialists to call.

    Strategies:
        - "sequential": All agents in order
        - "parallel": All agents concurrently
        - "conditional": Boss picks which agents to delegate to
    """

    routing_strategy: str = "sequential"
    max_delegations: int = 5

    async def execute(
        self,
        agents: list[Agent],
        messages: list[dict],
        memory: SharedMemory,
    ) -> HiveResult:
        """Run the supervisor topology."""
        results: list[AgentResult] = []
        context: dict[str, str] = {}

        if self.routing_strategy == "sequential":
            for agent in agents:
                result = await agent.execute(messages, shared_context=context)
                results.append(result)
                context[agent.name] = result.output
                memory.store(agent.name, result.output)

        elif self.routing_strategy == "parallel":
            import asyncio
            tasks = [agent.execute(messages) for agent in agents]
            results = await asyncio.gather(*tasks)
            for agent, result in zip(agents, results):
                memory.store(agent.name, result.output)

        elif self.routing_strategy == "conditional":
            # In production: supervisor LLM picks agents
            # Simplified: use first agent as supervisor, rest as workers
            if agents:
                supervisor = agents[0]
                plan = await supervisor.execute(messages)
                results.append(plan)
                # Delegate to remaining agents based on plan
                for agent in agents[1:]:
                    result = await agent.execute(messages, shared_context=context)
                    results.append(result)
                    context[agent.name] = result.output

        return HiveResult(
            final_answer=results[-1].output if results else "",
            agent_results=list(results),
            total_tokens=sum(r.tokens_used for r in results),
            topology_used=f"supervisor/{self.routing_strategy}",
        )
