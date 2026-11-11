"""Print what the colleagues' model bundle contains."""
import sys
from pathlib import Path

import joblib

BUNDLE = Path(sys.argv[1])

bundle = joblib.load(BUNDLE)
print("keys:", list(bundle))
for k in ("model_name", "threshold", "metrics_val"):
    print(k, "=", bundle[k])
print("n features:", len(bundle["features"]))
print("model:", bundle["model"])
for name, val in bundle["defaults"].items():
    print(f"  default {name} = {val}")
