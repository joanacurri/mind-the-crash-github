// A 10 × 10 unit grid: the first k dots in the accent, the rest in grey.
export function dots(k, { title }) {
  const r = 7, gap = 18;
  const circles = Array.from({ length: 100 }, (_, i) => {
    const cx = (i % 10) * gap + r + 1, cy = Math.floor(i / 10) * gap + r + 1;
    return `<circle cx="${cx}" cy="${cy}" r="${r}" class="${i < k ? "dot dot--on" : "dot"}"/>`;
  }).join("");
  const size = 9 * gap + 2 * r + 2;
  const box = document.createElement("div");
  box.innerHTML = `<svg class="dots" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}"
    role="img" aria-label="${title}"><title>${title}</title>${circles}</svg>`;
  const node = box.firstElementChild;
  node.remove();
  return node;
}
