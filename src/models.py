"""Model client wrappers and configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from openai import OpenAI


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    temperature: float = 0.2
    timeout_seconds: float = 20.0
    max_retries: int = 0


def _get_client(config: ModelConfig) -> OpenAI:
    if config.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing.")
        return OpenAI(
            api_key=api_key,
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    if config.provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing.")
        return OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    raise ValueError(f"Unsupported provider '{config.provider}'.")


def generate_answer(*, instruction: str, question: str, config: ModelConfig) -> str:
    """Call OpenAI chat completions and return the assistant text."""
    client = _get_client(config)

    responses = client.chat.completions.create(
        model=config.model,
        temperature=config.temperature,
        timeout=config.timeout_seconds,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": question},
        ],
    )

    content = responses.choices[0].message.content
    return (content or "").strip()


def parse_model_specs(specs: Iterable[str]) -> list[ModelConfig]:
    """Parse specs like 'openai:gpt-4.1-mini'."""
    parsed: list[ModelConfig] = []
    for raw in specs:
        value = raw.strip()
        if not value:
            continue
        if ":" not in value:
            raise ValueError(
                f"Invalid model spec '{value}'. Expected format 'provider:model'."
            )
        provider, model = value.split(":", 1)
        provider = provider.strip().lower()
        model = model.strip()
        parsed.append(ModelConfig(provider=provider, model=model))
    if not parsed:
        raise ValueError("No valid model specs were provided.")
    return parsed


def default_model_configs() -> list[ModelConfig]:
    env_specs = os.getenv(
        "EVAL_MODELS",
        (
            "openai:gpt-4.1-mini,"
            "openrouter:meta-llama/llama-3.3-70b-instruct,"
            "openrouter:anthropic/claude-3.5-haiku"
        ),
    )
    specs = [s for s in env_specs.split(",") if s.strip()]
    return parse_model_specs(specs)
