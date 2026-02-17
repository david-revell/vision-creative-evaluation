from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT.parent / "provided_assessment_pack"
GT_PATH = DATA_DIR / "ground_truth.csv"
OUT_PATH = ROOT / "outputs" / "predictions_template.csv"


def main() -> None:
    with GT_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if not fieldnames:
        raise RuntimeError("ground_truth.csv appears empty or malformed")

    template_fields = fieldnames
    with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=template_fields)
        writer.writeheader()
        for row in rows:
            out = {k: "" for k in template_fields}
            out["creative_id"] = row["creative_id"]
            writer.writerow(out)

    print(f"Wrote template: {OUT_PATH}")


if __name__ == "__main__":
    main()


