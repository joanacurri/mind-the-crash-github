"""Check the bundle still reproduces the colleagues' scores, then export it for the browser.

Writes model.json (XGBoost trees) and meta.json (features, threshold, defaults, metrics)
to the output folder, plus a CSV of validation rows for the JS parity test.
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT = Path(sys.argv[1])  # "Mind the crash" folder
OUT = Path(sys.argv[2])  # dashboard/data
PARITY_CSV = Path(sys.argv[3])  # validation rows + Python probabilities

bundle = joblib.load(PROJECT / "00_Data/Models/best_model_bundle.joblib")
features = bundle["features"]
xgb = bundle["model"].named_steps["model"]

X = pd.read_csv(PROJECT / "00_Data/Input/X_test.csv", dtype={"collision_index": str})
X = X.set_index("collision_index")[features].astype("float32")
p = xgb.predict_proba(X)[:, 1]

saved = pd.read_csv(PROJECT / "00_Data/Output/score_validation.csv",
                    dtype={"collision_index": str}).set_index("collision_index")
diff = np.abs(saved.loc[X.index, "p_grave"].to_numpy() - p)
print(f"rows {len(X)} | max |p - saved| = {diff.max():.2e}")

xgb.get_booster().save_model(OUT / "model.json")
meta = {k: bundle[k] for k in ("model_name", "threshold", "features", "defaults", "metrics_val")}
(OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
print(f"model.json {(OUT / 'model.json').stat().st_size / 1e6:.1f} MB")

X.assign(p_python=p).to_csv(PARITY_CSV, index=False)
