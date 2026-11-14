import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { PRESETS, kelvinToRGB } from './presets.js';

const UP = new THREE.Vector3(0, 1, 0);
const BASE = 3; // ratio 1 -> 3 lux at the subject (same scale as a 3-strength sun)

export class Studio {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.AgXToneMapping;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap; // radius-based soft shadows, no VSM light bleeding
    RectAreaLightUniformsLib.init();

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.envMap = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environment = this.envMap;

    this.hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0);
    this.scene.add(this.hemi);

    this.rig = new THREE.Group();   // preset lights
    this.extras = new THREE.Group(); // glow cards, lamp props, beams
    this.scene.add(this.rig, this.extras);

    this.model = null;
    this.center = new THREE.Vector3();
    this.size = 1;
    this.lights = [];               // [{spec, light, dir (world unit), dist, on}]
    this.exposure = 0;
    this.worldExposure = 0;
    this.listeners = new Set();
    this.timer = new THREE.Timer();
    this.showStudio = true;

    this._makeStudio();
    this._resize();
    new ResizeObserver(() => this._resize()).observe(canvas);
    this.controls.addEventListener('change', () => this.emit('view'));
    this.renderer.setAnimationLoop(() => this._tick());
  }

  on(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  emit(type) { for (const fn of this.listeners) fn(type); }

  // ---------- model ----------
  async loadURL(url) {
    const gltf = await new GLTFLoader().loadAsync(url);
    this.setModel(gltf.scene);
  }

  async loadFile(file) {
    const url = URL.createObjectURL(file);
    try { await this.loadURL(url); } finally { URL.revokeObjectURL(url); }
  }

  setModel(obj) {
    if (this.model) this.scene.remove(this.model);
    this.model = obj;
    obj.traverse((o) => {
      if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
      if (o.isLight) o.visible = false; // the studio owns the lighting
    });
    this.scene.add(obj);
    const box = new THREE.Box3().setFromObject(obj);
    // stand the model on the floor (y = 0)
    obj.position.y -= box.min.y;
    box.setFromObject(obj);
    box.getCenter(this.center);
    this.size = Math.max(box.getSize(new THREE.Vector3()).length(), 0.01);
    this._fitStudio();
    this.frame();
    if (this.currentPreset) this.applyPreset(this.currentPreset);
    this.emit('model');
  }

  frame() {
    const d = (this.size * 0.85) / Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2));
    this.camera.position.copy(this.center).add(new THREE.Vector3(0, this.size * 0.12, d));
    this.camera.near = this.size / 100;
    this.camera.far = this.size * 200;
    this.camera.updateProjectionMatrix();
    this.controls.target.copy(this.center);
    this.controls.update();
  }

  _makeStudio() {
    const mat = new THREE.MeshStandardMaterial({ color: 0x5a5a5a, roughness: 0.9, side: THREE.DoubleSide });
    // seamless cyclorama: floor that curves up into a back wall
    const shape = new THREE.Shape();
    const R = 0.3, depth = 1.0, h = 1.0;
    shape.moveTo(-depth, 0);
    shape.lineTo(depth - R, 0);
    shape.absarc(depth - R, R, R, -Math.PI / 2, 0, false);
    shape.lineTo(depth, h);
    const pts = shape.getPoints(24);
    const prof = pts.map((p) => new THREE.Vector2(p.x, p.y));
    const cyc = new THREE.BufferGeometry();
    const W = 2.5, verts = [], idx = [];
    prof.forEach((p) => { verts.push(-W, p.y, -p.x, W, p.y, -p.x); });
    for (let i = 0; i < prof.length - 1; i++) {
      const a = i * 2;
      idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
    }
    cyc.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
    cyc.setIndex(idx);
    cyc.computeVertexNormals();
    this.cyc = new THREE.Mesh(cyc, mat);
    this.cyc.receiveShadow = true;
    this.scene.add(this.cyc);
  }

  _fitStudio() {
    const s = this.size * 3;
    this.cyc.scale.set(s, s, s);
    this.cyc.position.set(this.center.x, 0, this.center.z - 0);
  }

  setStudioVisible(v) { this.showStudio = v; this.cyc.visible = v; }

  // ---------- coordinates ----------
  camBasis() {
    const f = this.camera.position.clone().sub(this.center); f.y = 0;
    if (f.lengthSq() < 1e-9) f.set(0, 0, 1);
    f.normalize();
    const right = f.clone().negate().cross(UP).normalize();
    return { f, right };
  }

  dirFromAzEl(az, el, basis = this.camBasis()) {
    const a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el);
    const h = basis.f.clone().multiplyScalar(Math.cos(a)).addScaledVector(basis.right, Math.sin(a));
    return h.multiplyScalar(Math.cos(e)).addScaledVector(UP, Math.sin(e)).normalize();
  }

  // camera-space (x right, y up, z toward viewer) <-> world, used by the light ball
  toView(dir) { return dir.clone().applyQuaternion(this.camera.quaternion.clone().invert()); }
  fromView(v) { return v.clone().applyQuaternion(this.camera.quaternion).normalize(); }

  // ---------- presets ----------
  applyPreset(id) {
    const p = PRESETS[id];
    if (!p) return;
    this.currentPreset = id;
    this.clearLights();
    const basis = this.camBasis();
    for (const spec of p.lights) this.addLight(spec, basis);
    this.setWorld(p.world || {});
    this._extras(p.extras || {});
    this.emit('lights');
  }

  clearLights() {
    for (const l of this.lights) { this.rig.remove(l.light); if (l.light.target) this.rig.remove(l.light.target); l.light.dispose?.(); }
    this.lights = [];
    this.extras.clear();
    this.scene.fog = null;
  }

  addLight(spec, basis = this.camBasis()) {
    const s = { ...spec };
    const dir = this.dirFromAzEl(s.az, s.el, basis);
    const entry = { spec: s, dir, dist: s.dist, ratio: s.ratio, softness: Array.isArray(s.size) ? s.size[0] : s.size, kelvin: s.color ? null : s.kelvin, color: s.color || null, on: true, light: null };
    entry.light = this._makeLight(entry);
    this.rig.add(entry.light);
    if (entry.light.target) this.rig.add(entry.light.target);
    this.lights.push(entry);
    this.updateLight(entry);
    return entry;
  }

  _makeLight(e) {
    const s = e.spec;
    let l;
    if (s.kind === 'sun') {
      l = new THREE.DirectionalLight();
    } else if (s.kind === 'point') {
      l = new THREE.PointLight();
      l.decay = 2;
    } else if (s.kind === 'rect') {
      l = new THREE.RectAreaLight();
    } else {
      l = new THREE.SpotLight();
      l.decay = 2;
      if (s.gobo) l.map = goboTexture(s.gobo);
    }
    if (l.shadow) {
      l.castShadow = true;
      l.shadow.mapSize.set(2048, 2048);
      l.shadow.bias = -0.0004;
      l.shadow.normalBias = 0.02;
      l.shadow.blurSamples = 16;
    }
    l.userData.entry = e;
    return l;
  }

  updateLight(e) {
    const l = e.light, s = e.spec, size = this.size;
    const d = e.dist * size;
    const pos = this.center.clone().addScaledVector(e.dir, d);
    l.visible = e.on;
    // color
    const rgb = e.color || kelvinToRGB(e.kelvin || 5600);
    l.color.setRGB(rgb[0], rgb[1], rgb[2], THREE.SRGBColorSpace);
    // softness -> shadow blur / penumbra / panel size
    const soft = e.softness;
    if (s.kind === 'sun') {
      l.position.copy(this.center).addScaledVector(e.dir, size * 3);
      l.target.position.copy(this.center);
      l.intensity = BASE * e.ratio;
      const cam = l.shadow.camera;
      cam.left = cam.bottom = -size * 1.5; cam.right = cam.top = size * 1.5;
      cam.near = size * 0.5; cam.far = size * 6;
      cam.updateProjectionMatrix();
      l.shadow.radius = 1 + soft * 2; // sun size is degrees
    } else if (s.kind === 'rect') {
      const [w, h] = Array.isArray(s.size) ? [soft, s.size[1] * (soft / s.size[0])] : [soft, soft];
      l.width = Math.max(w * size, 0.001); l.height = Math.max(h * size, 0.001);
      l.position.copy(pos);
      l.lookAt(this.center);
      // luminance so that irradiance at subject ~ BASE * ratio
      l.intensity = (BASE * e.ratio * d * d) / Math.max(l.width * l.height, 1e-4) / Math.PI * 1.0;
    } else {
      l.position.copy(pos);
      l.intensity = BASE * e.ratio * d * d; // candela = lux * d^2
      l.shadow.radius = 1 + soft * 6;
      l.shadow.camera.near = Math.max(d - size, size * 0.05);
      l.shadow.camera.far = d + size * 4;
      if (l.isSpotLight) {
        l.target.position.copy(this.center);
        const cover = Math.atan((size * 0.75) / d) * 2.2;
        l.angle = s.cone ? THREE.MathUtils.degToRad(s.cone) / 2 * 1.0 : Math.min(Math.max(cover, 0.25), 1.2);
        l.penumbra = s.cone ? 0.15 : Math.min(0.5 + soft * 0.4, 1);
      }
    }
    e.baseIntensity = l.intensity;
    if (e.beam) this._placeBeam(e);
  }

  setWorld(w) {
    const strength = w.strength ?? 0.05;
    const rgb = w.kelvin ? kelvinToRGB(w.kelvin) : (w.color || [1, 1, 1]);
    const c = new THREE.Color().setRGB(rgb[0], rgb[1], rgb[2], THREE.SRGBColorSpace);
    this.hemi.color.copy(c);
    this.hemi.groundColor.copy(c).multiplyScalar(0.3);
    this.hemi.intensity = strength * BASE * 0.45;
    this.scene.environmentIntensity = Math.min(strength, 1) * 0.7 + 0.02;
    const bg = c.clone().multiplyScalar(Math.min(strength * 0.6, 0.85));
    this.scene.background = bg;
    this.worldExposure = w.exposure || 0;
    this._applyExposure();
  }

  setExposure(ev) { this.exposure = ev; this._applyExposure(); }
  _applyExposure() { this.renderer.toneMappingExposure = Math.pow(2, this.exposure + this.worldExposure); }

  _extras(x) {
    if (x.backGlow) {
      const g = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 4, 4), toneMapped: true }));
      const { f } = this.camBasis();
      g.position.copy(this.center).addScaledVector(f, -this.size * 1.1);
      g.scale.set(this.size * 4, this.size * 3, 1);
      g.lookAt(this.center.clone().addScaledVector(f, 5));
      this.extras.add(g);
    }
    if (x.lampProp) {
      const e = this.lights.find((l) => l.spec.name === x.lampProp);
      if (e) {
        const bulb = new THREE.Mesh(new THREE.SphereGeometry(this.size * 0.035, 24, 12), new THREE.MeshBasicMaterial({ color: new THREE.Color(6, 4.2, 2.4) }));
        bulb.userData.follows = e;
        this.extras.add(bulb);
        e.prop = bulb;
        e.light.castShadow = true;
        this._syncProp(e);
      }
    }
    if (x.haze) {
      this.scene.fog = new THREE.FogExp2(0x000000, x.haze / this.size);
    }
    for (const e of this.lights) if (e.spec.fx?.beam) { e.beam = true; this._placeBeam(e); }
  }

  _syncProp(e) { if (e.prop) e.prop.position.copy(e.light.position); }

  _placeBeam(e) {
    if (!e.beamMesh) {
      const geo = new THREE.ConeGeometry(1, 1, 48, 1, true);
      geo.translate(0, -0.5, 0);
      geo.rotateX(-Math.PI / 2);
      // soft beam: fades toward the far end and toward its silhouette edges
      const mat = new THREE.ShaderMaterial({
        uniforms: { color: { value: new THREE.Color(1, 1, 1) }, opacity: { value: 0.09 } },
        vertexShader: `varying float vAlong; varying vec3 vN; varying vec3 vV;
          void main(){ vAlong = uv.y; vec4 mv = modelViewMatrix * vec4(position,1.0);
            vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`,
        fragmentShader: `uniform vec3 color; uniform float opacity; varying float vAlong; varying vec3 vN; varying vec3 vV;
          void main(){ float edge = pow(abs(dot(normalize(vN), normalize(vV))), 2.0);
            float along = pow(vAlong, 1.4); gl_FragColor = vec4(color, opacity * edge * along); }`,
        transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
      });
      e.beamMesh = new THREE.Mesh(geo, mat);
      this.extras.add(e.beamMesh);
    }
    const len = e.dist * this.size * 1.6;
    const r = Math.tan(e.light.angle || 0.3) * len;
    e.beamMesh.scale.set(r, r, len);
    e.beamMesh.position.copy(e.light.position);
    e.beamMesh.lookAt(this.center);
    e.beamMesh.material.uniforms.color.value.copy(e.light.color);
  }

  // ---------- light editing (used by the light ball and the list) ----------
  setLightDir(e, dir) { e.dir.copy(dir).normalize(); this.updateLight(e); this._syncProp(e); this.emit('edit'); }
  setLightParam(e, key, value) { e[key] = value; this.updateLight(e); this._syncProp(e); this.emit('edit'); }

  // ---------- loop ----------
  _tick() {
    this.timer.update();
    const t = this.timer.getElapsed();
    const frame = t * 24;
    for (const e of this.lights) {
      const fx = e.spec.fx;
      if (!fx || !e.on) continue;
      if (fx.flicker) {
        const sp = fx.speed || 1;
        e.light.intensity = e.baseIntensity * (1 + fx.flicker * (0.5 * Math.sin(frame * 1.7 * sp) + 0.3 * Math.sin(frame * 4.3 * sp + 1) + 0.2 * Math.sin(frame * 9.1 * sp + 2)));
      }
      if (fx.strobe) e.light.intensity = Math.cos((frame * 2 * Math.PI) / fx.strobe) > Math.cos(Math.PI / fx.strobe) ? e.baseIntensity : 0;
      if (fx.pass) {
        const u = ((frame % fx.pass) / fx.pass) * 2 - 1; // -1..1
        const { right } = this.camBasis();
        const base = this.center.clone().addScaledVector(e.dir, e.dist * this.size);
        e.light.position.copy(base).addScaledVector(right, u * 3 * this.size);
        e.light.target.position.copy(this.center).addScaledVector(right, u * 3 * this.size * 0.6);
      }
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  _resize() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  snapshot() { return this.canvas.toDataURL('image/png'); }
}

function goboTexture(kind) {
  const N = 512, c = document.createElement('canvas');
  c.width = c.height = N;
  const g = c.getContext('2d');
  g.fillStyle = '#fff'; g.fillRect(0, 0, N, N);
  g.fillStyle = '#000';
  if (kind === 'blinds') {
    const n = 14, pitch = N / n;
    for (let i = 0; i < n; i++) g.fillRect(0, i * pitch, N, pitch * 0.5);
  } else {
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < 260; i++) {
      g.beginPath();
      g.ellipse(rnd() * N, rnd() * N, 10 + rnd() * 30, 6 + rnd() * 18, rnd() * Math.PI, 0, Math.PI * 2);
      g.fill();
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
