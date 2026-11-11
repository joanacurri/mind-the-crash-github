# 04_Models – saving, loading and which cells to run

## What the saved file contains

Tuning and fitting run once; after that the notebook reloads everything from `../00_Data/Models/models_04.joblib` and restarts from the threshold choice.

| Key | Content | Used for |
|---|---|---|
| `features` | list of the columns used in training | check at load time |
| `searches` | full Random Search (`cv_results_`, `best_params_`) | tuning table |
| `best_params_dict` | hyperparameters chosen per model | report |
| `models` | tuned models, not fitted | optional re-fit |
| `fitted` | models fitted on the training set | overfitting, importance, scoring |
| `probs` | probabilities on the validation set | assessment, threshold, matrix |
| `oof_probs` | out-of-fold probabilities of the best model | threshold choice |
| `cv_auc` | per-fold AUC of the best model | report |

The file must be regenerated (full path below) whenever you change something in 01, 02 or 03, or update scikit-learn or xgboost: a `.joblib` only loads with the same library versions.

## Full path: first time, or after changes to 01–03

Do Restart & Run All: the notebook trains everything, saves the file and reloads it straight away. Order of the sections:

1. Imports and configuration: libraries, `RS`, `N_FOLDS`, `N_ITER_MODEL`
2. Loading the data: CSVs in `00_Data/Input` and `selected_features.csv`
3. Data preparation: creates `X_tr`, `X_te`, `y_tr`, `y_te` and checks `collision_injury_based`
4. Column name clean-up: asserts on float32 and names
5. Preprocessing: `bin_cols`, `num_cols`, `scaler()` function
6. Model definitions: `make_models()`
7. Hyperparameter tuning: Random Search (the slow part)
8. Fit on the full training set: creates `fitted` and `probs`
9. `cv_run` function and OOF of the best model: creates `oof_probs` for the threshold
10. Saving: writes `models_04.joblib`
11. Loading and all the following cells (next section)

## Quick path: restarting from the load

After a kernel restart, run only the cells that prepare the data, then jump straight to the load: the file contains the models, not `X_tr`, `X_te`, `y_tr`, `y_te`.

| Section | Run? | Why |
|---|---|---|
| Imports and configuration | Yes | libraries and `RS` are used everywhere |
| Loading the data | Yes | `X_test` is needed by the scoring for the `collision_index` index |
| Data preparation | Yes | creates `X_tr`, `X_te`, `y_tr`, `y_te` |
| Column name clean-up | Yes | quick checks |
| Preprocessing | No | the scaler is already inside the saved pipelines |
| Model definitions | No | the models come from the file |
| Hyperparameter tuning | No | `searches` comes from the file |
| Fit on the full training set | No | `fitted` and `probs` come from the file |
| Training vs validation | No* | see next section |
| `cv_run` and OOF | No | `oof_probs` comes from the file |
| Saving | No | it would overwrite the file |
| Loading | Yes | reloads everything and checks the features |
| Choosing the threshold | Yes | defines `best`, `t_rec`, `RECALL_TARGET` |
| Confusion matrix at the chosen threshold | Yes | defines `THR` |
| Feature importance | Yes | uses `fitted[best]` and `X_te` |
| Scoring | Yes | uses `fitted[best]`, `THR`, `X_test` |

*With this path you do not see the ROC curves, the lift and the overfitting table again, because they are in skipped cells. To get them here too, apply the reorganisation in the next section.

Order matters: "Choosing the threshold" must run before the matrix, and the matrix before the scoring, because each creates variables used by the next.

## Suggested reorganisation

Moving the analysis after the load makes the two paths produce the same outputs: the part before trains and saves, the part after analyses.

1. In the "Fit on the full training set" cell keep only the fit loop (it creates `fitted` and `probs`).
2. Create a new cell right after "Loading" and paste in the rest of that cell: `test_res`, ROC curves and cumulative lift. They only use `probs` and `y_te`.
3. Move the "Training vs validation: overfitting check" cell after the new one. It uses `fitted`, `X_tr`, `y_tr`, `probs`, `y_te`, all available after the load.
4. Leave the OOF cell where it is (before the save): the OOF probabilities need the CV and must end up in the file.

Final order after the load: Loading → Assessment (ROC, lift) → Overfitting → Threshold → Matrix → Feature importance → Scoring.

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `AssertionError: Le feature sono cambiate` | 01, 02 or 03 re-run with changes: `selected_features.csv` no longer matches | Full path |
| `FileNotFoundError` on `models_04.joblib` | file never created, or different folder | Full path; check `MODEL_DIR` |
| Unpickling or attribute errors at load time | scikit-learn or xgboost version changed | Full path with the new versions |
| `NameError: X_tr` (or `y_te`, `X_test`) | data preparation cells skipped | Run imports, loading and data preparation |
| `NameError: best` or `t_rec` | "Choosing the threshold" skipped | Run it before the matrix and the scoring |
| `NameError: THR` | "Confusion matrix at the chosen threshold" skipped | Run it before the scoring |
| `NameError: best_x` in the OOF cell | `best_x = models[best]` is missing | Add it under the `best` line |

Rule of thumb: if in doubt about the kernel state, Restart and take the quick path from the top; the load takes a few seconds.
