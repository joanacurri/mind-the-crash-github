"""Real validation incidents with an injured pedestrian: actual KSI rate and model scores."""
import sys
from pathlib import Path

import joblib
import pandas as pd

DATA = Path(sys.argv[1]) / "00_Data"
bundle = joblib.load(DATA / "Models/best_model_bundle.joblib")
X = pd.read_csv(DATA / "Input/X_test.csv", dtype={"collision_index": str}).set_index("collision_index")
y = pd.read_csv(DATA / "Input/y_test.csv", dtype={"collision_index": str}).set_index("collision_index")
y = y.loc[X.index].iloc[:, 0]
p = pd.Series(bundle["model"].predict_proba(X[bundle["features"]].astype("float32"))[:, 1], X.index)
thr = bundle["threshold"]

groups = {
    "tutti gli incidenti": X.index == X.index,
    "almeno un pedone ferito": X["casualty_class_Pedestrian"] > 0,
    "nessun pedone": X["casualty_class_Pedestrian"] == 0,
}
for name, mask in groups.items():
    print(f"{name:26s} n={mask.sum():7d} | gravi davvero {y[mask].mean():.1%} | "
          f"p media {p[mask].mean():.3f} | segnalati gravi {(p[mask] >= thr).mean():.1%}")
