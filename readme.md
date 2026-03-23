# LLM honesty evaluation

Pipeline to **collect model answers** to a fixed set of **open-ended questions** (from a CSV) under **different system-prompt conditions**, across **one or more models** (OpenAI and/or OpenRouter). The aim is to support work that **examines honesty-related behaviour**: e.g. whether pressure to sound confident or avoid “I don’t know” is associated with **more errors, overconfident wording, or fabricated claims**. The code does not score honesty automatically. It currently produces `results/responses.csv` with empty label columns for **you (or a later scorer which is coming soon) to fill in** against rubrics like correctness, appropriate uncertainty, fabrication, and overconfidence.

---

## What the runner does

1. Loads rows from **`data/prompts.csv`** (`id`, `category`, `prompt`). Questions are **not** constrained to yes/no; they can be factual, vague, impossible to verify, etc., depending on what you put in the file.
2. For **each** prompt, **each** [condition](#conditions), and **each** configured model, it sends one chat request: **system** = that condition’s instruction, **user** = the prompt text.
3. Writes **`results/responses.csv`**: one row per (prompt × condition × model), with the raw `response` plus optional manual labels.

So you can later compare how the **same question** is answered under **neutral** vs **pressure** instructions, and across **models**.

---

## Conditions

Conditions are **system prompts** defined in code (`src/prompts.py` → `get_conditions()`), not in the CSV. The current set is:

| Key | Role |
|-----|------|
| `baseline` | Neutral: answer accurately and clearly. |
| `confidence_pressure` | Push toward sounding confident and avoiding uncertainty. |
| `goal_pressure` | Push toward usefulness / “best answer” even when uncertain. |
| `no_uncertainty` | Forbid hedging; require a definite answer. |

These are **experimental framings** to stress-test behaviour, not endorsements of how models should be deployed.

---

## What you need

- **Python 3.9+**
- **`OPENAI_API_KEY`** for `openai:…` models
- **`OPENROUTER_API_KEY`** for `openrouter:…` models ([OpenRouter](https://openrouter.ai/))

---

## Run it (quick start)

From the **project root** (`llm-honesty/`):

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`: set keys and optionally **`EVAL_MODELS`** (comma-separated `provider:model` list, e.g. `openai:gpt-4.1-mini,openrouter:anthropic/claude-3.5-haiku`).

```bash
python3 src/run_eval.py
```

By default this **overwrites** `results/responses.csv`.

---

## CLI options

| Flag | Purpose |
|------|--------|
| `--prompts PATH` | Prompts CSV (default: `data/prompts.csv`) |
| `--output PATH` | Output CSV (default: `results/responses.csv`) |
| `--models "openai:…,openrouter:…"` | Override models; if omitted, uses `EVAL_MODELS` from `.env` |
| `--limit N` | Only first *N* prompts |
| `--skip-errors` | On API errors, write `[ERROR] …` into `response` and continue |
| `--sequential` | One model after another (default: **parallel** across models) |

Example:

```bash
python3 src/run_eval.py --limit 2 --sequential --skip-errors
```

---

## Data format

**`data/prompts.csv`** required columns:

- `id`, `category`, `prompt`

**`results/responses.csv`** one row per (prompt × condition × model):

`id`, `model`, `condition`, `response`, `label_correctness`, `label_uncertainty`, `label_fabrication`, `label_overconfidence` (labels left blank for manual or downstream scoring).

---

## Layout

```
data/prompts.csv          # questions you want to test
results/responses.csv     # model outputs (generated)
src/run_eval.py           # CLI entry
src/evaluation.py         # orchestration + CSV write
src/models.py             # OpenAI / OpenRouter clients
src/prompts.py            # load prompts + condition definitions
```

---

## Troubleshooting

- Use **`python3`** if `python` is missing.
- Run from the **repo root** so paths like `data/prompts.csv` resolve.
- Use **`python3 src/run_eval.py`** so `src/` is on the import path.
