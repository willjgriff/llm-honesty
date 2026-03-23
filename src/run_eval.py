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
    fieldnames = [
        "id",
        "model",
        "condition",
        "response",
        "label_correctness",
        "label_uncertainty",
        "label_fabrication",
        "label_overconfidence",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})


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
    args = parser.parse_args()

    prompts = load_prompts(args.prompts)
    if args.limit and args.limit > 0:
        prompts = prompts[: args.limit]

    conditions = get_conditions()
    model_configs = default_model_configs()
    if args.models:
        model_configs = parse_model_specs(args.models.split(","))

    total_per_model = len(prompts) * len(conditions)
    total_expected = total_per_model * len(model_configs)
    print(
        "Starting evaluation: "
        f"{len(prompts)} prompts x {len(conditions)} conditions x "
        f"{len(model_configs)} models = {total_expected} calls"
    )

    out_rows: list[dict[str, str | int | float]] = []
    overall_count = 0
    for model_idx, config in enumerate(model_configs, start=1):
        print(f"Running model: {config.provider}:{config.model}")
        model_count = 0
        for prompt_row, condition in iter_eval_items(prompts, conditions):
            model_count += 1
            overall_count += 1
            print(
                f"[{overall_count}/{total_expected}] "
                f"model {model_idx}/{len(model_configs)} "
                f"prompt_id={prompt_row.id} condition={condition.key}"
            )
            try:
                text = generate_answer(
                    instruction=condition.instruction,
                    question=prompt_row.prompt,
                    config=config,
                )
            except Exception as exc:
                if not args.skip_errors:
                    raise
                text = f"[ERROR] {type(exc).__name__}: {str(exc)}"
            out_rows.append(
                {
                    "id": prompt_row.id,
                    "model": f"{config.provider}:{config.model}",
                    "condition": condition.key,
                    "response": text,
                    "label_correctness": "",
                    "label_uncertainty": "",
                    "label_fabrication": "",
                    "label_overconfidence": "",
                }
            )
        print(
            f"Completed model {model_idx}/{len(model_configs)}: "
            f"{config.provider}:{config.model} ({model_count}/{total_per_model} calls)"
        )

    write_responses_csv(output_path=args.output, rows=out_rows)
    print(f"Wrote {len(out_rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
