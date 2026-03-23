"""Model client wrappers and configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass(frozen=True)
class ModelConfig:
    model: str
    temperature: float = 0.2


def _get_client() -> OpenAI:
    # Uses OPENAI_API_KEY by default.
    return OpenAI()


def generate_answer(*, instruction: str, question: str, config: ModelConfig) -> str:
    """Call OpenAI chat completions and return the assistant text."""
    client = _get_client()

    resp = client.chat.completions.create(
        model=config.model,
        temperature=config.temperature,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": question},
        ],
    )

    content = resp.choices[0].message.content
    return (content or "").strip()


def default_model_config() -> ModelConfig:
    return ModelConfig(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
