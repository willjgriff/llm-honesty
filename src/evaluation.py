"""Core evaluation pipeline: two-turn Q&A, parallel orchestration, responses CSV."""

from __future__ import annotations

import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from models import (
    ModelConfig,
    default_model_configs,
    generate_chat_completion,
    parse_model_specs,
)
from prompts import (
    DEFAULT_SYSTEM_INSTRUCTION,
    FOLLOWUP_CHALLENGE_MESSAGE,
    PromptRow,
    load_prompts,
)

RESPONSES_CSV_FIELD_NAMES = [
    "id",
    "category",
    "model",
    "question",
    "first_response",
    "second_response",
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
    skip_errors: bool,
    model_index: int,
    total_models: int,
    total_per_model: int,
    progress_lock: threading.Lock,
) -> list[dict[str, str | int | float]]:
    """Run two-turn evaluation for every prompt on one model (worker-thread safe)."""
    model_label = f"{model_config.provider}:{model_config.model}"
    rows: list[dict[str, str | int | float]] = []
    with progress_lock:
        print(f"[parallel] Started model {model_index}/{total_models}: {model_label}")
    prompt_index = 0
    for prompt_row in prompts:
        prompt_index += 1
        with progress_lock:
            print(
                f"[parallel] {model_label} "
                f"({prompt_index}/{total_per_model}) "
                f"prompt_id={prompt_row.id}"
            )
        first_messages: list[dict[str, str]] = [
            {"role": "system", "content": DEFAULT_SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt_row.prompt},
        ]
        try:
            first_response = generate_chat_completion(
                messages=first_messages, config=model_config
            )
        except Exception as exception_error:
            if not skip_errors:
                raise
            first_response = (
                f"[ERROR] {type(exception_error).__name__}: {str(exception_error)}"
            )
            second_response = "[SKIPPED] first turn failed"
        else:
            second_messages = first_messages + [
                {"role": "assistant", "content": first_response},
                {"role": "user", "content": FOLLOWUP_CHALLENGE_MESSAGE},
            ]
            try:
                second_response = generate_chat_completion(
                    messages=second_messages, config=model_config
                )
            except Exception as exception_error:
                if not skip_errors:
                    raise
                second_response = (
                    f"[ERROR] {type(exception_error).__name__}: {str(exception_error)}"
                )
        rows.append(
            {
                "id": prompt_row.id,
                "category": prompt_row.category,
                "model": model_label,
                "question": prompt_row.prompt,
                "first_response": first_response,
                "second_response": second_response,
                "label_correctness": "",
                "label_uncertainty": "",
                "label_fabrication": "",
                "label_overconfidence": "",
            }
        )
    with progress_lock:
        print(
            f"[parallel] Completed model {model_index}/{total_models}: "
            f"{model_label} ({prompt_index}/{total_per_model} prompts, 2 turns each)"
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
    Each prompt yields one row with first and second model replies.
    """
    prompts = load_prompts(prompts_path)
    if limit > 0:
        prompts = prompts[:limit]

    model_configs = default_model_configs()
    if models_override.strip():
        model_configs = parse_model_specs(models_override.split(","))

    total_per_model = len(prompts)
    api_calls_per_model = total_per_model * 2
    total_api_calls = api_calls_per_model * len(model_configs)
    print(
        "Starting evaluation: "
        f"{len(prompts)} prompts x {len(model_configs)} models; "
        f"2 API turns per prompt → {total_api_calls} total API calls"
    )
    print(f"Follow-up message: {FOLLOWUP_CHALLENGE_MESSAGE!r}")
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
                        skip_errors=skip_errors,
                        model_index=model_index,
                        total_models=len(model_configs),
                        total_per_model=total_per_model,
                        progress_lock=progress_lock,
                    )
                )
            for future in as_completed(submitted_futures):
                output_rows.extend(future.result())

        def sort_response_row(row: dict[str, str | int | float]) -> tuple:
            return (int(row["id"]), str(row["model"]))

        output_rows.sort(key=sort_response_row)

    write_responses_csv(output_path=output_path, rows=output_rows)
    print(f"Wrote {len(output_rows)} rows to {output_path}")
