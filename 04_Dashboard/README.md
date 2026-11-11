# Mind the Crash – dashboard

Four pages built with the GOV.UK Design System: the simulator for the 999 call handler, the model threshold,
what weighs most in the estimate, and the map of where collisions turn serious.

## Opening it

- **Windows:** double-click `Open the simulator.bat`.
- **Mac/Linux:** from a terminal in this folder, `python3 serve.py`.

The browser opens at http://localhost:4321/take-a-call.html. Only Python is needed (no packages).
Double-clicking the `.html` files does not work: the browser blocks the data from loading.

## What is here

- `take-a-call.qmd`, `how-it-works.qmd`, `what-matters.qmd`, `where-serious.qmd`: Quarto sources
  (OJS); the `.html` files are already rendered.
- `data/`: the exported XGBoost model (`trees.json`) and the aggregated data the pages read.
- `js/`: the model evaluated in the browser (`xgb.js`), the translation from answers to the 40 features
  (`call.js`), the GOV.UK-style controls.
- `scripts/`: the Python scripts that produced `data/` from the model bundle and the CSVs.

The model in the browser gives the same probabilities as `best_model_bundle.joblib`
(checked against `score_validation.csv`).
