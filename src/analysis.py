"""Analysis helpers for aggregate metrics and charts."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from scorer import count_yes_no_by_pressure_level, read_response_rows


def run_yes_no_analysis(*, responses_csv: Path, output_dir: Path) -> None:
    """
    Count Yes/No/Other by pressure level and save:
    - results/pressure_level_yes_no_counts.csv
    - results/pressure_level_yes_no_counts.png
    """
    print(f"[analysis] Reading responses from: {responses_csv}")
    rows = read_response_rows(responses_csv)
    if not rows:
        raise ValueError(f"No rows found in {responses_csv}")
    print(f"[analysis] Loaded {len(rows)} rows")
    print("[analysis] Scoring responses into Yes/No/Other buckets")
    counts_by_level = count_yes_no_by_pressure_level(rows)

    sorted_levels = sorted(counts_by_level.keys(), key=lambda item: item[0])
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[analysis] Found {len(sorted_levels)} pressure levels")

    summary_csv_path = output_dir / "pressure_level_yes_no_counts.csv"
    print(f"[analysis] Writing summary CSV: {summary_csv_path}")
    with summary_csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["pressure_level_id", "pressure_name", "yes_count", "no_count", "other_count"],
        )
        writer.writeheader()
        for pressure_level_id, pressure_name in sorted_levels:
            level_counts = counts_by_level[(pressure_level_id, pressure_name)]
            writer.writerow(
                {
                    "pressure_level_id": pressure_level_id,
                    "pressure_name": pressure_name,
                    "yes_count": level_counts["Yes"],
                    "no_count": level_counts["No"],
                    "other_count": level_counts["Other"],
                }
            )

    x_labels = [f"{level_id}:{level_name}" for level_id, level_name in sorted_levels]
    yes_counts = [counts_by_level[level]["Yes"] for level in sorted_levels]
    no_counts = [counts_by_level[level]["No"] for level in sorted_levels]
    other_counts = [counts_by_level[level]["Other"] for level in sorted_levels]

    x_positions = range(len(x_labels))
    width = 0.25

    print("[analysis] Building bar chart")
    plt.figure(figsize=(10, 5))
    plt.bar([x - width for x in x_positions], yes_counts, width=width, label="Yes")
    plt.bar(list(x_positions), no_counts, width=width, label="No")
    plt.bar([x + width for x in x_positions], other_counts, width=width, label="Other")
    plt.xticks(list(x_positions), x_labels, rotation=20, ha="right")
    plt.ylabel("Response count")
    plt.title("Yes/No counts by pressure level")
    plt.legend()
    plt.tight_layout()

    plot_path = output_dir / "pressure_level_yes_no_counts.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()

    print(f"[analysis] Analysis summary CSV: {summary_csv_path}")
    print(f"[analysis] Analysis plot: {plot_path}")
