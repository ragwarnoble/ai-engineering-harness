from harness.engineering_evaluation import (
    build_engineering_evaluation,
    run_engineering_evaluation,
)


def test_build_engineering_evaluation() -> None:
    spec = build_engineering_evaluation()

    assert spec.name == "engineering_evaluation"
    assert len(spec.cases) == 2


def test_engineering_evaluation_passes() -> None:
    assert run_engineering_evaluation() is True
