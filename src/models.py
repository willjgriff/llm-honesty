"""Model client wrappers and configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass(frozen=True)
class ModelConfig:
    model: str
    temperature: float = 0.2
    timeout_seconds: float = 20.0
    max_retries: int = 0


def _get_client(config: ModelConfig) -> OpenAI:
    # Uses OPENAI_API_KEY by default.
    return OpenAI(timeout=config.timeout_seconds, max_retries=config.max_retries)


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


def default_model_config() -> ModelConfig:
    return ModelConfig(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
