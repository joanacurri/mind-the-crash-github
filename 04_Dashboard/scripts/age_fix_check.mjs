// Old vs new simulator on random calls. Old behaviour = age "non so" left at the median (35).
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [dataDir, callPath, xgbPath] = process.argv.slice(2);
const { assess, toFeatures } = await import(pathToFileURL(callPath));
const { predict } = await import(pathToFileURL(xgbPath));
const read = (f) => JSON.parse(readFileSync(`${dataDir}/${f}`, "utf8"));
const model = read("trees.json"), meta = read("meta.json"), ages = read("ages.json");
const locs = read("locations.json");
const now = new Date("2026-10-21T15:30:00");

let seed = 42;
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const pick = (xs) => xs[Math.floor(rnd() * xs.length)];
const count = () => pick([0, 0, 1, 1, 2]);

function randomCall() {
  const veicoli = { auto: count(), moto_big: count() * (rnd() < .2), moto_small: count() * (rnd() < .2),
                    bici: count() * (rnd() < .2), altri: count() * (rnd() < .2) };
  const feriti = { auto: count(), due_ruote: count() * (rnd() < .3), pedoni: count() * (rnd() < .3),
                   furgone: 0, pedone_attraversa: rnd() < .5 };
  if (!Object.values(veicoli).some((n) => n > 0)) veicoli.auto = 1;
  if (feriti.auto + feriti.due_ruote + feriti.pedoni === 0) feriti.auto = 1;
  return {
    veicoli, feriti, eta: pick([null, "bambino", "adulto", "anziano"]),
    urto: pick([null, "frontale", "tamponamento", "laterale"]), limite: pick([20, 30, 40, 50, 60, 70]),
    manovra: pick([null, "dritto", "svolta", "fermo"]), uscita: pick([null, "no", "si", "albero"]),
    luce: pick([null, "giorno", "buio_illuminato", "buio_non"]), ribaltato: pick([null, "no", "si"]),
    strada: pick([null, "superstrada", "principale", "locale"]), incrocio: pick([null, "no", "semaforo", "precedenza"]),
  };
}

const stats = { known: { n: 0, maxDiff: 0 }, unknown: { n: 0, diffs: [], toGrave: 0, toLieve: 0 } };
for (let i = 0; i < 20000; i++) {
  const ans = randomCall();
  const ctx = { meta, ages, loc: pick(locs), now };
  const pOld = predict(model, toFeatures(ans, ctx));
  const pNew = assess(model, ans, ctx).p;
  const thr = meta.threshold;
  if (ans.eta) {
    stats.known.n++;
    stats.known.maxDiff = Math.max(stats.known.maxDiff, Math.abs(pNew - pOld));
  } else {
    const s = stats.unknown;
    s.n++; s.diffs.push(pNew - pOld);
    if (pOld < thr && pNew >= thr) s.toGrave++;
    if (pOld >= thr && pNew < thr) s.toLieve++;
  }
}
const u = stats.unknown, d = u.diffs.sort((a, b) => a - b);
const q = (f) => d[Math.floor(f * (d.length - 1))].toFixed(3);
console.log(`età indicata: ${stats.known.n} chiamate, differenza massima ${stats.known.maxDiff}`);
console.log(`età non so: ${u.n} chiamate | differenza p (nuovo - vecchio) mediana ${q(.5)}, ` +
            `5° pct ${q(.05)}, 95° pct ${q(.95)}, max ${q(1)}`);
console.log(`verdetti cambiati: lieve->grave ${(u.toGrave / u.n * 100).toFixed(1)}%, ` +
            `grave->lieve ${(u.toLieve / u.n * 100).toFixed(1)}%`);
