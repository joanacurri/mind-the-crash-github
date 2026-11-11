// Runs three typical calls through call.js and prints the verdicts.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [dataDir, callPath] = process.argv.slice(2);
const { assess, emptyAnswers } = await import(pathToFileURL(callPath));
const read = (f) => JSON.parse(readFileSync(`${dataDir}/${f}`, "utf8"));
const model = read("trees.json");
const ctx = { meta: read("meta.json"), ages: read("ages.json"),
              loc: read("locations.json")[0], now: new Date("2026-10-21T15:30:00") };
console.log("posizione:", ctx.loc);

const veh = (o) => ({ auto: 0, moto_big: 0, moto_small: 0, bici: 0, altri: 0, ...o });
const cas = (o) => ({ auto: 0, due_ruote: 0, pedoni: 0, furgone: 0, pedone_attraversa: false, ...o });
const calls = {
  "nessuna risposta": emptyAnswers(),
  "tamponamento in città": { ...emptyAnswers(), veicoli: veh({ auto: 2 }),
    feriti: cas({ auto: 1 }), eta: "adulto", urto: "tamponamento", limite: 30 },
  "moto fuori città, anziano": { ...emptyAnswers(), veicoli: veh({ auto: 1, moto_big: 1 }),
    feriti: cas({ due_ruote: 1 }), eta: "anziano", urto: "frontale", limite: 60 },
  "pedone che attraversa, buio": { ...emptyAnswers(), veicoli: veh({ auto: 1 }),
    feriti: cas({ pedoni: 1, pedone_attraversa: true }), eta: "anziano", limite: 30,
    luce: "buio_non" },
};
for (const [name, ans] of Object.entries(calls)) {
  const r = assess(model, ans, ctx);
  const why = r.reasons.slice(0, 3).map((x) => `${x.q} ${x.delta >= 0 ? "+" : ""}${x.delta.toFixed(2)}`);
  console.log(`${name.padEnd(28)} p=${r.p.toFixed(3)} ${r.grave ? "GRAVE" : "lieve"} ` +
              `(${r.answered}/${r.total}) | ${why.join(", ")}`);
}
