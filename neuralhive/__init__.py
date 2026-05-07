"""NeuralHive — Multi-Agent Orchestration Framework."""

from neuralhive.agent import Agent
from neuralhive.hive import Hive
from neuralhive.topologies.supervisor import SupervisorTopology
from neuralhive.topologies.router import RouterTopology
from neuralhive.topologies.consensus import ConsensusTopology
from neuralhive.memory import SharedMemory

__version__ = "2.0.0"
__all__ = [
    "Agent", "Hive", "SupervisorTopology", "RouterTopology",
    "ConsensusTopology", "SharedMemory",
]
