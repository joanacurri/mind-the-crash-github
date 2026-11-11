// Share of locations where typical calls come out "grave", age left at "non so".
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [dataDir, callPath] = process.argv.slice(2);
const { assess, emptyAnswers } = await import(pathToFileURL(callPath));
const read = (f) => JSON.parse(readFileSync(`${dataDir}/${f}`, "utf8"));
const model = read("trees.json"), meta = read("meta.json"), ages = read("ages.json");
const locs = read("locations.json").slice(0, 200);
const now = new Date("2026-10-21T15:30:00");

const veh = (o) => ({ auto: 0, moto_big: 0, moto_small: 0, bici: 0, altri: 0, ...o });
const cas = (o) => ({ auto: 0, due_ruote: 0, pedoni: 0, furgone: 0, pedone_attraversa: false, ...o });
const calls = {
  "nessuna risposta": {},
  "2 auto, 1 ferito in auto": { veicoli: veh({ auto: 2 }), feriti: cas({ auto: 1 }) },
  "2 auto, 2 feriti in auto": { veicoli: veh({ auto: 2 }), feriti: cas({ auto: 2 }) },
  "1 auto, 1 pedone": { veicoli: veh({ auto: 1 }), feriti: cas({ pedoni: 1 }) },
  "auto + bici, ciclista ferito": { veicoli: veh({ auto: 1, bici: 1 }), feriti: cas({ due_ruote: 1 }) },
  "auto + moto>125, motociclista": { veicoli: veh({ auto: 1, moto_big: 1 }), feriti: cas({ due_ruote: 1 }) },
  "solo 2 auto, feriti non so": { veicoli: veh({ auto: 2 }) },
};
for (const [name, a] of Object.entries(calls)) {
  const ps = locs.map((loc) => assess(model, { ...emptyAnswers(), ...a, limite: loc.speed_limit },
                                      { meta, ages, loc, now }).p);
  const grave = ps.filter((p) => p >= meta.threshold).length / ps.length;
  const med = ps.sort((x, y) => x - y)[100];
  console.log(`${name.padEnd(32)} p mediana ${med.toFixed(3)} | grave nel ${(grave * 100).toFixed(0)}%`);
}
