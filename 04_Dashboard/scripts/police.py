"""Where each collision happened, labelled from the DfT data guide: police force area and district."""
import pandas as pd

GUIDE = ("File_di_spiegazione_dataset/"
         "dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025 (1).xlsx")
COLLISIONS = "00_Data/5_years/dft-road-casualty-statistics-collision-last-5-years.csv"


def guide_labels(project, field, numeric):
    guide = pd.read_excel(project / GUIDE, sheet_name="2024_code_list")
    rows = guide[guide["field name"] == field]
    codes = rows["code/format"]
    if numeric:
        codes = pd.to_numeric(codes, errors="coerce")  # some rows are notes
        rows, codes = rows[codes.notna()], codes.dropna().astype(int)
    return dict(zip(codes, rows["label"]))


def collision_places(project):
    """DataFrame indexed by collision_index: area (police force) and district names."""
    raw = pd.read_csv(project / COLLISIONS, dtype={"collision_index": str},
                      usecols=["collision_index", "police_force", "local_authority_ons_district"])
    raw = raw.set_index("collision_index")
    return pd.DataFrame({
        "area": raw["police_force"].map(guide_labels(project, "police_force", True)),
        "district": raw["local_authority_ons_district"].map(
            guide_labels(project, "local_authority_ons_district", False)),
    })


def collision_areas(project):
    """Series: collision_index → police force area name."""
    return collision_places(project)["area"]
