# Vision Creative Eval

## Data Inputs (local-only)

Expected local path:

- `data/raw/questions_basic.txt`
- `data/raw/ground_truth.csv`
- `data/raw/data/`

These provided files are intentionally git-ignored.

## Environment Variables

Create `.env` from template and add key:

```powershell
Copy-Item .env.example .env
```

```env
OPENAI_API_KEY=your_key_here
```

## Setup

```powershell
pip install -r requirements.txt
```

## Artefacts vs Runs

- `artefacts/`: static scaffolds (e.g., predictions template)
- `outputs/runs/<run_id>/`: run-specific predictions + metrics + error rows

## 1) Create predictions template (non-run scaffold)

```powershell
python src\make_predictions_template.py
```

Writes:

- `artefacts/predictions_template.csv`

## 2) Smoke inference on 3 images

You can use any run ID (for example, smoke_run2).

```powershell
python src\run_inference_smoke.py --model gpt-5-nano --limit 3 --run-id smoke_run2
```

Writes:

- `outputs/runs/smoke_run2/predictions_smoke_3.csv`

Notes:

- The CSV includes both answer columns and `<question>_explanation` columns.
- Evaluator scoring uses the answer columns only (explanations are stored for audit/review).

## 3) Evaluate smoke run

```powershell
python src\evaluate.py --predictions outputs\runs\smoke_run2\predictions_smoke_3.csv --scope common --run-id smoke_run2
```

Tip:

- Use the same `--run-id` for inference and evaluation to keep one folder per run.

Writes:

- `outputs/runs/smoke_run2/metrics_summary.json`
- `outputs/runs/smoke_run2/error_rows.csv`

Optional (colour-only LLM judge):

```powershell
python src\evaluate.py --predictions outputs\runs\smoke_run2\predictions_smoke_3.csv --scope common --run-id smoke_run2 --use-llm-judge-colour
```

When `--use-llm-judge-colour` is enabled:

- Judge scope is only `What is the primary colour scheme?` mismatches.
- Judge model is fixed to `gpt-5-nano` with default model settings.
- `error_rows.csv` includes `llm_judge_verdict` (`YES`/`NO` when invoked) and `final_is_error`.
- Judged colour rows are always written to `error_rows.csv` for traceability, even when the final verdict is not an error (`final_is_error=no`).
- Because of that audit behaviour, `error_rows_written` can be higher than `error_count` in `metrics_summary.json`.
- This is an offline benchmarking pattern that depends on labelled ground truth.



