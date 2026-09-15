from pathlib import Path

from harness.agent import AgentRequest, MockAgent


def test_agent_request_defaults(tmp_path: Path) -> None:
    request = AgentRequest(
        task="inspect repository",
        repository_root=str(tmp_path),
    )

    assert request.task == "inspect repository"
    assert request.repository_root == str(tmp_path)
    assert request.instructions == ""
    assert request.constraints == ()


def test_agent_request_accepts_instructions_and_constraints(
    tmp_path: Path,
) -> None:
    request = AgentRequest(
        task="run engineering checks",
        repository_root=str(tmp_path),
        instructions="be deterministic",
        constraints=("no network", "do not modify tests"),
    )

    assert request.instructions == "be deterministic"
    assert request.constraints == ("no network", "do not modify tests")


def test_mock_agent_completes_request(tmp_path: Path) -> None:
    request = AgentRequest(
        task="inspect repository",
        repository_root=str(tmp_path),
    )

    response = MockAgent().run(request)

    assert response.status == "completed"
    assert response.summary == "Mock execution: inspect repository"
    assert response.changes == ()
    assert response.evidence == ("mock-agent",)
