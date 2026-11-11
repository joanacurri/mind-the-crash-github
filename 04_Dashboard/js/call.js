// Translates the operator's answers into the 40 model features.
// An answer left at null ("non so") keeps the training median from meta.defaults.
import { predict } from "./xgb.js";

// Question keys, in the order the explanation and the "k of M" counter use.
export const QUESTIONS = [
  "veicoli", "feriti", "eta", "urto", "limite",
  "manovra", "uscita", "luce", "ribaltato", "strada", "incrocio",
];

const sum = (obj) => Object.values(obj).reduce((a, b) => a + b, 0);
const cap4 = (n) => Math.min(n, 4);  // the model saw counts truncated at 4

// Vehicles: {auto, moto_big, moto_small, bici, altri}; all zero means not answered.
// Casualties: {auto, due_ruote, pedoni, furgone, pedone_attraversa}.
export function emptyAnswers() {
  return {
    veicoli: null, feriti: null, eta: null, urto: null, limite: null,
    manovra: null, uscita: null, luce: null, ribaltato: null, strada: null, incrocio: null,
  };
}

function isoWeek(date) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil(((d - yearStart) / 86400000 + 1) / 7);
}

export function toFeatures(ans, ctx) {
  const { meta, ages, loc, now } = ctx;
  const f = { ...meta.defaults };

  // From the phone ping and the clock: never asked.
  f.latitude = loc.lat;
  f.longitude = loc.lon;
  f.urban_or_rural_area_Urban = loc.urban;
  f.collision_injury_based = loc.ibrs;
  f.woy = isoWeek(now);
  f.time_period_afternoon = now.getHours() >= 12 && now.getHours() < 18 ? 1 : 0;

  const v = ans.veicoli;
  const N = v ? Math.max(1, cap4(sum(v))) : meta.defaults.number_of_vehicles;
  if (v) {
    f.number_of_vehicles = N;
    f["vehicle_type_Motorcycle over 125cc"] = v.moto_big;
    f["vehicle_type_Motorcycle up to 125cc"] = v.moto_small;
    f["vehicle_type_Pedal cycle"] = v.bici;
  }
  // Per-vehicle counts that follow from N unless an answer says otherwise.
  f["vehicle_location_restricted_lane_Main carriageway"] = N;
  const overturned = ans.ribaltato === "si" ? 1 : 0;
  f["skidding_and_overturning_Overturned"] = overturned;
  f["skidding_and_overturning_None"] = N - overturned;

  const c = ans.feriti;
  if (c) {
    const inVehicle = c.auto + c.due_ruote + c.furgone;
    // Assumption: one casualty per vehicle is its driver, riders are always drivers.
    const drivers = c.due_ruote + Math.min(c.auto, v ? v.auto : 1)
      + Math.min(c.furgone, v ? v.altri : 1);
    f.number_of_casualties = Math.max(1, cap4(inVehicle + c.pedoni));
    f.casualty_type_Car = c.auto;
    f.casualty_type_Van = c.furgone;
    f.casualty_class_Pedestrian = c.pedoni;
    f["casualty_class_Driver or rider"] = drivers;
    f.casualty_class_Passenger = inVehicle - drivers;
    f.pedestrian_movement_Crossing = c.pedone_attraversa ? c.pedoni : 0;
  }

  if (ans.eta) f.age_of_casualty_mean = ages[ans.eta].age;
  if (ans.limite) f.speed_limit = ans.limite;

  const impact = {
    frontale: [Math.min(N, 2), 0, 0], tamponamento: [1, 1, 0], laterale: [1, 0, 1],
  }[ans.urto];
  if (impact) {
    [f.first_point_of_impact_Front, f.first_point_of_impact_Back,
     f.first_point_of_impact_Side] = impact;
  }

  const manoeuvre = {
    dritto: [N, 0, 0], svolta: [N - 1, 0, 1], fermo: [N - 1, 1, 0],
  }[ans.manovra];
  if (manoeuvre) {
    [f["vehicle_manoeuvre_Going ahead"], f["vehicle_manoeuvre_Waiting or slowing"],
     f.vehicle_manoeuvre_Turning] = manoeuvre;
  }

  const leaving = { no: [0, 0, 0], si: [1, 0, 0], albero: [1, 0, 1] }[ans.uscita];
  if (leaving) {
    [f.vehicle_leaving_carriageway_Nearside, f.vehicle_leaving_carriageway_Offside,
     f.hit_object_off_carriageway_Tree] = leaving;
  }

  const light = { giorno: [0, 0], buio_illuminato: [1, 0], buio_non: [0, 1] }[ans.luce];
  if (light) {
    [f["light_conditions_Darkness - lights lit"],
     f["light_conditions_Darkness - no or unlit lighting"]] = light;
  }

  const road = { superstrada: [0, 0, 0], principale: [1, 1, 0], locale: [1, 0, 1] }[ans.strada];
  if (road) {
    [f["road_type_Single carriageway"], f["road_class_name_Main road"],
     f["road_class_name_Local road"]] = road;
  }

  const junction = { no: [N, 0], semaforo: [0, 0], precedenza: [0, 1] }[ans.incrocio];
  if (junction) {
    [f["junction_location_Not at junction"],
     f["junction_control_Give way or uncontrolled"]] = junction;
  }

  return meta.features.map((name) => f[name]);
}

// Age "non so" averages p over the bands, weighted by how common each is. The training
// median (35) is also the value missing ages were imputed with, and the model reads it
// as "age missing, probably slight".
function probability(model, ans, ctx) {
  if (ans.eta) return predict(model, toFeatures(ans, ctx));
  return Object.entries(ctx.ages).reduce(
    (acc, [band, { share }]) => acc + share * predict(model, toFeatures({ ...ans, eta: band }, ctx)),
    0,
  );
}

export function assess(model, ans, ctx) {
  const p = probability(model, ans, ctx);
  const answered = QUESTIONS.filter((q) => ans[q] !== null);
  // How much each answer moved p: the same call with that answer set to "non so".
  const reasons = answered
    .map((q) => ({ q, delta: p - probability(model, { ...ans, [q]: null }, ctx) }))
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  return {
    p, grave: p >= ctx.meta.threshold, reasons,
    answered: answered.length, total: QUESTIONS.length,
  };
}
