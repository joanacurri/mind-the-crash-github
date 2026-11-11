"""Build the small data files the simulator page reads.

locations.json  real validation incidents: where the phone ping would place the call
ages.json       median casualty age and share of casualties in each age band offered to the
                operator; "non so" must not fall on 35, the value used to impute missing ages
Also prints how much each question group moves the model (grouped permutation, AUC drop).
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))  # -I leaves the script folder off the path
from police import collision_areas  # noqa: E402

PROJECT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
DATA = PROJECT / "00_Data"
SEED = 42
N_LOCATIONS = 2000
N_PERM = 30_000
AGE_BANDS = {"bambino": (0, 15), "adulto": (16, 64), "anziano": (65, 120)}

GROUPS = {
    "veicoli": ["number_of_vehicles", "vehicle_type_Motorcycle over 125cc",
                "vehicle_type_Motorcycle up to 125cc", "vehicle_type_Pedal cycle"],
    "feriti": ["number_of_casualties", "casualty_type_Car", "casualty_type_Van",
               "casualty_class_Driver or rider", "casualty_class_Passenger",
               "casualty_class_Pedestrian", "pedestrian_movement_Crossing"],
    "eta": ["age_of_casualty_mean"],
    "urto": ["first_point_of_impact_Front", "first_point_of_impact_Back",
             "first_point_of_impact_Side"],
    "limite": ["speed_limit"],
    "luce": ["light_conditions_Darkness - lights lit",
             "light_conditions_Darkness - no or unlit lighting"],
    "strada": ["road_type_Single carriageway", "road_class_name_Main road",
               "road_class_name_Local road"],
    "incrocio": ["junction_location_Not at junction", "junction_control_Give way or uncontrolled"],
    "uscita": ["vehicle_leaving_carriageway_Nearside", "vehicle_leaving_carriageway_Offside",
               "hit_object_off_carriageway_Tree"],
    "ribaltamento": ["skidding_and_overturning_None", "skidding_and_overturning_Overturned"],
    "manovra": ["vehicle_manoeuvre_Going ahead", "vehicle_manoeuvre_Waiting or slowing",
                "vehicle_manoeuvre_Turning"],
    "sesso conducente": ["sex_of_driver_Male", "sex_of_driver_Female"],
    "corsia": ["vehicle_location_restricted_lane_Main carriageway"],
    "posizione (auto)": ["latitude", "longitude", "urban_or_rural_area_Urban",
                         "collision_injury_based"],
    "quando (auto)": ["woy", "time_period_afternoon"],
}


def build_locations(X):
    area = collision_areas(PROJECT)
    sample = X.sample(N_LOCATIONS, random_state=SEED)
    return [
        {"lat": round(float(r.latitude), 5), "lon": round(float(r.longitude), 5),
         "urban": int(r.urban_or_rural_area_Urban), "ibrs": int(r.collision_injury_based),
         "speed_limit": int(r.speed_limit), "area": area.get(idx, "")}
        for idx, r in sample.iterrows()
    ]


def band_ages():
    age = pd.read_csv(DATA / "5_years/dft-road-casualty-statistics-casualty-last-5-years.csv",
                      usecols=["age_of_casualty"])["age_of_casualty"]
    age = age[age >= 0]
    # share weights the "non so" answer: the simulator averages p over the bands
    return {band: {"age": float(age[age.between(lo, hi)].median()),
                   "share": float(age.between(lo, hi).mean())}
            for band, (lo, hi) in AGE_BANDS.items()}


def group_importance(model, X, y):
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(X), N_PERM, replace=False)
    Xs, ys = X.iloc[idx].astype("float32"), y[idx]
    base = roc_auc_score(ys, model.predict_proba(Xs)[:, 1])
    drops = {}
    for name, cols in GROUPS.items():
        Xp = Xs.copy()
        Xp[cols] = Xs[cols].to_numpy()[rng.permutation(len(Xs))]
        drops[name] = base - roc_auc_score(ys, model.predict_proba(Xp)[:, 1])
    return base, drops


def main():
    bundle = joblib.load(DATA / "Models/best_model_bundle.joblib")
    features = bundle["features"]
    assert sorted(sum(GROUPS.values(), [])) == sorted(features), "groups must cover the 40 features"

    X = pd.read_csv(DATA / "Input/X_test.csv", dtype={"collision_index": str})
    X = X.set_index("collision_index")[features]
    y = pd.read_csv(DATA / "Input/y_test.csv", dtype={"collision_index": str})
    y = y.set_index("collision_index").loc[X.index].iloc[:, 0].to_numpy()

    locations = build_locations(X)
    (OUT / "locations.json").write_text(json.dumps(locations, separators=(",", ":")))
    print(f"locations: {len(locations)}, senza nome area: {sum(not l['area'] for l in locations)}")

    ages = band_ages()
    (OUT / "ages.json").write_text(json.dumps(ages))
    print("età mediane per fascia:", ages)

    base, drops = group_importance(bundle["model"].named_steps["model"], X, y)
    print(f"AUC sul campione: {base:.4f}")
    for name, d in sorted(drops.items(), key=lambda kv: -kv[1]):
        print(f"  {name:18s} {d:.4f}")


main()
