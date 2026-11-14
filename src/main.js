import { Studio } from './studio.js';
import { LightBall } from './ball.js';
import { PRESETS, GROUPS, INFO, LIGHT_LABELS } from './presets.js';

const $ = (s) => document.querySelector(s);
const studio = new Studio($('#view'));
const ball = new LightBall($('#ball'), studio, { onSelect: (e) => renderLights(e) });
window.studio = studio; // handy for debugging and tests

// ---------- presets ----------
let group = GROUPS[0].id;
function renderTabs() {
  $('#tabs').innerHTML = GROUPS.map((g) => `<button data-g="${g.id}" class="${g.id === group ? 'on' : ''}">${g.ko}</button>`).join('');
}
function renderPresets() {
  const g = GROUPS.find((x) => x.id === group);
  $('#presets').innerHTML = g.ids.map((id) => {
    const p = PRESETS[id];
    return `<button class="preset ${studio.currentPreset === id ? 'on' : ''}" data-id="${id}">
      <span class="num">${String(p.n).padStart(2, '0')}</span>
      <span class="name">${p.ko}</span>
      <span class="desc">${INFO[id]}</span></button>`;
  }).join('');
}
$('#tabs').addEventListener('click', (ev) => {
  const b = ev.target.closest('button'); if (!b) return;
  group = b.dataset.g; renderTabs(); renderPresets();
});
$('#presets').addEventListener('click', (ev) => {
  const b = ev.target.closest('.preset'); if (!b) return;
  studio.applyPreset(b.dataset.id);
});

function hint(p) {
  const fx = p.lights.some((l) => l.fx) ? ' · 움직이는 조명' : '';
  $('#hint').textContent = `${p.ko}${fx}`;
}

// ---------- light list (plain-word sliders, no angles) ----------
const warmth = (k) => 1 - (Math.log(k) - Math.log(1800)) / (Math.log(12000) - Math.log(1800)); // 1 = warm
const kelvin = (w) => Math.exp(Math.log(1800) + (1 - w) * (Math.log(12000) - Math.log(1800)));

function renderLights(selected = ball.selected) {
  if (selected) ball.select(selected);
  const box = $('#lights');
  if (!studio.lights.length) { box.innerHTML = '<div class="empty">이 프리셋은 라이트 대신 배경 빛을 써요</div>'; return; }
  box.innerHTML = studio.lights.map((e, i) => {
    const label = LIGHT_LABELS[e.spec.name] || e.spec.name;
    const sel = e === ball.selected ? 'sel' : '';
    return `<div class="light ${sel}" data-i="${i}">
      <div class="row head"><label><input type="checkbox" data-k="on" ${e.on ? 'checked' : ''}/> ${label}</label></div>
      <div class="row"><span>밝기</span><input type="range" data-k="ratio" min="0" max="4" step="0.01" value="${e.ratio}"></div>
      <div class="row"><span>부드러움</span><input type="range" data-k="softness" min="0.01" max="2" step="0.01" value="${e.softness}"></div>
      <div class="row"><span>거리</span><input type="range" data-k="dist" min="0.4" max="4" step="0.01" value="${e.dist}"></div>
      ${e.kelvin ? `<div class="row"><span>따뜻함</span><input type="range" data-k="warmth" min="0" max="1" step="0.005" value="${warmth(e.kelvin)}"></div>` : ''}
    </div>`;
  }).join('');
}
$('#lights').addEventListener('input', (ev) => {
  const el = ev.target, card = el.closest('.light'); if (!card) return;
  const e = studio.lights[+card.dataset.i], k = el.dataset.k;
  if (k === 'on') studio.setLightParam(e, 'on', el.checked);
  else if (k === 'warmth') studio.setLightParam(e, 'kelvin', kelvin(+el.value));
  else studio.setLightParam(e, k, +el.value);
});
$('#lights').addEventListener('pointerdown', (ev) => {
  const card = ev.target.closest('.light'); if (!card) return;
  const e = studio.lights[+card.dataset.i];
  if (ball.selected !== e) {
    ball.select(e);
    document.querySelectorAll('.light').forEach((c) => c.classList.toggle('sel', c === card));
  }
});

// ---------- top bar ----------
$('#exposure').addEventListener('input', (ev) => studio.setExposure(+ev.target.value));
$('#studio').addEventListener('change', (ev) => studio.setStudioVisible(ev.target.checked));
$('#sample').addEventListener('click', () => studio.loadURL('./sample.glb'));
$('#file').addEventListener('change', (ev) => { const f = ev.target.files[0]; if (f) studio.loadFile(f); });
$('#shot').addEventListener('click', () => {
  const a = document.createElement('a');
  a.href = studio.snapshot();
  a.download = `renderlight-${studio.currentPreset || 'shot'}.png`;
  a.click();
});

// drag & drop
const view = $('.view');
['dragenter', 'dragover'].forEach((t) => view.addEventListener(t, (ev) => { ev.preventDefault(); view.classList.add('dragging'); }));
['dragleave', 'drop'].forEach((t) => view.addEventListener(t, (ev) => { ev.preventDefault(); view.classList.remove('dragging'); }));
view.addEventListener('drop', (ev) => {
  const f = [...ev.dataTransfer.files].find((x) => /\.(glb|gltf)$/i.test(x.name));
  if (f) studio.loadFile(f);
});

// keep the UI in sync however a preset gets applied (buttons, console, tests)
studio.on((type) => {
  if (type !== 'lights') return;
  const p = PRESETS[studio.currentPreset];
  if (!p) return;
  const g = GROUPS.find((x) => x.ids.includes(studio.currentPreset));
  if (g && g.id !== group) { group = g.id; renderTabs(); }
  ball.select(studio.lights[0] || null);
  renderPresets(); renderLights(studio.lights[0]); hint(p);
});

// ---------- start ----------
renderTabs();
renderPresets();
studio.loadURL('./sample.glb').then(() => studio.applyPreset('rembrandt'));
