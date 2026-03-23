<h1>LLM Honesty Under Prompt Pressure</h1>

<h2>Overview</h2>

This project evaluates how large language models (LLMs) behave under different forms of prompt pressure.

In particular, it tests whether instructions that encourage confidence, persuasion, or goal completion cause models to produce more incorrect, overconfident, or fabricated responses.

<hr />

<h2>Motivation</h2>

As LLMs become more capable, their behaviour under pressure becomes increasingly important.

Instructions that discourage uncertainty or prioritise usefulness may lead models to produce confident but incorrect responses. Understanding these behaviours is relevant to AI safety, reliability, and trustworthiness.

<strong>This project aims to:</strong>
<ul>
  <li>Explore how prompt instructions affect model honesty</li>
  <li>Build a simple evaluation pipeline</li>
  <li>Create reproducible results</li>
  <li>Demonstrate hands-on engagement with AI safety concepts</li>
</ul>

<hr />

<h2>Research Question</h2>

Do large language models become less truthful or more overconfident when prompted to prioritise confidence, persuasion, or usefulness?

<hr />

<h2>Hypothesis</h2>

Prompts that discourage uncertainty or encourage persuasion will increase:
<ul>
  <li>Incorrect responses</li>
  <li>Overconfident language</li>
  <li>Fabricated information</li>
</ul>

compared to neutral baseline prompts.

<hr />

<h2>Method (Version 1)</h2>

<h3>Pressure levels</h3>

System instructions are loaded from <code>data/pressure_levels.csv</code> (columns <code>pressure_level_id</code>, <code>name</code>, <code>prompt</code>). Levels 1–3 may include the placeholder <code>{ORG_NAME}</code>, which the runner replaces with the <code>organisation</code> field from that prompt row before calling the API. Level 0 (neutral) has no placeholder. Each level instructs the model to answer using only <code>Yes</code> or <code>No</code>.

Each row in <code>data/prompts.csv</code> (<code>question_id</code>, <code>organisation</code>, <code>question</code>, <code>ground_truth</code>) is asked once per pressure level per model. The model’s single reply is recorded alongside <code>ground_truth</code> for later comparison.

<hr />

<h2>Prompt Dataset</h2>

Prompts are in <code>data/prompts.csv</code> with columns <code>question_id</code>, <code>organisation</code>, <code>question</code>, and <code>ground_truth</code> (expected <code>Yes</code>/<code>No</code>). Rows reference real or fictitious claims about named organisations.

<hr />

<h2>Evaluation Metrics</h2>

Responses will be evaluated using labels such as:
<ul>
  <li>Correct vs Incorrect</li>
  <li>Appropriate vs Inappropriate uncertainty</li>
  <li>Fabricated vs Non-fabricated</li>
  <li>Overconfident vs Not overconfident</li>
</ul>

Initial scoring will be performed manually.

<hr />

<h2>Project Structure</h2>

<pre><code>llm-honesty-evals/
├── README.md
├── requirements.txt
├── data/
│   ├── prompts.csv
│   └── pressure_levels.csv
├── results/
│   └── responses.csv
├── src/
│   ├── run_eval.py
│   ├── evaluation.py
│   ├── models.py
│   ├── prompts.py
│   ├── scorer.py
│   └── analysis.py
└── notebooks/
    └── exploration.ipynb
</code></pre>

<h2>Expected Outputs</h2>

<strong>This project will produce:</strong>
<ul>
  <li>A reusable evaluation pipeline</li>
  <li>Structured response datasets</li>
  <li>Summary statistics</li>
  <li>Visualisations of behavioural differences</li>
  <li>A written analysis of findings</li>
</ul>

<hr />

<h2>Limitations</h2>

This is a small-scale exploratory project.

<strong>Limitations include:</strong>
<ul>
  <li>Limited dataset size</li>
  <li>Manual scoring subjectivity</li>
  <li>Prompt sensitivity</li>
  <li>Dependence on external APIs</li>
</ul>

These constraints are intentional to keep the project manageable and reproducible.

<hr />

<h2>Future Work</h2>

<strong>Possible extensions include:</strong>
<ul>
  <li>Expanding the prompt dataset</li>
  <li>Adding additional models</li>
  <li>Automating response scoring</li>
  <li>Testing adversarial prompt strategies</li>
  <li>Comparing behaviour across model versions</li>
</ul>

<hr />

<h2>Status</h2>

Planned — initial design phase.
<h3>Next steps</h3>
<ul>
  <li>Define prompt categories</li>
  <li>Build prompt dataset</li>
  <li>Implement evaluation runner</li>
  <li>Run initial experiments</li>
</ul>