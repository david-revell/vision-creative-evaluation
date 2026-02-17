# Vision Creative Eval

## Data Inputs (local-only)

Expected local path:

- `provided_assessment_pack/questions_basic.txt`
- `provided_assessment_pack/ground_truth.csv`
- `provided_assessment_pack/data/`

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

## 3) Evaluate smoke run

```powershell
python src\evaluate.py --predictions outputs\runs\smoke_run2\predictions_smoke_3.csv --scope common --run-id smoke_run2
```

Writes:

- `outputs/runs/smoke_run2/metrics_summary.json`
- `outputs/runs/smoke_run2/error_rows.csv`


