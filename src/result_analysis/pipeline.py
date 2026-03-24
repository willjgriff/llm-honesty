"""Orchestrate loading responses, scoring, CSV export, and charts."""

from __future__ import annotations

from pathlib import Path

from result_analysis.charts import (
    build_false_denial_by_model_line_chart,
    build_false_denial_line_chart,
    build_model_yes_to_no_flip_bar_chart,
    build_yes_no_bar_chart,
)
from result_analysis.csv_writes import (
    write_false_denial_by_model_csv,
    write_false_denial_csv,
    write_model_yes_to_no_flip_csv,
    write_yes_no_counts_csv,
)
from result_analysis.scoring import (
    compute_false_denial_by_pressure_level,
    compute_false_denial_by_pressure_level_and_model,
    compute_yes_to_no_flip_rate_when_pressured_by_model,
    count_yes_no_by_pressure_level,
    read_responses,
)


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
    summary_csv_path = write_yes_no_counts_csv(
        output_dir, sorted_pressure_levels, counts_by_level
    )
    yes_no_plot_path = build_yes_no_bar_chart(
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
    false_denial_csv_path = write_false_denial_csv(
        output_dir, false_denial_levels, false_denial_summary
    )
    false_denial_plot_path = build_false_denial_line_chart(
        output_dir, false_denial_levels, false_denial_summary, total_neutral_yes
    )
    print(f"[analysis] False denial CSV: {false_denial_csv_path}")
    print(f"[analysis] False denial plot: {false_denial_plot_path}")

    print("[analysis] Calculating false denial rate by pressure level and model")
    false_denial_by_model_summary, total_neutral_yes_by_model = (
        compute_false_denial_by_pressure_level_and_model(responses)
    )
    sorted_models = sorted(
        {summary_key[2] for summary_key in false_denial_by_model_summary.keys()}
    )
    by_model_csv_path = write_false_denial_by_model_csv(
        output_dir,
        false_denial_levels,
        sorted_models,
        false_denial_by_model_summary,
    )
    by_model_plot_path = build_false_denial_by_model_line_chart(
        output_dir,
        false_denial_levels,
        sorted_models,
        false_denial_by_model_summary,
        total_neutral_yes_by_model,
    )
    print(f"[analysis] Per-model false denial CSV: {by_model_csv_path}")
    print(f"[analysis] Per-model false denial plot: {by_model_plot_path}")

    print("[analysis] Calculating Yes→No flip rate when pressured (by model)")
    flip_summary_by_model = compute_yes_to_no_flip_rate_when_pressured_by_model(
        responses
    )
    sorted_models_for_flip = sorted(flip_summary_by_model.keys())
    if sorted_models_for_flip:
        flip_csv_path = write_model_yes_to_no_flip_csv(
            output_dir, sorted_models_for_flip, flip_summary_by_model
        )
        flip_plot_path = build_model_yes_to_no_flip_bar_chart(
            output_dir, sorted_models_for_flip, flip_summary_by_model
        )
        print(f"[analysis] Model Yes→No flip CSV: {flip_csv_path}")
        print(f"[analysis] Model Yes→No flip plot: {flip_plot_path}")
    else:
        print(
            "[analysis] Skipping model Yes→No flip chart (no questions with neutral "
            "'Yes' in the data)."
        )
