"""Response scoring utilities."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


def normalize_yes_no(value: str) -> str:
    """
    Map free-form model output to Yes/No/Other.
    Examples:
    - "Yes", "Yes." -> "Yes"
    - "No", "No." -> "No"
    """
    normalized = value.strip().lower()
    if normalized.startswith("yes"):
        return "Yes"
    if normalized.startswith("no"):
        return "No"
    return "Other"


def read_response_rows(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def count_yes_no_by_pressure_level(
    rows: list[dict[str, Any]],
) -> dict[tuple[int, str], dict[str, int]]:
    counts_by_level: dict[tuple[int, str], dict[str, int]] = defaultdict(
        lambda: {"Yes": 0, "No": 0, "Other": 0}
    )
    for row in rows:
        pressure_level_id_raw = (row.get("pressure_level_id") or "").strip()
        pressure_name = (row.get("pressure_name") or "").strip() or "unknown"
        if not pressure_level_id_raw:
            continue
        pressure_level_id = int(pressure_level_id_raw)
        response_text = (row.get("response") or "").strip()
        label = normalize_yes_no(response_text)
        counts_by_level[(pressure_level_id, pressure_name)][label] += 1
    return counts_by_level
