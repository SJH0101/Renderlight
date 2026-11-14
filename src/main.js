import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css';
import './style.css';
import { Studio } from './studio.js';
import { LightBall } from './ball.js';
import { PRESETS, GROUPS, INFO, LIGHT_LABELS, kelvinToRGB } from './presets.js';

const $ = (s) => document.querySelector(s);
const studio = new Studio($('#view'));
const ball = new LightBall($('#ball'), studio, { onSelect: (e) => renderLights(e) });
window.studio = studio; // handy for debugging and tests

// ---------- presets: one quiet grouped list ----------
function renderPresets() {
  $('#presets').innerHTML = GROUPS.map((g) => `
    <div class="group">${g.ko}</div>
    ${g.ids.map((id) => `
      <button class="preset" data-id="${id}" aria-pressed="${studio.currentPreset === id}">
        ${PRESETS[id].ko}<span class="desc">${INFO[id]}</span>
      </button>`).join('')}`).join('');
}
$('#presets').addEventListener('click', (ev) => {
  const b = ev.target.closest('.preset');
  if (b) studio.applyPreset(b.dataset.id);
});

// ---------- lights: compact rows, the selected one opens its controls ----------
const warmth = (k) => 1 - (Math.log(k) - Math.log(1800)) / (Math.log(12000) - Math.log(1800)); // 1 = warm
const kelvin = (w) => Math.exp(Math.log(1800) + (1 - w) * (Math.log(12000) - Math.log(1800)));
const swatch = (e) => `rgb(${(e.color || kelvinToRGB(e.kelvin || 5600)).map((c) => Math.round(c * 255))})`;

function field(label, key, min, max, step, value, lo = '', hi = '', cls = '') {
  return `<label class="field"><span class="field-top">${label}${lo ? `<em>${lo} ↔ ${hi}</em>` : ''}</span>
    <input type="range" class="${cls}" data-k="${key}" min="${min}" max="${max}" step="${step}" value="${value}"></label>`;
}

function renderLights(selected = ball.selected) {
  if (selected) ball.select(selected);
  const box = $('#lights');
  if (!studio.lights.length) {
    box.innerHTML = '<p class="empty">이 조명은 따로 움직일 라이트 없이 밝은 배경으로만 만들어요.</p>';
    return;
  }
  box.innerHTML = studio.lights.map((e, i) => {
    const label = LIGHT_LABELS[e.spec.name] || e.spec.name;
    const cls = ['light', e === ball.selected ? 'sel' : '', e.on ? '' : 'off'].join(' ');
    return `<div class="${cls}" data-i="${i}">
      <div class="light-head">
        <span class="swatch" style="background:${swatch(e)}"></span>
        <span class="light-name">${label}</span>
        <button class="eye" aria-pressed="${e.on}">${e.on ? '켜짐' : '꺼짐'}</button>
      </div>
      <div class="light-body">
        ${field('밝기', 'ratio', 0, 4, 0.01, e.ratio)}
        ${field('그림자', 'softness', 0.01, 2, 0.01, e.softness, '선명하게', '부드럽게')}
        ${field('거리', 'dist', 0.4, 4, 0.01, e.dist, '가까이', '멀리')}
        ${e.kelvin ? field('색온도', 'warmth', 0, 1, 0.005, warmth(e.kelvin), '차갑게', '따뜻하게', 'warmth') : ''}
      </div>
    </div>`;
  }).join('');
}

$('#lights').addEventListener('input', (ev) => {
  const el = ev.target, row = el.closest('.light'); if (!row) return;
  const e = studio.lights[+row.dataset.i], k = el.dataset.k;
  if (k === 'warmth') {
    studio.setLightParam(e, 'kelvin', kelvin(+el.value));
    row.querySelector('.swatch').style.background = swatch(e);
  } else studio.setLightParam(e, k, +el.value);
});
$('#lights').addEventListener('click', (ev) => {
  const row = ev.target.closest('.light'); if (!row) return;
  const e = studio.lights[+row.dataset.i];
  if (ev.target.closest('.eye')) { studio.setLightParam(e, 'on', !e.on); renderLights(); return; }
  if (ev.target.closest('.light-head') && ball.selected !== e) renderLights(e);
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

// keep the UI in sync however a preset gets applied (list, console, tests)
studio.on((type) => {
  if (type !== 'lights') return;
  ball.select(studio.lights[0] || null);
  renderPresets();
  renderLights(studio.lights[0]);
});

renderPresets();
studio.loadURL('./sample.glb').then(() => studio.applyPreset('rembrandt'));
