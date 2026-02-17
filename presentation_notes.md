# Presentation Notes (Deliverable 2)

Use this file as your running evidence log while building Deliverable 1.
For each section, keep concise bullets under `Decision`, `Evidence`, and `Implication`.

## 1) Your choice of model and rationale

- Decision: Start with OpenAI `gpt-5-nano` as primary model; keep Gemini as optional second model if time allows.
- Evidence: Existing personal projects already use `gpt-5-nano`; minimal setup friction; low cost profile for iterative runs.
- Implication: Faster iteration cycle and lower risk of implementation delay; enables more focus on prompt/evaluation quality.

## 2) Your approach to transforming basic questions into effective prompts (structured questions file + prompt design)

- Decision:
- Evidence:
- Implication:

## 3) Key design decisions in your evaluation framework

- Decision: Use `.env` + `python-dotenv` for local secrets, with `.env` excluded from version control via `.gitignore`.
- Evidence: Added `.env.example`, `.gitignore`, and README instructions for API-key setup and non-commit policy.
- Implication: Improves reproducibility for reviewers and keeps submission secure/professional by design.

## 4) Results and insights from your evaluation

- Decision: Run an initial smoke evaluation on 3 creatives using `gpt-5-nano` before scaling to full-dataset runs.
- Evidence: `python src\run_inference_smoke.py --model gpt-5-nano --limit 3` followed by `python src\\evaluate.py --predictions outputs\\runs\\smoke_run1\\predictions_smoke_3.csv --scope common --run-id smoke_run1` produced macro accuracy `0.7333` with `8` errors (run1). After output-structure refactor and rerun (`smoke_run2`), macro accuracy improved to `0.8` with `6` errors.
- Implication: End-to-end pipeline is validated (inference -> persisted predictions -> scoring -> error report), enabling controlled prompt iteration before full 30-image cost.

## 5) Analysis of where the model performed well vs. poorly (with interesting error examples)

- Decision: Use per-question accuracy + row-level error inspection (`outputs/runs/<run_id>/error_rows.csv`) to identify failure modes.
- Evidence: Strong on `person`, `out of focus`, `overlay text`, `promotion` (all `1.0` on smoke set); weaker on `product`, `CTA`, `logo present`, `logo location`, `urgency`; `primary colour scheme` remains the hardest category. In `smoke_run2`, total errors dropped from `8` to `6`.
- Implication: Next prompt iteration should prioritize disambiguation for product-vs-scene, CTA detection, and stricter colour-format guidance/normalization rather than broad prompt changes.

## 6) Any concerns or observations about the ground truth data

- Decision:
- Evidence:
- Implication:

## 7) Any optional extensions you implemented and why

- Decision:
- Evidence:
- Implication:

## 8) Challenges you encountered and how you addressed them

- Decision:
- Evidence:
- Implication:

## 9) Ideas for how this framework could be extended or improved for production use

- Decision:
- Evidence:
- Implication:

## Slide Mapping (max 10 slides)

- Slide 1: Context, objective, and success criteria
- Slide 2: Model choice and rationale
- Slide 3: Structured question design and prompt strategy
- Slide 4: Framework architecture and key implementation decisions
- Slide 5: Metric definitions and evaluation methodology
- Slide 6: Overall results
- Slide 7: Error analysis: where it worked vs failed
- Slide 8: Ground-truth observations and data quality caveats
- Slide 9: Challenges, mitigations, and optional extensions
- Slide 10: Production improvements and next steps






