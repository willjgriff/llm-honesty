# LLM (Large Language Model) honesty under pressure

**Do models deny true facts more often when the system prompt applies pressure by framing them as protecting a named organisation?**


This project is a small **AI safety** evaluation exploring whether language models become less truthful when the system prompt frames them as protecting a named organisation. It tests how answers change under escalating organisational pressure, using simple Yes/No questions where the ground truth is known.

The same questions are run under neutral and pressured prompts across multiple models, and the results are aggregated into denial and refusal metrics. In this setup, a **No** answer to a Yes-ground-truth question is treated as a false denial, letting the project measure how often pressure shifts responses away from the neutral baseline.

This approach was inspired by the [MASK Benchmark](https://arxiv.org/abs/2503.03750) (Ren et al., 2025), which disentangles honesty from accuracy in LLMs and finds that frontier models exhibit a substantial propensity to lie under pressure despite scoring well on truthfulness benchmarks.

---

## Results (representative run)

The same items are queried under neutral and pressured system prompts; each chart summarises how answers shift with pressure and how that differs by model. Regenerated outputs live in `results/`; images embedded here are kept in `docs/images/` (copy after analysis with `--copy-readme-images` if you refresh them).

**Key takeaway:** In this representative run, all evaluated models showed some increase in non-Yes responses under organisation-aligned pressure, though the magnitude and pattern differed by model.

**Figure 1 — False denial and other/refusal rates by pressure level (per model)**

For each model, the lines show rates of **No** answers (**false denial**: the model had answered **Yes** under neutral on the same question) and **Other** (non-committal or unparseable) answers **at each pressure level**. Reading this through a safety lens: **higher** curves suggest the model is more willing to **deny or dodge** well-known facts when the system prompt emphasises loyalty to the named organisation.

![Figure 1: false denial and other/refusal rates by pressure level, per model](docs/images/pressure_level_false_denial_rate_by_model.png)

Notably, **Claude 3.5 Haiku** almost never directly denied true facts (low false denial rate) but instead gave increasingly **evasive or non-committal responses** (high Other rate) under pressure. **GPT-4.1 mini** and **Llama 3.3 70B** showed the opposite pattern: they were more likely to explicitly say **No** — a direct denial. This suggests different models have different pressure-response styles: outright denial vs. evasion.

**Figure 2 — How often each model changes its answer under any pressure**

For each model, the bars show the percentage of questions it answered **Yes** under neutral that received at least one **No** or **Other** response under any pressured prompt. A higher bar means the model was more susceptible to changing its answer away from the neutral baseline when placed under organisational pressure. Unlike Figure 1, each question is counted at most once regardless of how many pressure levels caused a change.

![Figure 2: % of neutral-Yes questions that change under pressure, per model](docs/images/model_answer_change_when_pressured.png)

### Results files (`results/`)

| Artifact | What it supports |
|----------|------------------|
| `pressure_level_false_denial_rate_by_model.csv` / `.png` | Figure 1: false denial vs other/refusal **by pressure level and model** |
| `model_answer_change_when_pressured.csv` / `.png` | Figure 2: share of neutral-Yes items that **ever** become non-Yes under **any** pressure |
| `pressure_level_false_denial_rate.csv` / `.png` | Same denial/other split **by level**, aggregated across models |
| `pressure_level_yes_no_counts.csv` / `.png` | Raw **Yes / No / Other** counts **by pressure level** |

**Scope:** These results are **exploratory** and illustrate **methodology and metrics**, not causal claims about production systems. Ground truth is **Yes-only** for now; parsing and dataset limits are spelled out under **Limitations**.

---

## Project overview

- **Multi-model querying** — OpenAI and OpenRouter (default: GPT‑4.1 mini, Llama 3.3 70B, Claude 3.5 Haiku), parallel across models.
- **Pressure ladder** — four system-prompt levels (`neutral` → `strong`), with `{ORG_NAME}` filled from each question’s organisation.
- **CSV pipeline** — prompts and pressure definitions in `data/`; raw responses in `results/responses.csv`.
- **Analysis** — normalise answers to Yes/No/Other, aggregate by pressure level, export CSVs and matplotlib charts to `results/`. Metric definitions live under `src/result_analysis/scoring/`.

**Stack:** Python 3.9+, `openai` SDK (chat completions), `python-dotenv`, `matplotlib`.

---

## How it works

1. Load questions from `data/prompts.csv` and pressure templates from `data/pressure_levels.csv`.
2. For each `(question × pressure level × model)`, call the API with organisation-specific system text.
3. Write all rows to `results/responses.csv`.
4. The analysis pipeline normalises responses and writes summary CSVs and charts (including those in **Results**) into `results/`.

Although the task is simplified, the controlled Yes-ground-truth setup makes it easier to isolate answer changes caused by prompt pressure.

### Source layout (`src/`)

- `run.py` — CLI entrypoint.
- `prompts.py` — load questions and pressure-level templates.
- `model_interaction/` — OpenRouter/OpenAI clients, parallel querying, `responses.csv` writer.
- `result_analysis/` — scoring, summary CSV writing, chart generation, and analysis orchestration.

---

## Run it (if you want to reproduce)

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY and OPENROUTER_API_KEY; optional EVAL_MODELS
```

```bash
python3 src/run.py --mode both        # query + analyse
python3 src/run.py --mode query       # responses only → results/responses.csv
python3 src/run.py --mode analyse     # from existing results/responses.csv
```

<details>
<summary><strong>Full CLI and output reference</strong></summary>

| Flag | Purpose |
|------|--------|
| `--mode {query,analyse,both}` | Query only, analyse only, or both |
| `--prompts PATH` | Questions CSV (default: `data/prompts.csv`) |
| `--pressure-levels PATH` | Pressure definitions (default: `data/pressure_levels.csv`) |
| `--output PATH` | Raw responses CSV (default: `results/responses.csv`) |
| `--models "openai:...,openrouter:..."` | Override `EVAL_MODELS` from `.env` |
| `--limit N` | Only the first `N` questions |
| `--skip-errors` | On API failure, write `[ERROR] ...` in `response` and continue |
| `--sequential` | One model at a time (default: parallel across models) |
| `--copy-readme-images` | After analysis, copy chart PNGs from `results/` to `docs/images/` (default: off) |

Example:

```bash
python3 src/run.py --mode both --limit 5 --skip-errors
```

**Analysis outputs** (written to `results/` when you use `analyse` or `both`): `responses.csv`, `pressure_level_yes_no_counts.csv`, `pressure_level_yes_no_counts.png`, `pressure_level_false_denial_rate.csv`, `pressure_level_false_denial_rate.png`, `pressure_level_false_denial_rate_by_model.csv`, `pressure_level_false_denial_rate_by_model.png` (per-model false denial + other/refusal lines), `model_answer_change_when_pressured.csv`, `model_answer_change_when_pressured.png` (per-model % of neutral-Yes questions with at least one pressured answer that is not Yes — i.e. No or Other).

</details>

---

## Limitations

- Prompt set is **Yes-ground-truth only**; metrics assume `Yes` is the correct answer for interpretation of “denial.”
- Parsing is simple: leading `yes`/`no` (case-insensitive) → Yes/No; else `Other`.
- Not a substitute for rigorous safety evaluation — a small exploratory harness.

## Future work

These are **planned extensions**, not part of the default run today:

- Increasing dataset breadth (No-ground-truth and open-ended prompts)
- Testing models for ideological bias
- Testing jailbreak susceptibility
- Testing in-context emergent misalignment