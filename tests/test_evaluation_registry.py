from harness.evaluation_registry import run_configured_evaluations


def test_runs_available_required_evaluation() -> None:
    results = run_configured_evaluations(
        (
            "engineering_evaluation",
            "ai_evaluation",
        )
    )

    assert results == {
        "engineering_evaluation": True,
    }


def test_returns_empty_for_unconfigured_evaluations() -> None:
    results = run_configured_evaluations(
        (
            "ai_evaluation",
            "ai_regression",
        )
    )

    assert results == {}
