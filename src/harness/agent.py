from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AgentRequest:
    """A task submitted to an AI engineering agent."""

    task: str
    repository_root: str
    instructions: str = ""
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentResponse:
    """The result returned by an AI engineering agent."""

    status: str
    summary: str
    changes: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()


class AgentProvider(Protocol):
    """Provider-neutral interface for AI engineering agents."""

    def run(self, request: AgentRequest) -> AgentResponse:
        """Execute an engineering task."""
        ...


class MockAgent:
    """Deterministic agent implementation for testing the contract."""

    def run(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            status="completed",
            summary=f"Mock execution: {request.task}",
            evidence=("mock-agent",),
        )
