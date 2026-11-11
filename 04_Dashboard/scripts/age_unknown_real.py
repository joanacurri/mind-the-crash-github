"""Hide the age of real validation incidents and compare two ways of filling "non so".

old: age = 35 (training median, also the imputation value)
new: p averaged over the age bands, weighted by their share (what the simulator now does)
Reference: the model with the true age. Only incidents whose age is not 35 are used, so the
true age is known for all of them.
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

DATA = Path(sys.argv[1]) / "00_Data"
ages = json.loads(Path(sys.argv[2]).read_text())
bundle = joblib.load(DATA / "Models/best_model_bundle.joblib")
model, thr, feats = bundle["model"], bundle["threshold"], bundle["features"]

X = pd.read_csv(DATA / "Input/X_test.csv", dtype={"collision_index": str}).set_index("collision_index")
y = pd.read_csv(DATA / "Input/y_test.csv", dtype={"collision_index": str}).set_index("collision_index")
y = y.loc[X.index].iloc[:, 0].to_numpy()
X = X[feats].astype("float32")
known = (X["age_of_casualty_mean"] != 35).to_numpy()
X, y = X[known], y[known]


def proba(age=None):
    Xa = X.copy()
    if age is not None:
        Xa["age_of_casualty_mean"] = age
    return model.predict_proba(Xa)[:, 1]


variants = {
    "età vera (riferimento)": proba(),
    "non so = 35 (vecchio)": proba(35.0),
    "non so = media sulle fasce (nuovo)": sum(b["share"] * proba(b["age"]) for b in ages.values()),
}
print(f"incidenti con età nota: {len(y)} | gravi davvero {y.mean():.1%}")
for name, p in variants.items():
    print(f"{name:36s} p media {p.mean():.3f} | ASE {np.mean((y - p) ** 2):.4f} | "
          f"AUC {roc_auc_score(y, p):.4f} | segnalati gravi {(p >= thr).mean():.1%} | "
          f"recall {(p[y == 1] >= thr).mean():.1%}")
