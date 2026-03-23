"""Prompt and pressure-level loading."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PromptRow:
    id: int
    category: str
    prompt: str
    ground_truth: str


@dataclass(frozen=True)
class PressureLevel:
    """One row from data/pressure_levels.csv (system instruction in column 'prompt')."""

    pressure_level_id: int
    name: str
    system_instruction: str


def load_prompts(csv_path: Path) -> list[PromptRow]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        prompt_rows: list[PromptRow] = []
        for row_data in reader:
            prompt_rows.append(
                PromptRow(
                    id=int(row_data["id"]),
                    category=(row_data.get("category") or "").strip(),
                    prompt=(row_data.get("prompt") or "").strip(),
                    ground_truth=(row_data.get("ground_truth") or "").strip(),
                )
            )
    return prompt_rows


def load_pressure_levels(csv_path: Path) -> list[PressureLevel]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        levels: list[PressureLevel] = []
        for row_data in reader:
            levels.append(
                PressureLevel(
                    pressure_level_id=int(row_data["pressure_level_id"]),
                    name=(row_data.get("name") or "").strip(),
                    system_instruction=(row_data.get("prompt") or "").strip(),
                )
            )
    levels.sort(key=lambda level: level.pressure_level_id)
    return levels


def iter_prompt_pressure_pairs(
    prompts: Iterable[PromptRow], pressure_levels: Iterable[PressureLevel]
) -> Iterable[tuple[PromptRow, PressureLevel]]:
    for prompt_row in prompts:
        for pressure_level in pressure_levels:
            yield prompt_row, pressure_level
