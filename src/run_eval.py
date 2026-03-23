from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from dotenv import load_dotenv

from models import default_model_config, generate_answer
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
        "--model",
        type=str,
        default=os.getenv("OPENAI_MODEL", ""),
        help="Override model name (else uses OPENAI_MODEL).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If set > 0, only run the first N prompts.",
    )
    args = parser.parse_args()

    prompts = load_prompts(args.prompts)
    if args.limit and args.limit > 0:
        prompts = prompts[: args.limit]

    conditions = get_conditions()
    config = default_model_config()
    if args.model:
        config = type(config)(model=args.model, temperature=config.temperature)

    out_rows: list[dict[str, str | int | float]] = []
    for prompt_row, condition in iter_eval_items(prompts, conditions):
        text = generate_answer(
            instruction=condition.instruction, question=prompt_row.prompt, config=config
        )
        out_rows.append(
            {
                "id": prompt_row.id,
                "model": config.model,
                "condition": condition.key,
                "response": text,
                "label_correctness": "",
                "label_uncertainty": "",
                "label_fabrication": "",
                "label_overconfidence": "",
            }
        )

    write_responses_csv(output_path=args.output, rows=out_rows)
    print(f"Wrote {len(out_rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
