"""Core evaluation pipeline: model calls, parallel orchestration, responses CSV."""

from __future__ import annotations

import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from models import ModelConfig, default_model_configs, generate_answer, parse_model_specs
from prompts import Condition, PromptRow, get_conditions, iter_eval_items, load_prompts

RESPONSES_CSV_FIELD_NAMES = [
    "id",
    "model",
    "condition",
    "response",
    "label_correctness",
    "label_uncertainty",
    "label_fabrication",
    "label_overconfidence",
]


def write_responses_csv(
    *, output_path: Path, rows: list[dict[str, str | int | float]]
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=RESPONSES_CSV_FIELD_NAMES)
        writer.writeheader()
        for row_data in rows:
            writer.writerow(
                {
                    field_name: row_data.get(field_name, "")
                    for field_name in RESPONSES_CSV_FIELD_NAMES
                }
            )


def evaluate_single_model(
    *,
    model_config: ModelConfig,
    prompts: list[PromptRow],
    conditions: list[Condition],
    skip_errors: bool,
    model_index: int,
    total_models: int,
    total_per_model: int,
    progress_lock: threading.Lock,
) -> list[dict[str, str | int | float]]:
    """Run all prompt/condition pairs for one model (safe to run in a worker thread)."""
    model_label = f"{model_config.provider}:{model_config.model}"
    rows: list[dict[str, str | int | float]] = []
    with progress_lock:
        print(f"[parallel] Started model {model_index}/{total_models}: {model_label}")
    model_count = 0
    for prompt_row, condition in iter_eval_items(prompts, conditions):
        model_count += 1
        with progress_lock:
            print(
                f"[parallel] {model_label} "
                f"({model_count}/{total_per_model}) "
                f"prompt_id={prompt_row.id} condition={condition.key}"
            )
        try:
            response_text = generate_answer(
                instruction=condition.instruction,
                question=prompt_row.prompt,
                config=model_config,
            )
        except Exception as exception_error:
            if not skip_errors:
                raise
            response_text = (
                f"[ERROR] {type(exception_error).__name__}: {str(exception_error)}"
            )
        rows.append(
            {
                "id": prompt_row.id,
                "model": model_label,
                "condition": condition.key,
                "response": response_text,
                "label_correctness": "",
                "label_uncertainty": "",
                "label_fabrication": "",
                "label_overconfidence": "",
            }
        )
    with progress_lock:
        print(
            f"[parallel] Completed model {model_index}/{total_models}: "
            f"{model_label} ({model_count}/{total_per_model} calls)"
        )
    return rows


def run_evaluation(
    *,
    prompts_path: Path,
    output_path: Path,
    models_override: str,
    limit: int,
    skip_errors: bool,
    sequential: bool,
) -> None:
    """
    Load prompts, run all configured models (parallel or sequential), write CSV.
    """
    prompts = load_prompts(prompts_path)
    if limit > 0:
        prompts = prompts[:limit]

    conditions = get_conditions()
    model_configs = default_model_configs()
    if models_override.strip():
        model_configs = parse_model_specs(models_override.split(","))

    total_per_model = len(prompts) * len(conditions)
    total_expected = total_per_model * len(model_configs)
    print(
        "Starting evaluation: "
        f"{len(prompts)} prompts x {len(conditions)} conditions x "
        f"{len(model_configs)} models = {total_expected} calls"
    )
    if sequential:
        print("Mode: sequential (one model at a time).")
    else:
        print(
            f"Mode: parallel — up to {len(model_configs)} models calling APIs at the same time."
        )

    output_rows: list[dict[str, str | int | float]] = []
    progress_lock = threading.Lock()

    if sequential:
        for model_index, model_config in enumerate(model_configs, start=1):
            output_rows.extend(
                evaluate_single_model(
                    model_config=model_config,
                    prompts=prompts,
                    conditions=conditions,
                    skip_errors=skip_errors,
                    model_index=model_index,
                    total_models=len(model_configs),
                    total_per_model=total_per_model,
                    progress_lock=progress_lock,
                )
            )
    else:
        submitted_futures = []
        with ThreadPoolExecutor(max_workers=len(model_configs)) as executor:
            for model_index, model_config in enumerate(model_configs, start=1):
                submitted_futures.append(
                    executor.submit(
                        evaluate_single_model,
                        model_config=model_config,
                        prompts=prompts,
                        conditions=conditions,
                        skip_errors=skip_errors,
                        model_index=model_index,
                        total_models=len(model_configs),
                        total_per_model=total_per_model,
                        progress_lock=progress_lock,
                    )
                )
            for future in as_completed(submitted_futures):
                output_rows.extend(future.result())

        condition_order = {
            condition.key: index for index, condition in enumerate(conditions)
        }

        def sort_response_row(row: dict[str, str | int | float]) -> tuple:
            return (
                int(row["id"]),
                condition_order.get(str(row["condition"]), 999),
                str(row["model"]),
            )

        output_rows.sort(key=sort_response_row)

    write_responses_csv(output_path=output_path, rows=output_rows)
    print(f"Wrote {len(output_rows)} rows to {output_path}")
