from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from harness.executor import execute


@dataclass(frozen=True)
class AgentRequest:
    """A task submitted to an AI engineering agent."""

    task: str
    repository_root: str
    instructions: str = ""
    constraints: tuple[str, ...] = ()
    scope: str = "read_only"
    action: str = "analyze"


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


class GovernedAgent:
    """Enforce platform execution policy before invoking an agent."""

    def __init__(self, provider: AgentProvider) -> None:
        self._provider = provider

    def run(self, request: AgentRequest) -> AgentResponse:
        root = Path(request.repository_root)

        execution = execute(
            root,
            scope=request.scope,
            action=request.action,
        )

        if not execution.executed:
            return AgentResponse(
                status="denied",
                summary=f"Agent execution denied: {request.task}",
                evidence=tuple(["governance:denied", *execution.failures]),
            )

        response = self._provider.run(request)

        return AgentResponse(
            status=response.status,
            summary=response.summary,
            changes=response.changes,
            evidence=(
                "governance:authorized",
                *response.evidence,
            ),
        )
