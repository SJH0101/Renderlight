import * as THREE from 'three';
import { kelvinToRGB } from './presets.js';

// The light ball: a sphere seen from the current camera, shaded by the actual lights.
// Each light is a dot at its direction. Filled = in front of the subject, ring = behind.
// Drag a dot to move the light; dragging past the rim flips it to the other side.
export class LightBall {
  constructor(canvas, studio, { onSelect } = {}) {
    this.c = canvas;
    this.g = canvas.getContext('2d');
    this.studio = studio;
    this.onSelect = onSelect;
    this.selected = null;
    this.drag = null;
    this.size = canvas.width;
    this.R = this.size * 0.42;
    this.img = this.g.createImageData(this.size, this.size);
    canvas.addEventListener('pointerdown', (ev) => this._down(ev));
    canvas.addEventListener('pointermove', (ev) => this._move(ev));
    window.addEventListener('pointerup', () => this._up());
    canvas.addEventListener('dblclick', (ev) => this._flip(ev));
    studio.on(() => this.draw());
    this.draw();
  }

  select(e) { this.selected = e; this.draw(); }

  _xy(ev) {
    const r = this.c.getBoundingClientRect();
    const k = this.size / r.width;
    const x = ((ev.clientX - r.left) * k - this.size / 2) / this.R;
    const y = -((ev.clientY - r.top) * k - this.size / 2) / this.R;
    return { x, y };
  }

  _dots() {
    return this.studio.lights.map((e) => ({ e, v: this.studio.toView(e.dir) }));
  }

  _down(ev) {
    const p = this._xy(ev);
    let best = null, bd = 0.18;
    for (const { e, v } of this._dots()) {
      const d = Math.hypot(v.x - p.x, v.y - p.y);
      if (d < bd) { bd = d; best = { e, v }; }
    }
    if (best) {
      this.drag = { e: best.e, front: best.v.z >= 0 };
      this.selected = best.e;
      this.onSelect?.(best.e);
    } else if (this.selected && Math.hypot(p.x, p.y) <= 1.15) {
      // click empty spot: move the selected light there
      this.drag = { e: this.selected, front: this.studio.toView(this.selected.dir).z >= 0 };
      this._apply(p);
    }
    this.c.setPointerCapture?.(ev.pointerId);
    this.draw();
  }

  _move(ev) {
    const p = this._xy(ev);
    if (!this.drag) {
      const over = this._dots().some(({ v }) => Math.hypot(v.x - p.x, v.y - p.y) < 0.18);
      this.c.style.cursor = over ? 'grab' : this.selected ? 'crosshair' : 'default';
      return;
    }
    this.c.style.cursor = 'grabbing';
    this._apply(p);
  }

  _apply(p) {
    let { x, y } = p;
    let r = Math.hypot(x, y);
    const d = this.drag;
    if (r > 1) {
      // past the rim: continue around the back of the ball
      const rr = Math.min(r, 1.98);
      const k = (2 - rr) / r;
      x *= k; y *= k;
      if (!d.flipped) { d.front = !d.front; d.flipped = true; }
      r = Math.hypot(x, y);
    } else if (d.flipped && r < 0.97) {
      d.flipped = false;
    }
    const z = Math.sqrt(Math.max(0, 1 - Math.min(r, 1) ** 2)) * (d.front ? 1 : -1);
    this.studio.setLightDir(d.e, this.studio.fromView(new THREE.Vector3(x, y, z)));
  }

  _up() { this.drag = null; this.c.style.cursor = 'default'; }

  _flip(ev) {
    // double-click a dot: send that light to the other side (front <-> back)
    const p = this._xy(ev);
    for (const { e, v } of this._dots()) {
      if (Math.hypot(v.x - p.x, v.y - p.y) < 0.18) {
        this.studio.setLightDir(e, this.studio.fromView(new THREE.Vector3(v.x, v.y, -v.z)));
        return;
      }
    }
  }

  draw() {
    const { size, R, img } = this;
    const lights = this._dots().filter(({ e }) => e.on).map(({ e, v }) => {
      const rgb = e.color || kelvinToRGB(e.kelvin || 5600);
      return { v, rgb: rgb.map((c) => c * c), w: e.ratio, sharp: 1 / (0.15 + e.softness) };
    });
    const maxW = Math.max(0.0001, ...lights.map((l) => l.w));
    const ambient = Math.min(this.studio.hemi.intensity / 3, 0.6) * 0.5;
    const data = img.data;
    const half = size / 2;
    for (let py = 0; py < size; py++) {
      for (let px = 0; px < size; px++) {
        const i = (py * size + px) * 4;
        const x = (px - half) / R, y = -(py - half) / R;
        const r2 = x * x + y * y;
        if (r2 > 1) { data[i + 3] = 0; continue; }
        const z = Math.sqrt(1 - r2);
        let cr = ambient, cg = ambient, cb = ambient;
        for (const l of lights) {
          const ndl = x * l.v.x + y * l.v.y + z * l.v.z;
          const wrap = Math.max(0, (ndl + 0.1) / 1.1);
          // half vector with the viewer (0,0,1) for a highlight
          let hx = l.v.x, hy = l.v.y, hz = l.v.z + 1;
          const hl = Math.hypot(hx, hy, hz) || 1;
          const ndh = Math.max(0, (x * hx + y * hy + z * hz) / hl);
          const spec = Math.pow(ndh, 12 + l.sharp * 20) * 0.6;
          const k = (l.w / maxW) * 0.9;
          cr += (wrap * k + spec * k) * l.rgb[0];
          cg += (wrap * k + spec * k) * l.rgb[1];
          cb += (wrap * k + spec * k) * l.rgb[2];
        }
        data[i] = 255 * Math.pow(cr / (1 + cr) * 1.4, 1 / 2.2);
        data[i + 1] = 255 * Math.pow(cg / (1 + cg) * 1.4, 1 / 2.2);
        data[i + 2] = 255 * Math.pow(cb / (1 + cb) * 1.4, 1 / 2.2);
        data[i + 3] = 255;
      }
    }
    const g = this.g;
    g.clearRect(0, 0, size, size);
    g.putImageData(img, 0, 0);
    // rim
    g.strokeStyle = 'rgba(255,255,255,0.25)';
    g.lineWidth = 1.5;
    g.beginPath(); g.arc(half, half, R, 0, Math.PI * 2); g.stroke();
    // dots
    for (const { e, v } of this._dots()) {
      const x = half + v.x * R, y = half - v.y * R;
      const rgb = (e.color || kelvinToRGB(e.kelvin || 5600)).map((c) => Math.round(c * 255));
      const sel = e === this.selected;
      g.beginPath();
      g.arc(x, y, sel ? 9 : 7, 0, Math.PI * 2);
      if (v.z >= 0) {
        g.fillStyle = e.on ? `rgb(${rgb})` : '#555';
        g.fill();
        g.strokeStyle = sel ? '#fff' : 'rgba(0,0,0,0.7)';
        g.lineWidth = sel ? 3 : 1.5;
        g.stroke();
      } else {
        g.strokeStyle = e.on ? `rgb(${rgb})` : '#555';
        g.lineWidth = sel ? 3.5 : 2.5;
        g.setLineDash([3, 3]);
        g.stroke();
        g.setLineDash([]);
      }
    }
  }
}
