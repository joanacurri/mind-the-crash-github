"""Build map.json: held-out collisions binned into hexagons, plus a table by police force area.

Each hexagon and area carries counts only (collisions, serious, serious the model missed at its
threshold); the page turns them into shares and colour classes.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))  # -I leaves the script folder off the path
from police import collision_places  # noqa: E402

PROJECT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
DATA = PROJECT / "00_Data"
R = 0.14            # hexagon radius, in degrees of latitude
LAT0 = 54.5         # longitude is shrunk by cos(LAT0) so the map is not stretched
MIN_HEX = 30        # fewer collisions than this: no share shown


def hex_bin(x, y):
    """Axial coordinates of the pointy-top hexagon of radius R holding each point."""
    q = (np.sqrt(3) / 3 * x - y / 3) / R
    r = (2 / 3 * y) / R
    cx, cz = q, r
    cy = -cx - cz
    rx, ry, rz = np.round(cx), np.round(cy), np.round(cz)
    dx, dy, dz = np.abs(rx - cx), np.abs(ry - cy), np.abs(rz - cz)
    fix_x = (dx > dy) & (dx > dz)
    fix_z = ~fix_x & (dz >= dy)
    rx = np.where(fix_x, -ry - rz, rx)
    rz = np.where(fix_z, -rx - ry, rz)
    return rx.astype(int), rz.astype(int)


def counts(df, keys):
    g = df.groupby(keys)
    return pd.DataFrame({"n": g.size(), "serious": g["serious"].sum(), "missed": g["missed"].sum()})


def place(g):
    """The two districts with most collisions in a hexagon, and its main police force area."""
    districts = g["district"].value_counts().index[:2]
    area = g["area"].mode()
    return {"districts": list(districts), "area": area.iloc[0] if len(area) else "",
            "areas": sorted(g["area"].dropna().unique())}  # every force with a collision here


def main():
    meta = json.loads((OUT / "meta.json").read_text())
    X = pd.read_csv(DATA / "Input/X_test.csv", dtype={"collision_index": str},
                    usecols=["collision_index", "latitude", "longitude", "urban_or_rural_area_Urban"])
    y = pd.read_csv(DATA / "Input/y_test.csv", dtype={"collision_index": str})
    s = pd.read_csv(DATA / "Output/score_validation.csv", dtype={"collision_index": str})
    df = X.merge(y, on="collision_index", validate="1:1").merge(s, on="collision_index",
                                                                 validate="1:1")
    assert len(df) == len(X) == len(s), "test rows must match"
    df["serious"] = df["collision_severity_bin"] == 1
    df["missed"] = df["serious"] & (df["p_grave"] < meta["threshold"])

    df["x"] = df["longitude"] * np.cos(np.radians(LAT0))
    df["q"], df["r"] = hex_bin(df["x"].to_numpy(), df["latitude"].to_numpy())
    hexes = counts(df, ["q", "r"]).reset_index()  # sorted by (q, r), like groupby below
    hexes["cx"] = (R * np.sqrt(3) * (hexes["q"] + hexes["r"] / 2)).round(4)
    hexes["cy"] = (R * 1.5 * hexes["r"]).round(4)

    df = df.join(collision_places(PROJECT), on="collision_index")
    hexes["place"] = [place(g) for _, g in df.groupby(["q", "r"])]
    areas = counts(df.dropna(subset=["area"]), "area").reset_index()
    setting = counts(df.assign(setting=np.where(df["urban_or_rural_area_Urban"] == 1,
                                                "Urban", "Rural")), "setting").reset_index()

    out = {"radius": R, "min_hex": MIN_HEX, "n": len(df),
           "hexes": hexes[["cx", "cy", "n", "serious", "missed", "place"]].to_dict("records"),
           "areas": areas.to_dict("records"), "setting": setting.to_dict("records")}
    (OUT / "map.json").write_text(json.dumps(out, separators=(",", ":"), default=int))
    print(f"rows {len(df)}, hexes {len(hexes)} ({(hexes['n'] >= MIN_HEX).sum()} shown), "
          f"areas {len(areas)}, no area {df['area'].isna().sum()}")
    print(setting.assign(share=setting["serious"] / setting["n"],
                         miss=setting["missed"] / setting["serious"]))


main()
