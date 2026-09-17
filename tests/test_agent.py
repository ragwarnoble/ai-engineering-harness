from pathlib import Path

from harness.agent import AgentRequest, GovernedAgent, MockAgent


def test_governed_agent_allows_read_only_request(tmp_path: Path) -> None:
    request = AgentRequest(
        task="analyze repository",
        repository_root=str(tmp_path),
        scope="read_only",
        action="analyze",
    )

    response = GovernedAgent(MockAgent()).run(request)

    assert response.status == "completed"
    assert response.summary == "Mock execution: analyze repository"
    assert response.evidence == (
        "governance:authorized",
        "mock-agent",
    )


def test_governed_agent_denies_unauthorized_production_request(
    tmp_path: Path,
) -> None:
    request = AgentRequest(
        task="commit changes",
        repository_root=str(tmp_path),
        scope="production_changes",
        action="commit",
    )

    response = GovernedAgent(MockAgent()).run(request)

    assert response.status == "denied"
    assert response.summary == "Agent execution denied: commit changes"
    assert response.evidence[0] == "governance:denied"
    assert "gate evidence does not exist" in response.evidence
