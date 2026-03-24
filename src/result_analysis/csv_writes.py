"""Write analysis summary CSV files."""

from __future__ import annotations

import csv
from pathlib import Path


def write_yes_no_counts_csv(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    counts_by_pressure_level: dict[tuple[int, str], dict[str, int]],
) -> Path:
    summary_csv_path = output_dir / "pressure_level_yes_no_counts.csv"
    print(f"[analysis] Writing summary CSV: {summary_csv_path}")
    with summary_csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "pressure_level_id",
                "pressure_name",
                "yes_count",
                "no_count",
                "other_count",
            ],
        )
        writer.writeheader()
        for pressure_level_id, pressure_name in sorted_pressure_levels:
            level_counts = counts_by_pressure_level[(pressure_level_id, pressure_name)]
            writer.writerow(
                {
                    "pressure_level_id": pressure_level_id,
                    "pressure_name": pressure_name,
                    "yes_count": level_counts["Yes"],
                    "no_count": level_counts["No"],
                    "other_count": level_counts["Other"],
                }
            )
    return summary_csv_path


def write_false_denial_csv(
    output_dir: Path,
    false_denial_levels: list[tuple[int, str]],
    false_denial_summary: dict[tuple[int, str], dict[str, float]],
) -> Path:
    false_denial_csv_path = output_dir / "pressure_level_false_denial_rate.csv"
    print(f"[analysis] Writing false denial CSV: {false_denial_csv_path}")
    with false_denial_csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "pressure_level_id",
                "pressure_name",
                "false_denial_count",
                "other_response_count",
                "total_neutral_yes",
                "false_denial_rate_percent",
                "other_rate_percent",
            ],
        )
        writer.writeheader()
        for pressure_level_id, pressure_name in false_denial_levels:
            level_data = false_denial_summary[(pressure_level_id, pressure_name)]
            writer.writerow(
                {
                    "pressure_level_id": pressure_level_id,
                    "pressure_name": pressure_name,
                    "false_denial_count": int(level_data["false_denial_count"]),
                    "other_response_count": int(level_data["other_response_count"]),
                    "total_neutral_yes": int(level_data["total_neutral_yes"]),
                    "false_denial_rate_percent": round(
                        level_data["false_denial_rate_percent"], 4
                    ),
                    "other_rate_percent": round(level_data["other_rate_percent"], 4),
                }
            )
    return false_denial_csv_path


def write_false_denial_by_model_csv(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    sorted_models: list[str],
    false_denial_by_model_summary: dict[tuple[int, str, str], dict[str, float]],
) -> Path:
    csv_path = output_dir / "pressure_level_false_denial_rate_by_model.csv"
    print(f"[analysis] Writing per-model false denial CSV: {csv_path}")
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "pressure_level_id",
                "pressure_name",
                "model",
                "false_denial_count",
                "other_response_count",
                "total_neutral_yes",
                "false_denial_rate_percent",
                "other_rate_percent",
            ],
        )
        writer.writeheader()
        for pressure_level_id, pressure_name in sorted_pressure_levels:
            for model in sorted_models:
                level_data = false_denial_by_model_summary[
                    (pressure_level_id, pressure_name, model)
                ]
                writer.writerow(
                    {
                        "pressure_level_id": pressure_level_id,
                        "pressure_name": pressure_name,
                        "model": model,
                        "false_denial_count": int(level_data["false_denial_count"]),
                        "other_response_count": int(level_data["other_response_count"]),
                        "total_neutral_yes": int(level_data["total_neutral_yes"]),
                        "false_denial_rate_percent": round(
                            level_data["false_denial_rate_percent"], 4
                        ),
                        "other_rate_percent": round(level_data["other_rate_percent"], 4),
                    }
                )
    return csv_path


def write_model_yes_to_no_flip_csv(
    output_dir: Path,
    sorted_models: list[str],
    flip_summary_by_model: dict[str, dict[str, float]],
) -> Path:
    csv_path = output_dir / "model_answer_change_when_pressured.csv"
    print(f"[analysis] Writing model Yes→No flip CSV: {csv_path}")
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "model",
                "yes_to_no_flip_question_count",
                "neutral_yes_question_count",
                "yes_to_no_flip_rate_percent",
            ],
        )
        writer.writeheader()
        for model in sorted_models:
            row = flip_summary_by_model[model]
            writer.writerow(
                {
                    "model": model,
                    "yes_to_no_flip_question_count": int(
                        row["yes_to_no_flip_question_count"]
                    ),
                    "neutral_yes_question_count": int(row["neutral_yes_question_count"]),
                    "yes_to_no_flip_rate_percent": round(
                        row["yes_to_no_flip_rate_percent"], 4
                    ),
                }
            )
    return csv_path
