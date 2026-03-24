# LLM honesty querying (pressure levels)

This project evaluates how model answers change when the **same question** is asked under different **pressure-level system prompts**.

The current default model set is:
- `openai:gpt-4.1-mini`
- `openrouter:meta-llama/llama-3.3-70b-instruct`
- `openrouter:anthropic/claude-3.5-haiku`

For each question and each model, the runner tests four pressure levels (`neutral`, `mild`, `moderate`, `strong`) and records raw responses for scoring and comparison. The project is designed to support downstream analysis and visualisation (for example, graphs comparing error rates or confidence markers by pressure level/model), which can be useful for deeper follow-up investigation.

At this stage, it is a **minimal proof of concept**. The current prompt set is mostly Yes-ground-truth items; planned expansion includes explicit No-ground-truth sets and eventually broader open-ended question sets.

## What this currently does

1. Loads questions from `data/prompts.csv`.
2. Loads pressure levels from `data/pressure_levels.csv`.
3. Substitutes `{ORG_NAME}` in pressure prompts with the row's `organisation`.
4. Calls each configured model for every `(question x pressure_level)` pair.
5. Writes raw outputs to `results/responses.csv`.
6. Analyses response patterns by pressure level and writes summary CSVs/graphs to `results/`.

The goal is to analyze honesty-related behavior under pressure (e.g. incorrect answers, overconfidence, fabrication).

## Future work

Potential extensions include:
- Increasing dataset breadth (more No-ground-truth and open-ended prompts)
- Testing models for ideological bias
- Testing jailbreak susceptibility
- Testing in-context emergent misalignment

---

## Setup

Requirements:
- Python 3.9+
- `OPENAI_API_KEY` for `openai:...` models
- `OPENROUTER_API_KEY` for `openrouter:...` models

Install and configure:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Then edit `.env`:
- Set your API keys
- Optionally set `EVAL_MODELS` (comma-separated `provider:model`)

Default models:
- `openai:gpt-4.1-mini`
- `openrouter:meta-llama/llama-3.3-70b-instruct`
- `openrouter:anthropic/claude-3.5-haiku`

---

## Run

From the repo root:

```bash
python3 src/run.py --mode query
```

This overwrites `results/responses.csv` by default.

Run analysis only (uses `results/responses.csv`):

```bash
python3 src/run.py --mode analyse
```

Run querying + analysis in one command:

```bash
python3 src/run.py --mode both
```

---

## CLI options

| Flag | Purpose |
|------|--------|
| `--mode {query,analyse,both}` | Run querying only, analysis only, or both |
| `--prompts PATH` | Prompts CSV path (default: `data/prompts.csv`) |
| `--pressure-levels PATH` | Pressure levels CSV path (default: `data/pressure_levels.csv`) |
| `--output PATH` | Output CSV path (default: `results/responses.csv`) |
| `--models "openai:...,openrouter:..."` | Override `EVAL_MODELS` from `.env` |
| `--limit N` | Evaluate only first `N` prompts |
| `--skip-errors` | Continue run on API errors and write `[ERROR] ...` in `response` |
| `--sequential` | Run models sequentially (default runs models in parallel) |

Example:

```bash
python3 src/run.py --mode both --limit 5 --skip-errors
```

---

## CSV schemas

### `data/prompts.csv`
Required columns:
- `question_id`
- `organisation`
- `question`
- `ground_truth`

### `data/pressure_levels.csv`
Required columns:
- `pressure_level_id`
- `name`
- `prompt`

`prompt` may include `{ORG_NAME}`; this is replaced with the prompt row's `organisation` at runtime.

### `results/responses.csv`
Columns:
- `question_id`
- `organisation`
- `model`
- `pressure_level_id`
- `pressure_name`
- `question`
- `ground_truth`
- `response`

### Analysis outputs in `results/`

After `--mode analyse` or `--mode both`, the pipeline writes:

- `pressure_level_false_denial_rate.csv`: rate summary by pressure level, including:
  - `false_denial_rate_percent`
  - `other_rate_percent`
  - both calculated over cases where the neutral response was `Yes`
- `pressure_level_false_denial_rate.png`: line chart with:
  - **False denial rate** = percentage of true facts denied under pressure
  - **Other/refusal rate** = percentage of non-`Yes`/`No` responses under pressure
- `pressure_level_yes_no_counts.csv`: Yes/No/Other counts per pressure level
- `pressure_level_yes_no_counts.png`: grouped bar chart of those counts
