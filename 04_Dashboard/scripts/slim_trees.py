"""Keep only what the browser needs from XGBoost's model.json."""
import json
import math
import sys
from pathlib import Path

SRC, DST = Path(sys.argv[1]), Path(sys.argv[2])

learner = json.loads(SRC.read_text())["learner"]
base_score = float(learner["learner_model_param"]["base_score"].strip("[]"))
trees = [
    {k: t[k] for k in ("left_children", "right_children", "split_indices",
                       "split_conditions", "default_left")}
    for t in learner["gradient_booster"]["model"]["trees"]
]
slim = {"base_margin": math.log(base_score / (1 - base_score)), "trees": trees}
DST.write_text(json.dumps(slim, separators=(",", ":")))
print(f"{DST.name} {DST.stat().st_size / 1e6:.1f} MB")
