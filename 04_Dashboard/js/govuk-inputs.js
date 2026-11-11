// GOV.UK Design System inputs that OJS can use as views: each exposes .value and
// fires a bubbling "input" event when it changes.

let uid = 0;

// The node must come back detached: OJS inserts a node only if it has no parent,
// otherwise it shows it as an inspected object.
function el(markup) {
  const box = document.createElement("div");
  box.innerHTML = markup.trim();
  const node = box.firstElementChild;
  node.remove();
  return node;
}

const notify = (node) => node.dispatchEvent(new Event("input", { bubbles: true }));

// options: [[label, value], ...]; a value of null is the "Don't know" answer.
export function radios(legend, options, { value = null, hint = "" } = {}) {
  const name = `q${++uid}`;
  const items = options.map(([label], i) => `
    <div class="govuk-radios__item">
      <input class="govuk-radios__input" id="${name}-${i}" name="${name}" type="radio" value="${i}">
      <label class="govuk-label govuk-radios__label" for="${name}-${i}">${label}</label>
    </div>`).join("");
  const node = el(`
    <div class="govuk-form-group q-row">
      <fieldset class="govuk-fieldset">
        <legend class="govuk-fieldset__legend govuk-fieldset__legend--s">${legend}</legend>
        ${hint ? `<div class="govuk-hint">${hint}</div>` : ""}
        <div class="govuk-radios govuk-radios--small govuk-radios--inline">${items}</div>
      </fieldset>
    </div>`);
  const initial = options.findIndex(([, v]) => v === value);
  if (initial >= 0) node.querySelectorAll("input")[initial].checked = true;
  node.value = value;
  // Registered before OJS's own listener, so the value is updated when OJS reads it.
  node.addEventListener("input", (e) => { node.value = options[+e.target.value][1]; });
  return node;
}

// A group of − / + counters; value is {key: count}. The model saw counts capped at 4.
export function counters(legend, items, { max = 4, hint = "" } = {}) {
  const rows = items.map(([key, label]) => `
    <div class="counter" data-key="${key}">
      <span class="govuk-label counter__label">${label}</span>
      <div class="counter__row">
        <button type="button" class="govuk-button govuk-button--secondary counter__btn"
                data-step="-1" aria-label="${label}: one fewer">−</button>
        <output class="counter__value" aria-live="polite">0</output>
        <button type="button" class="govuk-button govuk-button--secondary counter__btn"
                data-step="1" aria-label="${label}: one more">+</button>
      </div>
    </div>`).join("");
  const node = el(`
    <div class="govuk-form-group">
      <fieldset class="govuk-fieldset">
        <legend class="govuk-fieldset__legend govuk-fieldset__legend--s">${legend}</legend>
        ${hint ? `<div class="govuk-hint">${hint}</div>` : ""}
        <div class="counter-group">${rows}</div>
      </fieldset>
    </div>`);
  node.value = Object.fromEntries(items.map(([key]) => [key, 0]));
  node.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-step]");
    if (!btn) return;
    const box = btn.closest(".counter");
    const n = Math.min(max, Math.max(0, node.value[box.dataset.key] + Number(btn.dataset.step)));
    node.value = { ...node.value, [box.dataset.key]: n };
    box.querySelector("output").textContent = n === max ? `${max}+` : n;
    notify(node);
  });
  return node;
}

// Wrapped in a div: a <button>'s own .value is a string and would turn the count into "01".
export function button(text, classes = "") {
  const node = el(`<div><button type="button" class="govuk-button ${classes}">${text}</button></div>`);
  node.value = 0;
  node.addEventListener("click", () => { node.value += 1; notify(node); });
  return node;
}

// A slider with its current value printed beside it; value is a number.
export function range(label, { min, max, step, value, format = String }) {
  const id = `q${++uid}`;
  const node = el(`
    <div class="govuk-form-group range">
      <label class="govuk-label govuk-label--s" for="${id}">${label}</label>
      <div class="range__row">
        <input class="range__input" id="${id}" type="range" min="${min}" max="${max}" step="${step}" value="${value}">
        <output class="range__value" for="${id}">${format(value)}</output>
      </div>
    </div>`);
  node.value = value;
  node.addEventListener("input", (e) => {
    node.value = Number(e.target.value);
    node.querySelector("output").textContent = format(node.value);
  });
  return node;
}
