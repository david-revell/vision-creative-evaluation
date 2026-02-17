from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/raw"
GT_PATH = DATA_DIR / "ground_truth.csv"


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
    return name != "creative_id" and not name.lower().startswith("where in the image") and not name.lower().startswith("what is the primary colour")


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


def evaluate(pred_path: Path, scope: str = "all") -> dict:
    cols, gt = read_csv_by_id(GT_PATH)
    _, pred = read_csv_by_id(pred_path)

    question_cols = [c for c in cols if c != "creative_id"]

    if scope == "common":
        ids = sorted(set(gt.keys()).intersection(set(pred.keys())))
    else:
        ids = sorted(gt.keys())

    per_q = {c: {"correct": 0, "total": 0, "accuracy": 0.0} for c in question_cols}
    errors: List[dict] = []

    for cid in ids:
        gt_row = gt[cid]
        pred_row = pred.get(cid, {})
        for col in question_cols:
            gt_val = normalize(col, gt_row.get(col, ""))
            pred_val = normalize(col, pred_row.get(col, ""))
            is_correct = pred_val == gt_val

            per_q[col]["total"] += 1
            if is_correct:
                per_q[col]["correct"] += 1
            else:
                errors.append(
                    {
                        "creative_id": cid,
                        "question": col,
                        "ground_truth": gt_row.get(col, ""),
                        "prediction": pred_row.get(col, ""),
                        "ground_truth_norm": gt_val,
                        "prediction_norm": pred_val,
                    }
                )

    for col, stats in per_q.items():
        total = stats["total"]
        stats["accuracy"] = round((stats["correct"] / total) if total else 0.0, 4)

    macro_accuracy = round(sum(v["accuracy"] for v in per_q.values()) / len(per_q), 4) if per_q else 0.0

    return {
        "scope": scope,
        "scored_rows": len(ids),
        "rows_ground_truth": len(gt),
        "rows_predictions": len(pred),
        "questions": per_q,
        "macro_accuracy": macro_accuracy,
        "error_count": len(errors),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="Path to predictions CSV")
    parser.add_argument("--scope", choices=["all", "common"], default="all", help="all = score all GT rows; common = only IDs present in both GT and predictions")
    parser.add_argument("--run-id", default=None, help="Run identifier. Default is current timestamp.")
    parser.add_argument("--out-dir", default="outputs/runs", help="Directory under which run folders are created")
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

    result = evaluate(pred_path, scope=args.scope)

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump({k: v for k, v in result.items() if k != "errors"}, f, indent=2)

    with errors_path.open("w", encoding="utf-8", newline="") as f:
        fields = ["creative_id", "question", "ground_truth", "prediction", "ground_truth_norm", "prediction_norm"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["errors"])

    print("Run ID:", run_id)
    print("Scope:", result["scope"])
    print("Scored rows:", result["scored_rows"])
    print("Macro accuracy:", result["macro_accuracy"])
    print("Errors:", result["error_count"])
    print(f"Saved: {metrics_path}")
    print(f"Saved: {errors_path}")


if __name__ == "__main__":
    main()

