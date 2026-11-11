// Compares the JS evaluator with Python's predict_proba on every validation row.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [modelPath, csvPath, xgbPath] = process.argv.slice(2);
const { predict } = await import(pathToFileURL(xgbPath));
const model = JSON.parse(readFileSync(modelPath, "utf8"));

const lines = readFileSync(csvPath, "utf8").trim().split("\n").slice(1);
let maxDiff = 0, flips = 0;
const t0 = performance.now();
for (const line of lines) {
  const row = line.split(",").map(Number);
  const pPy = row.pop();
  const pJs = predict(model, row);
  maxDiff = Math.max(maxDiff, Math.abs(pJs - pPy));
  if ((pJs >= 0.221) !== (pPy >= 0.221)) flips++;
}
const ms = performance.now() - t0;
console.log(`rows ${lines.length} | max diff ${maxDiff.toExponential(2)} | ` +
            `decisions changed ${flips} | ${(ms / lines.length * 1000).toFixed(1)} µs/prediction`);
