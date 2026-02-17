import argparse
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data/raw"
GT_PATH = DATA_DIR / "ground_truth.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artefacts/predictions_template.csv")
    args = parser.parse_args()

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path

    with GT_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if not fieldnames:
        raise RuntimeError("ground_truth.csv appears empty or malformed")

    template_fields = fieldnames
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=template_fields)
        writer.writeheader()
        for row in rows:
            out = {k: "" for k in template_fields}
            out["creative_id"] = row["creative_id"]
            writer.writerow(out)

    print(f"Wrote template: {out_path}")


if __name__ == "__main__":
    main()

