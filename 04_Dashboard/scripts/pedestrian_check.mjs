// Simulator probability for "1 car, 1 injured pedestrian" by age band, over many locations.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [dataDir, callPath] = process.argv.slice(2);
const { assess, emptyAnswers } = await import(pathToFileURL(callPath));
const read = (f) => JSON.parse(readFileSync(`${dataDir}/${f}`, "utf8"));
const model = read("trees.json"), meta = read("meta.json"), ages = read("ages.json");
const locs = read("locations.json").slice(0, 200);
const now = new Date("2026-10-21T15:30:00");

const base = { ...emptyAnswers(),
  veicoli: { auto: 1, moto_big: 0, moto_small: 0, bici: 0, altri: 0 },
  feriti: { auto: 0, due_ruote: 0, pedoni: 1, furgone: 0, pedone_attraversa: false } };
for (const eta of [null, "bambino", "adulto", "anziano"]) {
  const ps = locs.map((loc) => assess(model, { ...base, eta, limite: loc.speed_limit },
                                      { meta, ages, loc, now }).p).sort((a, b) => a - b);
  const grave = ps.filter((p) => p >= meta.threshold).length / ps.length;
  console.log(`età ${String(eta).padEnd(8)} mediana p ${ps[100].toFixed(3)} | grave in ${(grave * 100).toFixed(0)}% delle posizioni`);
}
