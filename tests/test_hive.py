"""Tests for NeuralHive multi-agent orchestration."""

import pytest
import asyncio
from neuralhive import Agent, Hive, SupervisorTopology, RouterTopology, ConsensusTopology, SharedMemory


# ── Agent Tests ──────────────────────────────────────────────────

class TestAgent:
    @pytest.fixture
    def agent(self):
        return Agent(name="test_agent", system_prompt="You help with testing.")

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, agent):
        result = await agent.execute([{"role": "user", "content": "Hello"}])
        assert result.agent_name == "test_agent"
        assert result.output != ""

    @pytest.mark.asyncio
    async def test_tracks_calls(self, agent):
        await agent.execute([{"role": "user", "content": "Hi"}])
        await agent.execute([{"role": "user", "content": "Hello again"}])
        assert agent._calls == 2

    @pytest.mark.asyncio
    async def test_shared_context_injected(self, agent):
        ctx = {"other_agent": "Previous finding: budget exceeded"}
        result = await agent.execute(
            [{"role": "user", "content": "Summarize"}],
            shared_context=ctx,
        )
        assert result.tokens_used > 0

    def test_stats(self, agent):
        stats = agent.stats
        assert stats["name"] == "test_agent"
        assert stats["calls"] == 0


# ── SharedMemory Tests ───────────────────────────────────────────

class TestSharedMemory:
    def test_store_and_get(self):
        mem = SharedMemory()
        mem.store("agent_a", "result A")
        assert mem.get("agent_a") == "result A"

    def test_max_entries(self):
        mem = SharedMemory(max_entries=3)
        mem.store("a", 1)
        mem.store("b", 2)
        mem.store("c", 3)
        mem.store("d", 4)  # evicts "a"
        assert mem.get("a") is None
        assert mem.get("d") == 4

    def test_get_by_prefix(self):
        mem = SharedMemory()
        mem.store("team1_analyst", "x")
        mem.store("team1_writer", "y")
        mem.store("team2_expert", "z")
        result = mem.get_by_prefix("team1")
        assert len(result) == 2

    def test_contains(self):
        mem = SharedMemory()
        mem.store("key", "val")
        assert "key" in mem
        assert "missing" not in mem

    def test_clear(self):
        mem = SharedMemory()
        mem.store("a", 1)
        mem.clear()
        assert len(mem) == 0


# ── Hive Tests ───────────────────────────────────────────────────

class TestHive:
    @pytest.fixture
    def agents(self):
        return [
            Agent(name="analyst", system_prompt="Analyze data."),
            Agent(name="writer", system_prompt="Write summaries."),
        ]

    @pytest.mark.asyncio
    async def test_sequential_default(self, agents):
        hive = Hive(agents=agents)
        result = await hive.run("What's happening?")
        assert result.topology_used == "sequential"
        assert len(result.agent_results) == 2

    @pytest.mark.asyncio
    async def test_supervisor_topology(self, agents):
        hive = Hive(agents=agents, topology=SupervisorTopology())
        result = await hive.run("Analyze the situation")
        assert "supervisor" in result.topology_used
        assert result.total_tokens > 0

    @pytest.mark.asyncio
    async def test_router_topology(self, agents):
        hive = Hive(
            agents=agents,
            topology=RouterTopology(routing_rules={"analyst": ["analyze", "data"]}),
        )
        result = await hive.run("Analyze the data please")
        assert "router→analyst" in result.topology_used
        assert len(result.agent_results) == 1

    @pytest.mark.asyncio
    async def test_consensus_topology(self, agents):
        hive = Hive(agents=agents, topology=ConsensusTopology(strategy="synthesis"))
        result = await hive.run("Give your opinion")
        assert "consensus" in result.topology_used
        assert "Synthesised from 2 agents" in result.final_answer

    @pytest.mark.asyncio
    async def test_memory_populated(self, agents):
        hive = Hive(agents=agents)
        await hive.run("Hello")
        assert "analyst" in hive.memory
        assert "writer" in hive.memory

    def test_get_agent(self, agents):
        hive = Hive(agents=agents)
        assert hive.get_agent("analyst") is not None
        assert hive.get_agent("nonexistent") is None

    def test_stats(self, agents):
        hive = Hive(agents=agents)
        stats = hive.stats
        assert len(stats) == 2
        assert stats[0]["name"] == "analyst"
