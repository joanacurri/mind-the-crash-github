"""Build scores.json for the threshold section: validation scores binned at 0.001, by outcome.

With bins at 0.001 any three-decimal threshold splits the bins exactly, so the page recomputes
the confusion matrix without the 154k rows.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
DATA = PROJECT / "00_Data"
N_BINS = 1000


def main():
    meta = json.loads((OUT / "meta.json").read_text())
    scores = pd.read_csv(DATA / "Output/score_validation.csv", dtype={"collision_index": str})
    y = pd.read_csv(DATA / "Input/y_test.csv", dtype={"collision_index": str})
    df = scores.merge(y, on="collision_index", validate="1:1")
    assert len(df) == len(scores) == len(y), "scores and labels must match row for row"

    bins = np.minimum((df["p_grave"].to_numpy() * N_BINS).astype(int), N_BINS - 1)
    ksi = df["collision_severity_bin"].to_numpy() == 1
    out = {
        "bins": N_BINS,
        "serious": np.bincount(bins[ksi], minlength=N_BINS).tolist(),
        "slight": np.bincount(bins[~ksi], minlength=N_BINS).tolist(),
    }
    (OUT / "scores.json").write_text(json.dumps(out, separators=(",", ":")))

    # The binned recall at the model threshold must match the one on the slides.
    t = meta["threshold"]
    caught = (df["p_grave"] >= t) & ksi
    binned = sum(out["serious"][round(t * N_BINS):])
    print(f"rows {len(df)}, serious {ksi.sum()}, recall {caught.sum() / ksi.sum():.4f}, "
          f"binned matches: {binned == caught.sum()}")


main()
