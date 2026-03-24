"""Analysis helpers for aggregate metrics and charts."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from scorer import (
    compute_false_denial_by_pressure_level,
    compute_false_denial_by_pressure_level_and_model,
    compute_yes_to_no_flip_rate_when_pressured_by_model,
    count_yes_no_by_pressure_level,
    read_responses,
)


def _false_denial_aggregate_chart_caption() -> str:
    return (
        "Rates are calculated over cases where the neutral response was 'Yes'.\n"
        "False denial rate = % of true facts denied under pressure. "
        "Other/refusal rate = % answered with non-Yes/No when under pressure."
    )


def _configure_pressure_level_rate_axes(
    pressure_level_ids: list[int],
    pressure_level_tick_labels: list[str],
) -> None:
    plt.xticks(pressure_level_ids, pressure_level_tick_labels, rotation=20, ha="right")
    plt.xlabel("Pressure level")
    plt.ylabel("Rate (%)")
    plt.ylim(bottom=0)


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
    plt.suptitle("Yes/No counts by pressure level", y=0.97)
    plt.title(
        "In this dataset, 'Yes' is the correct answer. "
        "'No' indicates denial under pressure; 'Other' is non-Yes/No.",
        fontsize=10,
        pad=6,
    )
    plt.legend()
    plt.tight_layout(rect=(0, 0, 1, 0.93))

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
    _configure_pressure_level_rate_axes(pressure_level_ids, pressure_level_labels)
    plt.suptitle("False denial and other/refusal rates by pressure level", y=0.965)
    plt.title(
        _false_denial_aggregate_chart_caption(),
        fontsize=10,
        pad=4,
    )
    plt.legend()
    # Keep title and description close while still preventing clipping.
    plt.tight_layout(rect=(0, 0, 1, 0.96))

    false_denial_plot_path = output_dir / "pressure_level_false_denial_rate.png"
    plt.savefig(false_denial_plot_path, dpi=150)
    plt.close()
    return false_denial_plot_path


def _write_false_denial_by_model_csv(
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


def _build_false_denial_by_model_line_chart(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    sorted_models: list[str],
    false_denial_by_model_summary: dict[tuple[int, str, str], dict[str, float]],
    total_neutral_yes_by_model: dict[str, int],
) -> Path:
    print("[analysis] Building per-model false denial line chart")
    pressure_level_ids = [
        pressure_level_id for pressure_level_id, _ in sorted_pressure_levels
    ]
    pressure_level_tick_labels = [
        f"{pressure_level_id}:{pressure_name}"
        for pressure_level_id, pressure_name in sorted_pressure_levels
    ]
    denominator_note = ", ".join(
        f"{model}={total_neutral_yes_by_model.get(model, 0)}"
        for model in sorted_models
    )
    print(
        f"[analysis] Per-model neutral-Yes denominators (total_neutral_yes): {denominator_note}"
    )

    colour_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    plt.figure(figsize=(11, 5.5))
    for model_index, model in enumerate(sorted_models):
        line_colour = colour_cycle[model_index % len(colour_cycle)]
        false_denial_rate_percentages = [
            false_denial_by_model_summary[
                (pressure_level_id, pressure_name, model)
            ]["false_denial_rate_percent"]
            for pressure_level_id, pressure_name in sorted_pressure_levels
        ]
        other_rate_percentages = [
            false_denial_by_model_summary[
                (pressure_level_id, pressure_name, model)
            ]["other_rate_percent"]
            for pressure_level_id, pressure_name in sorted_pressure_levels
        ]
        plt.plot(
            pressure_level_ids,
            false_denial_rate_percentages,
            color=line_colour,
            linestyle="-",
            marker="o",
            label=f"{model} — false denial",
        )
        plt.plot(
            pressure_level_ids,
            other_rate_percentages,
            color=line_colour,
            linestyle="--",
            marker="s",
            label=f"{model} — other/refusal",
        )

    _configure_pressure_level_rate_axes(pressure_level_ids, pressure_level_tick_labels)
    plt.suptitle(
        "False denial and other/refusal rates by pressure level (per model)",
        y=0.965,
    )
    plt.title(
        "Denominator per model: its own count of neutral 'Yes' responses. "
        "Solid = % pressured 'No'; dashed = % non-Yes/No under pressure.",
        fontsize=10,
        pad=4,
    )
    plt.legend(loc="best", fontsize=7)
    plt.tight_layout(rect=(0, 0, 1, 0.96))

    plot_path = output_dir / "pressure_level_false_denial_rate_by_model.png"
    plt.savefig(plot_path, dpi=150)
    plt.close()
    return plot_path


def _write_model_yes_to_no_flip_csv(
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


def _build_model_yes_to_no_flip_bar_chart(
    output_dir: Path,
    sorted_models: list[str],
    flip_summary_by_model: dict[str, dict[str, float]],
) -> Path:
    print("[analysis] Building model Yes→No flip bar chart")
    flip_rate_percentages = [
        flip_summary_by_model[model]["yes_to_no_flip_rate_percent"]
        for model in sorted_models
    ]
    model_positions = range(len(sorted_models))

    figure, axes = plt.subplots(figsize=(10, 4.8))
    axes.bar(list(model_positions), flip_rate_percentages, color="steelblue")
    axes.set_xticks(list(model_positions))
    axes.set_xticklabels(sorted_models, rotation=25, ha="right")
    axes.set_ylabel(
        "% of questions",
        fontsize=10,
    )
    axes.set_xlabel("Model")
    axes.set_title(
        "% of questions flip from\n yes to no under pressure per model",
        fontsize=10,
        pad=4,
    )
    axes.set_ylim(bottom=0)
    figure.tight_layout(rect=(0.06, 0.06, 0.98, 0.88))

    plot_path = output_dir / "model_answer_change_when_pressured.png"
    figure.savefig(plot_path, dpi=150, bbox_inches="tight", pad_inches=0.15)
    plt.close(figure)
    return plot_path


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

    print("[analysis] Calculating false denial rate by pressure level and model")
    false_denial_by_model_summary, total_neutral_yes_by_model = (
        compute_false_denial_by_pressure_level_and_model(responses)
    )
    sorted_models = sorted(
        {summary_key[2] for summary_key in false_denial_by_model_summary.keys()}
    )
    by_model_csv_path = _write_false_denial_by_model_csv(
        output_dir,
        false_denial_levels,
        sorted_models,
        false_denial_by_model_summary,
    )
    by_model_plot_path = _build_false_denial_by_model_line_chart(
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
        flip_csv_path = _write_model_yes_to_no_flip_csv(
            output_dir, sorted_models_for_flip, flip_summary_by_model
        )
        flip_plot_path = _build_model_yes_to_no_flip_bar_chart(
            output_dir, sorted_models_for_flip, flip_summary_by_model
        )
        print(f"[analysis] Model Yes→No flip CSV: {flip_csv_path}")
        print(f"[analysis] Model Yes→No flip plot: {flip_plot_path}")
    else:
        print(
            "[analysis] Skipping model Yes→No flip chart (no questions with neutral "
            "'Yes' in the data)."
        )
