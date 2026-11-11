"""Build importance.json: how much each question weighs, and which way each answer pushes.

SHAP contributions (XGBoost pred_contribs) on a sample of held-out collisions, summed over the
features each operator question fills in.
weight  share of the mean |contribution| that falls on each question
answers for the collisions with a given answer, the average change in probability that
        question's contribution makes: p - sigmoid(margin without it), in points
"""
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

PROJECT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
DATA = PROJECT / "00_Data"
SEED = 42
N_SAMPLE = 30_000

# Question → the features it fills in; the same split as prep_data.GROUPS, labelled for the page.
QUESTIONS = {
    "Casualties": ["number_of_casualties", "casualty_type_Car", "casualty_type_Van",
                   "casualty_class_Driver or rider", "casualty_class_Passenger",
                   "casualty_class_Pedestrian", "pedestrian_movement_Crossing"],
    "Vehicles involved": ["number_of_vehicles", "vehicle_type_Motorcycle over 125cc",
                          "vehicle_type_Motorcycle up to 125cc", "vehicle_type_Pedal cycle"],
    "Age of the casualties": ["age_of_casualty_mean"],
    "Type of impact": ["first_point_of_impact_Front", "first_point_of_impact_Back",
                       "first_point_of_impact_Side"],
    "Speed limit": ["speed_limit"],
    "Light": ["light_conditions_Darkness - lights lit",
              "light_conditions_Darkness - no or unlit lighting"],
    "Type of road": ["road_type_Single carriageway", "road_class_name_Main road",
                     "road_class_name_Local road"],
    "Junction": ["junction_location_Not at junction", "junction_control_Give way or uncontrolled"],
    "Leaving the road": ["vehicle_leaving_carriageway_Nearside",
                         "vehicle_leaving_carriageway_Offside", "hit_object_off_carriageway_Tree"],
    "Overturned vehicle": ["skidding_and_overturning_None", "skidding_and_overturning_Overturned"],
    "What the vehicles were doing": ["vehicle_manoeuvre_Going ahead",
                                     "vehicle_manoeuvre_Waiting or slowing",
                                     "vehicle_manoeuvre_Turning"],
    "Sex of the driver (not asked)": ["sex_of_driver_Male", "sex_of_driver_Female"],
    "Main carriageway (not asked)": ["vehicle_location_restricted_lane_Main carriageway"],
    "Location (from the phone)": ["latitude", "longitude", "urban_or_rural_area_Urban",
                                  "collision_injury_based"],
    "Time of call (from the clock)": ["woy", "time_period_afternoon"],
}

# Answer → (question, rows that gave it). Age 35 is the imputed value, so no band includes it.
ANSWERS = {
    "A pedestrian was hurt": ("Casualties", lambda X: X["casualty_class_Pedestrian"] > 0),
    "Only car occupants were hurt": (
        "Casualties", lambda X: X["casualty_type_Car"] == X["number_of_casualties"]),
    "A motorcycle over 125cc": (
        "Vehicles involved", lambda X: X["vehicle_type_Motorcycle over 125cc"] > 0),
    "A pedal cycle": ("Vehicles involved", lambda X: X["vehicle_type_Pedal cycle"] > 0),
    "Only one vehicle": ("Vehicles involved", lambda X: X["number_of_vehicles"] == 1),
    "Three or more vehicles": ("Vehicles involved", lambda X: X["number_of_vehicles"] >= 3),
    "Casualty aged 65 or over": ("Age of the casualties", lambda X: X["age_of_casualty_mean"] >= 65),
    "Casualty under 16": ("Age of the casualties", lambda X: X["age_of_casualty_mean"] < 16),
    "Rear-end impact": ("Type of impact", lambda X: X["first_point_of_impact_Back"] > 0),
    "Speed limit 60 or 70 mph": ("Speed limit", lambda X: X["speed_limit"] >= 60),
    "Speed limit 20 or 30 mph": ("Speed limit", lambda X: X["speed_limit"] <= 30),
    "Dark, no street lights": (
        "Light", lambda X: X["light_conditions_Darkness - no or unlit lighting"] > 0),
    "A vehicle hit a tree": (
        "Leaving the road", lambda X: X["hit_object_off_carriageway_Tree"] > 0),
    "A vehicle overturned": (
        "Overturned vehicle", lambda X: X["skidding_and_overturning_Overturned"] > 0),
    "Give way or uncontrolled junction": (
        "Junction", lambda X: X["junction_control_Give way or uncontrolled"] > 0),
    "Rural area": ("Location (from the phone)", lambda X: X["urban_or_rural_area_Urban"] == 0),
}


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def main():
    bundle = joblib.load(DATA / "Models/best_model_bundle.joblib")
    features = bundle["features"]
    assert sorted(sum(QUESTIONS.values(), [])) == sorted(features), "questions must cover the 40"

    X = pd.read_csv(DATA / "Input/X_test.csv", dtype={"collision_index": str})
    X = X.set_index("collision_index")[features].sample(N_SAMPLE, random_state=SEED)
    booster = bundle["model"].named_steps["model"].get_booster()
    contribs = booster.predict(xgb.DMatrix(X.astype("float32")), pred_contribs=True)
    margin = contribs.sum(axis=1)
    col = {f: i for i, f in enumerate(booster.feature_names)}
    by_q = {q: contribs[:, [col[f] for f in fs]].sum(axis=1) for q, fs in QUESTIONS.items()}

    size = {q: np.abs(s).mean() for q, s in by_q.items()}
    weights = [{"question": q, "share": round(float(v / sum(size.values())), 4)}
               for q, v in sorted(size.items(), key=lambda kv: -kv[1])]

    points = {q: sigmoid(margin) - sigmoid(margin - s) for q, s in by_q.items()}
    answers = []
    for label, (q, rows) in ANSWERS.items():
        mask = rows(X).to_numpy()
        answers.append({"answer": label, "question": q, "n": int(mask.sum()),
                        "points": round(float(points[q][mask].mean() * 100), 1)})
    answers.sort(key=lambda a: -a["points"])

    out = {"n": N_SAMPLE, "weights": weights, "answers": answers}
    (OUT / "importance.json").write_text(json.dumps(out, indent=1))
    for w in weights:
        print(f"  {w['question']:32s} {w['share']:.3f}")
    for a in answers:
        print(f"  {a['answer']:36s} {a['points']:+6.1f}  n={a['n']}")


main()
