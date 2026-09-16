from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from harness.gate import QualityGateResult


def write_gate_evidence(
    result: QualityGateResult,
    path: Path,
) -> None:
    """Persist a quality-gate result as deterministic JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)

    payload = asdict(result)

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
