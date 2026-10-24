from pathlib import Path
import argparse, hashlib, json

parser = argparse.ArgumentParser(description="Freeze a forecast CSV with a SHA-256 manifest; never overwrites.")
parser.add_argument("prediction_csv", type=Path)
parser.add_argument("--timestamp", required=True, help="UTC ISO timestamp supplied by the analyst")
parser.add_argument("--target", type=Path, required=True)
args = parser.parse_args()
if not args.prediction_csv.is_file(): raise SystemExit("Prediction CSV not found")
if args.target.exists() or args.target.with_suffix(args.target.suffix + ".json").exists():
    raise SystemExit("Freeze target already exists; choose a new versioned path")
args.target.parent.mkdir(parents=True, exist_ok=True)
args.target.write_bytes(args.prediction_csv.read_bytes())
digest = hashlib.sha256(args.target.read_bytes()).hexdigest()
manifest = {"frozen_at_utc": args.timestamp, "prediction_file": args.target.name, "sha256": digest,
            "note": "Analyst must record target definition, data cutoff, model and source provenance alongside this manifest."}
args.target.with_suffix(args.target.suffix + ".json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Frozen {args.target} (sha256 {digest})")
