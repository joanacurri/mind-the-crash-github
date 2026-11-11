"""Real KSI rate and model flag rate for the same call types, on validation incidents."""
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

two_wheel = (X["vehicle_type_Motorcycle over 125cc"] + X["vehicle_type_Motorcycle up to 125cc"]
             + X["vehicle_type_Pedal cycle"])
cases = {
    "2 veicoli, 1 ferito in auto": (X.number_of_vehicles == 2) & (X.number_of_casualties == 1)
    & (X.casualty_type_Car == 1) & (two_wheel == 0),
    "2 veicoli, 2 feriti in auto": (X.number_of_vehicles == 2) & (X.number_of_casualties == 2)
    & (X.casualty_type_Car == 2) & (two_wheel == 0),
    "1 veicolo, 1 pedone": (X.number_of_vehicles == 1) & (X.casualty_class_Pedestrian == 1)
    & (X.number_of_casualties == 1),
    "2 veicoli con bici, 1 ferito": (X.number_of_vehicles == 2) & (X["vehicle_type_Pedal cycle"] == 1)
    & (X.number_of_casualties == 1) & (X.casualty_type_Car == 0),
    "2 veicoli con moto>125, 1 ferito": (X.number_of_vehicles == 2)
    & (X["vehicle_type_Motorcycle over 125cc"] == 1) & (X.number_of_casualties == 1)
    & (X.casualty_type_Car == 0),
}
for name, m in cases.items():
    print(f"{name:34s} n={m.sum():6d} | gravi davvero {y[m].mean():.1%} | "
          f"modello: grave nel {(p[m] >= bundle['threshold']).mean():.1%}")
