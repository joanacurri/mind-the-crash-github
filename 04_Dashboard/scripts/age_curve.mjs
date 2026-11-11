// Probability as a function of casualty age for "1 car, 1 injured pedestrian", median over locations.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [dataDir, callPath, xgbPath] = process.argv.slice(2);
const { toFeatures, emptyAnswers } = await import(pathToFileURL(callPath));
const { predict } = await import(pathToFileURL(xgbPath));
const read = (f) => JSON.parse(readFileSync(`${dataDir}/${f}`, "utf8"));
const model = read("trees.json"), meta = read("meta.json"), ages = read("ages.json");
const locs = read("locations.json").slice(0, 200);
const now = new Date("2026-10-21T15:30:00");
const iAge = meta.features.indexOf("age_of_casualty_mean");

const ans = { ...emptyAnswers(),
  veicoli: { auto: 1, moto_big: 0, moto_small: 0, bici: 0, altri: 0 },
  feriti: { auto: 0, due_ruote: 0, pedoni: 1, furgone: 0, pedone_attraversa: false } };
const rows = [];
for (const age of [10, 20, 30, 33, 34, 34.5, 35, 35.5, 36, 40, 50, 60, 74]) {
  const ps = locs.map((loc) => {
    const x = toFeatures({ ...ans, limite: loc.speed_limit }, { meta, ages, loc, now });
    x[iAge] = age;
    return predict(model, x);
  }).sort((a, b) => a - b);
  rows.push(`${age}: ${ps[100].toFixed(3)}`);
}
console.log(rows.join(" | "));
