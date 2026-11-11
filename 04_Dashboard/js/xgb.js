// Evaluates the exported XGBoost model (binary:logistic) in the browser.
// XGBoost compares in float32, so both sides go through Math.fround.

export function predict(model, x) {
  let margin = model.base_margin;
  for (const t of model.trees) {
    let i = 0;
    while (t.left_children[i] !== -1) {
      const v = x[t.split_indices[i]];
      if (v === null || v === undefined || Number.isNaN(v)) {
        i = t.default_left[i] ? t.left_children[i] : t.right_children[i];
      } else {
        i = Math.fround(v) < Math.fround(t.split_conditions[i])
          ? t.left_children[i] : t.right_children[i];
      }
    }
    margin += t.split_conditions[i];  // a leaf stores its value here
  }
  return 1 / (1 + Math.exp(-margin));
}
