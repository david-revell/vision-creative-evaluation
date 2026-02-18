from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/raw"
GT_PATH = DATA_DIR / "ground_truth.csv"
LLM_JUDGE_MODEL = "gpt-5-nano"


def norm_text(value: str) -> str:
    v = (value or "").strip().lower()
    v = " ".join(v.split())
    return v


def norm_yes_no(value: str) -> str:
    v = norm_text(value)
    mapping = {
        "y": "yes",
        "yes": "yes",
        "true": "yes",
        "1": "yes",
        "n": "no",
        "no": "no",
        "false": "no",
        "0": "no",
    }
    return mapping.get(v, v)


def is_binary_column(name: str) -> bool:
    return (
        name != "creative_id"
        and not name.lower().startswith("where in the image")
        and not name.lower().startswith("what is the primary colour")
    )


def is_colour_column(name: str) -> bool:
    return name.lower().startswith("what is the primary colour")


def normalize(col: str, val: str) -> str:
    if is_binary_column(col):
        return norm_yes_no(val)
    return norm_text(val)


def read_csv_by_id(path: Path) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        data = {}
        for row in reader:
            cid = row.get("creative_id", "").strip()
            if cid:
                data[cid] = row
    return fieldnames, data


def parse_judge_verdict(text: str) -> str:
    t = (text or "").strip().upper()
    if t.startswith("YES"):
        return "YES"
    if t.startswith("NO"):
        return "NO"
    raise ValueError(f"Unexpected LLM judge verdict: {text!r}")


def judge_colour_equivalence(client: OpenAI, ground_truth: str, prediction: str) -> str:
    prompt = (
        "You are judging colour equivalence for an advertising creative evaluation.\n"
        "Respond with exactly one token: YES or NO.\n"
        "YES = semantically equivalent colour description (ignore order/minor wording differences).\n"
        "NO = not semantically equivalent.\n\n"
        f"Ground truth: {ground_truth}\n"
        f"Prediction: {prediction}\n"
    )
    resp = client.responses.create(
        model=LLM_JUDGE_MODEL,
        input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
    )
    return parse_judge_verdict(resp.output_text)


def evaluate(
    pred_path: Path,
    scope: str = "all",
    use_llm_judge_colour: bool = False,
    judge_client: OpenAI | None = None,
) -> dict:
    cols, gt = read_csv_by_id(GT_PATH)
    _, pred = read_csv_by_id(pred_path)

    question_cols = [c for c in cols if c != "creative_id"]

    if scope == "common":
        ids = sorted(set(gt.keys()).intersection(set(pred.keys())))
    else:
        ids = sorted(gt.keys())

    per_q = {c: {"correct": 0, "total": 0, "accuracy": 0.0} for c in question_cols}
    errors: List[dict] = []
    final_error_count = 0
    judge_rows: List[dict] = []

    for cid in ids:
        gt_row = gt[cid]
        pred_row = pred.get(cid, {})
        for col in question_cols:
            gt_val = normalize(col, gt_row.get(col, ""))
            pred_val = normalize(col, pred_row.get(col, ""))
            is_correct = pred_val == gt_val
            llm_judge_verdict = ""

            if use_llm_judge_colour and is_colour_column(col) and not is_correct:
                if judge_client is None:
                    raise RuntimeError("LLM judge enabled but judge client is not configured")
                llm_judge_verdict = judge_colour_equivalence(
                    judge_client, gt_row.get(col, ""), pred_row.get(col, "")
                )
                judge_rows.append(
                    {
                        "creative_id": cid,
                        "question": col,
                        "ground_truth": gt_row.get(col, ""),
                        "prediction": pred_row.get(col, ""),
                        "ground_truth_norm": gt_val,
                        "prediction_norm": pred_val,
                        "llm_judge_verdict": llm_judge_verdict,
                    }
                )
                if llm_judge_verdict == "YES":
                    is_correct = True

            per_q[col]["total"] += 1
            row_record = {
                "creative_id": cid,
                "question": col,
                "ground_truth": gt_row.get(col, ""),
                "prediction": pred_row.get(col, ""),
                "ground_truth_norm": gt_val,
                "prediction_norm": pred_val,
                "llm_judge_verdict": llm_judge_verdict,
                "final_is_error": "",
            }

            if is_correct:
                per_q[col]["correct"] += 1
            else:
                final_error_count += 1

            if llm_judge_verdict:
                row_record["final_is_error"] = "yes" if not is_correct else "no"
                errors.append(row_record)
            elif not is_correct:
                row_record["final_is_error"] = "yes"
                errors.append(row_record)

    for col, stats in per_q.items():
        total = stats["total"]
        stats["accuracy"] = round((stats["correct"] / total) if total else 0.0, 4)

    macro_accuracy = round(sum(v["accuracy"] for v in per_q.values()) / len(per_q), 4) if per_q else 0.0
    judge_yes_count = sum(1 for r in judge_rows if r["llm_judge_verdict"] == "YES")
    judge_no_count = sum(1 for r in judge_rows if r["llm_judge_verdict"] == "NO")

    return {
        "scope": scope,
        "scored_rows": len(ids),
        "rows_ground_truth": len(gt),
        "rows_predictions": len(pred),
        "questions": per_q,
        "macro_accuracy": macro_accuracy,
        "error_count": final_error_count,
        "error_rows_written": len(errors),
        "use_llm_judge_colour": use_llm_judge_colour,
        "llm_judge_model": LLM_JUDGE_MODEL if use_llm_judge_colour else None,
        "llm_judge_invocations": len(judge_rows),
        "llm_judge_yes_count": judge_yes_count,
        "llm_judge_no_count": judge_no_count,
        "errors": errors,
        "judge_rows": judge_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="Path to predictions CSV")
    parser.add_argument(
        "--scope",
        choices=["all", "common"],
        default="all",
        help="all = score all GT rows; common = only IDs present in both GT and predictions",
    )
    parser.add_argument("--run-id", default=None, help="Run identifier. Default is current timestamp.")
    parser.add_argument("--out-dir", default="outputs/runs", help="Directory under which run folders are created")
    parser.add_argument(
        "--use-llm-judge-colour",
        action="store_true",
        help="Use LLM judge (YES/NO) for colour question mismatches only",
    )
    args = parser.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.is_absolute():
        pred_path = ROOT / pred_path
    if not pred_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {pred_path}")

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = Path(args.out_dir)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    run_dir = out_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = run_dir / "metrics_summary.json"
    errors_path = run_dir / "error_rows.csv"

    judge_client = None
    if args.use_llm_judge_colour:
        load_dotenv(ROOT / ".env")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not found. Add it to .env")
        judge_client = OpenAI(api_key=api_key)

    result = evaluate(
        pred_path,
        scope=args.scope,
        use_llm_judge_colour=args.use_llm_judge_colour,
        judge_client=judge_client,
    )

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump({k: v for k, v in result.items() if k not in {"errors", "judge_rows"}}, f, indent=2)

    with errors_path.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "creative_id",
            "question",
            "ground_truth",
            "prediction",
            "ground_truth_norm",
            "prediction_norm",
            "llm_judge_verdict",
            "final_is_error",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["errors"])

    print("Run ID:", run_id)
    print("Scope:", result["scope"])
    print("Scored rows:", result["scored_rows"])
    print("Macro accuracy:", result["macro_accuracy"])
    print("Errors:", result["error_count"])
    if args.use_llm_judge_colour:
        print("LLM judge model:", result["llm_judge_model"])
        print("LLM judge invocations:", result["llm_judge_invocations"])
        print("LLM judge YES:", result["llm_judge_yes_count"])
        print("LLM judge NO:", result["llm_judge_no_count"])
    print(f"Saved: {metrics_path}")
    print(f"Saved: {errors_path}")


if __name__ == "__main__":
    main()
