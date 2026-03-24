"""Analysis helpers for aggregate metrics and charts."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from scorer import (
    compute_false_denial_by_pressure_level,
    count_yes_no_by_pressure_level,
    read_responses,
)


def _write_yes_no_counts_csv(
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


def _build_yes_no_bar_chart(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    counts_by_pressure_level: dict[tuple[int, str], dict[str, int]],
) -> Path:
    pressure_level_labels = [
        f"{pressure_level_id}:{pressure_name}"
        for pressure_level_id, pressure_name in sorted_pressure_levels
    ]
    yes_counts = [
        counts_by_pressure_level[pressure_level]["Yes"]
        for pressure_level in sorted_pressure_levels
    ]
    no_counts = [
        counts_by_pressure_level[pressure_level]["No"]
        for pressure_level in sorted_pressure_levels
    ]
    other_counts = [
        counts_by_pressure_level[pressure_level]["Other"]
        for pressure_level in sorted_pressure_levels
    ]

    pressure_level_positions = range(len(pressure_level_labels))
    bar_width = 0.25

    print("[analysis] Building bar chart")
    plt.figure(figsize=(10, 5))
    plt.bar(
        [position - bar_width for position in pressure_level_positions],
        yes_counts,
        width=bar_width,
        label="Yes",
    )
    plt.bar(
        list(pressure_level_positions),
        no_counts,
        width=bar_width,
        label="No",
    )
    plt.bar(
        [position + bar_width for position in pressure_level_positions],
        other_counts,
        width=bar_width,
        label="Other",
    )
    plt.xticks(
        list(pressure_level_positions), pressure_level_labels, rotation=20, ha="right"
    )
    plt.ylabel("Response count")
    plt.title("Yes/No counts by pressure level")
    plt.legend()
    plt.tight_layout()

    chart_path = output_dir / "pressure_level_yes_no_counts.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()
    return chart_path


def _write_false_denial_csv(
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


def _build_false_denial_line_chart(
    output_dir: Path,
    false_denial_levels: list[tuple[int, str]],
    false_denial_summary: dict[tuple[int, str], dict[str, float]],
    total_neutral_yes: int,
) -> Path:
    print(
        f"[analysis] Building false denial line chart (denominator total_neutral_yes={total_neutral_yes})"
    )
    pressure_level_ids = [
        pressure_level_id for pressure_level_id, _ in false_denial_levels
    ]
    false_denial_rate_percentages = [
        false_denial_summary[(pressure_level_id, pressure_name)][
            "false_denial_rate_percent"
        ]
        for pressure_level_id, pressure_name in false_denial_levels
    ]
    other_rate_percentages = [
        false_denial_summary[(pressure_level_id, pressure_name)]["other_rate_percent"]
        for pressure_level_id, pressure_name in false_denial_levels
    ]
    pressure_level_labels = [
        f"{pressure_level_id}:{pressure_name}"
        for pressure_level_id, pressure_name in false_denial_levels
    ]

    plt.figure(figsize=(10, 5.5))
    plt.plot(
        pressure_level_ids,
        false_denial_rate_percentages,
        marker="o",
        label="False denial rate",
    )
    plt.plot(
        pressure_level_ids,
        other_rate_percentages,
        marker="o",
        label="Other/refusal rate",
    )
    plt.xticks(pressure_level_ids, pressure_level_labels, rotation=20, ha="right")
    plt.xlabel("Pressure level")
    plt.ylabel("Rate (%)")
    plt.suptitle("False denial and other/refusal rates by pressure level", y=0.965)
    plt.title(
        "Rates are calculated over cases where the neutral response was 'Yes'.\n"
        "False denial rate = % of true facts denied under pressure. "
        "Other/refusal rate = % answered with non-Yes/No when under pressure.",
        fontsize=10,
        pad=4,
    )
    plt.legend()
    plt.ylim(bottom=0)
    # Keep title and description close while still preventing clipping.
    plt.tight_layout(rect=(0, 0, 1, 0.96))

    false_denial_plot_path = output_dir / "pressure_level_false_denial_rate.png"
    plt.savefig(false_denial_plot_path, dpi=150)
    plt.close()
    return false_denial_plot_path


def run_yes_no_analysis(*, responses_csv: Path, output_dir: Path) -> None:
    """
    Count Yes/No/Other by pressure level and save:
    - results/pressure_level_yes_no_counts.csv
    - results/pressure_level_yes_no_counts.png
    """
    print(f"[analysis] Reading responses from: {responses_csv}")
    responses = read_responses(responses_csv)
    if not responses:
        raise ValueError(f"No rows found in {responses_csv}")
    print(f"[analysis] Loaded {len(responses)} responses")
    print("[analysis] Scoring responses into Yes/No/Other buckets")
    counts_by_level = count_yes_no_by_pressure_level(responses)

    sorted_pressure_levels = sorted(
        counts_by_level.keys(), key=lambda pressure_level: pressure_level[0]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[analysis] Found {len(sorted_pressure_levels)} pressure levels")
    summary_csv_path = _write_yes_no_counts_csv(
        output_dir, sorted_pressure_levels, counts_by_level
    )
    yes_no_plot_path = _build_yes_no_bar_chart(
        output_dir, sorted_pressure_levels, counts_by_level
    )
    print(f"[analysis] Analysis summary CSV: {summary_csv_path}")
    print(f"[analysis] Analysis plot: {yes_no_plot_path}")

    print("[analysis] Calculating false denial rate by pressure level")
    false_denial_summary, total_neutral_yes = compute_false_denial_by_pressure_level(
        responses
    )
    false_denial_levels = sorted(
        false_denial_summary.keys(), key=lambda pressure_level: pressure_level[0]
    )
    false_denial_csv_path = _write_false_denial_csv(
        output_dir, false_denial_levels, false_denial_summary
    )
    false_denial_plot_path = _build_false_denial_line_chart(
        output_dir, false_denial_levels, false_denial_summary, total_neutral_yes
    )
    print(f"[analysis] False denial CSV: {false_denial_csv_path}")
    print(f"[analysis] False denial plot: {false_denial_plot_path}")
