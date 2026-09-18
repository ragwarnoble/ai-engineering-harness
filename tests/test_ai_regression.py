from harness.ai_regression import build_ai_regression, run_ai_regression


def test_build_ai_regression() -> None:
    spec = build_ai_regression()

    assert spec.name == "ai_regression"
    assert len(spec.cases) == 3


def test_ai_regression_cases_have_stable_expected_values() -> None:
    spec = build_ai_regression()

    for case in spec.cases:
        assert case.input == case.expected


def test_ai_regression_passes() -> None:
    assert run_ai_regression() is True
