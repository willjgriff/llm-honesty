"""CLI entrypoint for the LLM honesty evaluation pipeline."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from evaluation import run_evaluation


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run LLM honesty evaluation.")
    parser.add_argument(
        "--prompts",
        type=Path,
        default=Path("data/prompts.csv"),
        help="Path to prompts CSV (id, category, prompt, ground_truth).",
    )
    parser.add_argument(
        "--pressure-levels",
        type=Path,
        default=Path("data/pressure_levels.csv"),
        help="Path to pressure levels CSV (pressure_level_id, name, prompt).",
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
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="If set, run models one after another instead of in parallel threads.",
    )
    parsed_args = parser.parse_args()

    run_evaluation(
        prompts_path=parsed_args.prompts,
        pressure_levels_path=parsed_args.pressure_levels,
        output_path=parsed_args.output,
        models_override=parsed_args.models,
        limit=parsed_args.limit,
        skip_errors=parsed_args.skip_errors,
        sequential=parsed_args.sequential,
    )


if __name__ == "__main__":
    main()
