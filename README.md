# Satalia AI Engineer Assessment - Minimal Scaffold

This repo uses a KISS setup so you can work in small steps.

## Location

Project root:
`C:\Users\david\Dropbox\private_workspace\satalia\ai-eng-prompt-engineering-eval`

Deliverable repo root:
`C:\Users\david\Dropbox\private_workspace\satalia\ai-eng-prompt-engineering-eval\repo`

## Data Inputs

Data lives one level above `repo/` in:

- `provided_assessment_pack/questions_basic.txt`
- `provided_assessment_pack/ground_truth.csv`
- `provided_assessment_pack/data/`

## Environment Variables

This project uses `.env` for local secrets.

1. Create `.env` from the template:

```powershell
Copy-Item .env.example .env
```

2. Add your API key in `repo/.env`:

```env
OPENAI_API_KEY=your_key_here
```

Security notes:

- `.env` is ignored by git via `repo/.gitignore`.
- Never commit real API keys.
- `.env.example` is safe to commit and documents required variables.

## Install

```powershell
pip install -r requirements.txt
```

## Step 1: Create a predictions template

Run from the `repo/` directory:

```powershell
python src\make_predictions_template.py
```

Output:

- `outputs/predictions_template.csv`

## Step 2: Smoke inference on 3 images (`gpt-5-nano`)

```powershell
python src\run_inference_smoke.py --model gpt-5-nano --limit 3 --out outputs\predictions_smoke_3.csv
```

Output:

- `outputs/predictions_smoke_3.csv`

## Step 3: Evaluate smoke run (only scored IDs)

Use `--scope common` so only the 3 predicted IDs are scored.

```powershell
python src\evaluate.py --predictions outputs\predictions_smoke_3.csv --scope common
```

Outputs:

- Console metrics summary
- `outputs/metrics_summary.json`
- `outputs/error_rows.csv`

## Notes

- The evaluator is intentionally strict and simple.
- It currently uses exact-match after normalization (trim/lower/canonical yes/no).
- We can add fuzzy normalization later (especially for color scheme).
