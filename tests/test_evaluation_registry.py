from harness.evaluation_registry import run_configured_evaluations


def test_runs_available_required_evaluations() -> None:
    results = run_configured_evaluations(
        (
            "engineering_evaluation",
            "ai_regression",
            "ai_evaluation",
        )
    )

    assert results == {
        "engineering_evaluation": True,
        "ai_regression": True,
    }


def test_skips_unknown_evaluations() -> None:
    results = run_configured_evaluations(
        (
            "unknown_evaluation",
            "another_unknown_evaluation",
        )
    )

    assert results == {}
