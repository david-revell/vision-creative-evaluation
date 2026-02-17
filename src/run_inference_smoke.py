from __future__ import annotations

import argparse
import base64
import csv
import json
import mimetypes
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT.parent / "provided_assessment_pack"
IMAGES_DIR = DATA_DIR / "data"
GT_PATH = DATA_DIR / "ground_truth.csv"
QUESTIONS_PATH = ROOT / "questions_structured.json"


def read_ground_truth() -> tuple[list[str], list[dict[str, str]]]:
    with GT_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        rows = list(reader)
    if not cols or "creative_id" not in cols:
        raise RuntimeError("ground_truth.csv malformed")
    return cols, rows


def read_questions_structured() -> dict:
    with QUESTIONS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_instruction(question_spec: dict, question_cols: list[str]) -> str:
    lines: list[str] = []
    lines.append("You are evaluating one advertising creative image.")
    lines.append("Return JSON only. No markdown, no extra text.")
    lines.append("Output a single JSON object with exactly these keys:")
    for c in question_cols:
        lines.append(f"- {c}")
    lines.append("Use lowercase answers where possible.")
    lines.append("For yes/no questions, answer strictly: yes or no.")
    lines.append("For logo location, use one of: no logo, top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right.")
    lines.append("For primary colour scheme, provide concise dominant colours as comma-separated lowercase names.")
    lines.append("Question guidance:")

    by_q = {q["question"]: q for q in question_spec.get("questions", [])}
    for c in question_cols:
        q = by_q.get(c)
        if q:
            instr = q.get("instruction", "")
            lines.append(f"- {c}: {instr}")
        else:
            lines.append(f"- {c}: answer directly from the image")

    return "\n".join(lines)


def find_image_path(creative_id: str) -> Path:
    matches = sorted(IMAGES_DIR.glob(f"{creative_id}.*"))
    if not matches:
        raise FileNotFoundError(f"No image found for {creative_id} in {IMAGES_DIR}")
    return matches[0]


def image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def parse_json_object(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].strip()
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Model did not return JSON object: {text[:300]}")
    return json.loads(t[start : end + 1])


def infer_one(client: OpenAI, model: str, creative_id: str, question_cols: list[str], instruction: str) -> dict:
    image_path = find_image_path(creative_id)
    image_url = image_to_data_url(image_path)

    resp = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": instruction},
                    {"type": "input_image", "image_url": image_url},
                ],
            }
        ],
    )

    data = parse_json_object(resp.output_text)
    out = {"creative_id": creative_id}
    for q in question_cols:
        out[q] = str(data.get(q, "")).strip()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5-nano")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--out", default="outputs/predictions_smoke_3.csv")
    parser.add_argument("--ids", nargs="*", default=None, help="Optional explicit creative_ids")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not found. Add it to repo/.env")

    cols, gt_rows = read_ground_truth()
    question_cols = [c for c in cols if c != "creative_id"]
    question_spec = read_questions_structured()
    instruction = build_instruction(question_spec, question_cols)

    if args.ids:
        selected_ids = args.ids
    else:
        selected_ids = [r["creative_id"] for r in gt_rows[: max(1, args.limit)]]

    client = OpenAI(api_key=api_key)

    predictions: Dict[str, dict] = {}
    for cid in selected_ids:
        print(f"Inferring: {cid}")
        predictions[cid] = infer_one(client, args.model, cid, question_cols, instruction)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for cid in selected_ids:
            writer.writerow(predictions[cid])

    print(f"Saved predictions: {out_path}")
    print(f"Rows written: {len(selected_ids)}")


if __name__ == "__main__":
    main()
