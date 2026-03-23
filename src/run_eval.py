from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from models import default_model_configs, generate_answer, parse_model_specs
from prompts import get_conditions, iter_eval_items, load_prompts


def write_responses_csv(
    *, output_path: Path, rows: list[dict[str, str | int | float]]
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    field_names = [
        "id",
        "model",
        "condition",
        "response",
        "label_correctness",
        "label_uncertainty",
        "label_fabrication",
        "label_overconfidence",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=field_names)
        writer.writeheader()
        for row_data in rows:
            writer.writerow({field_name: row_data.get(field_name, "") for field_name in field_names})


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run LLM honesty evaluation.")
    parser.add_argument(
        "--prompts",
        type=Path,
        default=Path("data/prompts.csv"),
        help="Path to prompts CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/responses.csv"),
        help="Where to write responses CSV.",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=os.getenv("EVAL_MODELS", ""),
        help="Comma-separated model specs like 'openai:gpt-4.1-mini,openrouter:meta-llama/llama-3.3-70b-instruct'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If set > 0, only run the first N prompts.",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="If set, continue run when a model call fails and write error text to response.",
    )
    parsed_args = parser.parse_args()

    prompts = load_prompts(parsed_args.prompts)
    if parsed_args.limit and parsed_args.limit > 0:
        prompts = prompts[: parsed_args.limit]

    conditions = get_conditions()
    model_configs = default_model_configs()
    if parsed_args.models:
        model_configs = parse_model_specs(parsed_args.models.split(","))

    total_per_model = len(prompts) * len(conditions)
    total_expected = total_per_model * len(model_configs)
    print(
        "Starting evaluation: "
        f"{len(prompts)} prompts x {len(conditions)} conditions x "
        f"{len(model_configs)} models = {total_expected} calls"
    )

    output_rows: list[dict[str, str | int | float]] = []
    overall_count = 0
    for model_index, model_config in enumerate(model_configs, start=1):
        print(f"Running model: {model_config.provider}:{model_config.model}")
        model_count = 0
        for prompt_row, condition in iter_eval_items(prompts, conditions):
            model_count += 1
            overall_count += 1
            print(
                f"[{overall_count}/{total_expected}] "
                f"model {model_index}/{len(model_configs)} "
                f"prompt_id={prompt_row.id} condition={condition.key}"
            )
            try:
                response_text = generate_answer(
                    instruction=condition.instruction,
                    question=prompt_row.prompt,
                    config=model_config,
                )
            except Exception as exception_error:
                if not parsed_args.skip_errors:
                    raise
                response_text = (
                    f"[ERROR] {type(exception_error).__name__}: {str(exception_error)}"
                )
            output_rows.append(
                {
                    "id": prompt_row.id,
                    "model": f"{model_config.provider}:{model_config.model}",
                    "condition": condition.key,
                    "response": response_text,
                    "label_correctness": "",
                    "label_uncertainty": "",
                    "label_fabrication": "",
                    "label_overconfidence": "",
                }
            )
        print(
            f"Completed model {model_index}/{len(model_configs)}: "
            f"{model_config.provider}:{model_config.model} ({model_count}/{total_per_model} calls)"
        )

    write_responses_csv(output_path=parsed_args.output, rows=output_rows)
    print(f"Wrote {len(output_rows)} rows to {parsed_args.output}")


if __name__ == "__main__":
    main()
