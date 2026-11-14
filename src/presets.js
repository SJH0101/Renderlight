// 34 named lighting presets. Same coordinate system as the Blender skill:
//   az   0 = camera side, +90 = camera right, 180 = behind subject (degrees)
//   el   elevation from subject center (degrees)
//   dist multiple of subject bounding-box diagonal
//   size softness: multiple of subject diagonal (sun: degrees)
//   ratio brightness relative to key (1 = key)
// kinds: spot (default, casts shadows), sun, point, rect (soft panel, no shadows)

const L = (name, o) => ({ name, kind: 'spot', az: 45, el: 30, dist: 1.5, ratio: 1, kelvin: 5600, size: 0.5, ...o });

export const PRESETS = {
  high_key: { n: 1, ko: '하이키', lights: [L('Key', { az: 20, el: 25, size: 1.0 }), L('Fill', { az: -40, el: 10, ratio: 0.7, size: 1.2 })], world: { strength: 1.0, color: [1, 1, 1], exposure: 0.5 } },
  low_key: { n: 2, ko: '로우키', lights: [L('Key', { az: 50, el: 35, size: 0.4, kelvin: 4500 }), L('Rim', { az: 150, el: 25, ratio: 0.6, size: 0.3 })], world: { strength: 0.002 } },
  rembrandt: { n: 3, ko: '렘브란트', lights: [L('Key', { az: 45, el: 40 }), L('Fill', { az: -45, el: 10, ratio: 0.15, size: 1.0 })], world: { strength: 0.02 } },
  butterfly: { n: 4, ko: '버터플라이', lights: [L('Key', { az: 0, el: 50, dist: 1.3 }), L('Reflector', { az: 0, el: -25, dist: 1.0, ratio: 0.25, size: 0.8 })], world: { strength: 0.02 } },
  split: { n: 5, ko: '스플릿', lights: [L('Key', { az: 90, el: 5, dist: 1.3, size: 0.4 })], world: { strength: 0.005 } },
  loop: { n: 6, ko: '루프', lights: [L('Key', { az: 35, el: 30 }), L('Fill', { az: -40, el: 5, ratio: 0.25, size: 1.0 })], world: { strength: 0.02 } },
  broad: { n: 7, ko: '브로드', lights: [L('Key', { az: -45, el: 30 }), L('Fill', { az: 45, el: 10, ratio: 0.2, size: 1.0 })], world: { strength: 0.02 } },
  short: { n: 8, ko: '숏', lights: [L('Key', { az: 45, el: 30 }), L('Fill', { az: -45, el: 10, ratio: 0.15, size: 1.0 })], world: { strength: 0.02 } },
  chiaroscuro: { n: 9, ko: '키아로스쿠로', lights: [L('Key', { az: 70, el: 25, dist: 2, ratio: 1.5, size: 0.1, cone: 35, kelvin: 3800 })], world: { strength: 0 } },
  silhouette: { n: 10, ko: '실루엣', lights: [], world: { strength: 0 }, extras: { backGlow: true } },
  rim: { n: 11, ko: '림 라이트', lights: [L('RimR', { az: 140, el: 25, dist: 1.2, ratio: 1.2, size: 0.3 }), L('RimL', { az: -140, el: 25, dist: 1.2, ratio: 1.2, size: 0.3 })], world: { strength: 0.01 } },
  hard: { n: 12, ko: '하드 라이트', lights: [L('Key', { az: 40, el: 35, dist: 2.5, size: 0.03 })], world: { strength: 0.02 } },
  soft: { n: 13, ko: '소프트 라이트', lights: [L('Key', { az: 40, el: 30, dist: 1.0, size: 1.5 }), L('Fill', { az: -50, el: 10, dist: 1.0, ratio: 0.4, size: 1.5 })], world: { strength: 0.05 } },
  bounce: { n: 14, ko: '바운스', lights: [L('Bounce', { kind: 'rect', az: -60, el: 20, dist: 1.2, ratio: 0.9, size: 1.2 }), L('Key', { az: 60, el: 60, ratio: 0.3, size: 0.8 })], world: { strength: 0.02 } },
  top: { n: 15, ko: '탑 라이트', lights: [L('Key', { az: 0, el: 85, dist: 1.2, ratio: 1.2 })], world: { strength: 0.005 } },
  under: { n: 16, ko: '언더 라이트', lights: [L('Key', { az: 0, el: -45, dist: 1.0, size: 0.3 })], world: { strength: 0.005 } },
  golden_hour: { n: 17, ko: '골든 아워', lights: [L('Sun', { kind: 'sun', az: 60, el: 6, ratio: 1.2, size: 2, kelvin: 3000 })], world: { strength: 0.3, kelvin: 4500 } },
  blue_hour: { n: 18, ko: '블루 아워', lights: [L('Fill', { kind: 'rect', az: 0, el: 30, ratio: 0.3, size: 2.0, kelvin: 10000 })], world: { strength: 0.5, kelvin: 12000, exposure: -0.5 } },
  day_for_night: { n: 19, ko: '데이 포 나이트', lights: [L('Sun', { kind: 'sun', az: 60, el: 35, ratio: 1.0, size: 0.5, kelvin: 9000 })], world: { strength: 0.1, kelvin: 12000, exposure: -0.8 } },
  moonlight: { n: 20, ko: '문라이트', lights: [L('Moon', { kind: 'sun', az: 100, el: 40, ratio: 1.0, size: 0.5, kelvin: 7500 })], world: { strength: 0.15, color: [0.02, 0.03, 0.08] } },
  window: { n: 21, ko: '윈도우 라이트', lights: [L('Window', { kind: 'rect', az: 80, el: 20, ratio: 1.2, size: [1.2, 1.6], kelvin: 6000 }), L('Fill', { az: -60, el: 10, ratio: 0.15, size: 1.0 })], world: { strength: 0.05 } },
  practical: { n: 22, ko: '프랙티컬', lights: [L('Lamp', { kind: 'point', az: 70, el: 25, dist: 0.9, ratio: 0.8, size: 0.05, kelvin: 2700 })], world: { strength: 0.01 }, extras: { lampProp: 'Lamp' } },
  firelight: { n: 23, ko: '파이어라이트', lights: [L('Fire', { kind: 'point', az: 30, el: -20, dist: 1.0, size: 0.15, kelvin: 1900, fx: { flicker: 0.35 } })], world: { strength: 0.003 } },
  venetian_blinds: { n: 24, ko: '베니션 블라인드', lights: [L('Sun', { az: 70, el: 25, dist: 4, ratio: 1.5, size: 0.02, kelvin: 5000, gobo: 'blinds' })], world: { strength: 0.03 } },
  dappled: { n: 25, ko: '대플드', lights: [L('Sun', { az: 40, el: 55, dist: 4, ratio: 1.5, size: 0.03, kelvin: 5200, gobo: 'dapple' })], world: { strength: 0.1, kelvin: 6500 } },
  volumetric: { n: 26, ko: '볼류메트릭', lights: [L('Back', { az: 160, el: 40, ratio: 3, size: 0.05, cone: 30, fx: { beam: true } })], world: { strength: 0 }, extras: { haze: 0.05 } },
  flat: { n: 27, ko: '플랫 라이트', lights: [L('Key', { az: 0, el: 10, dist: 1.2, size: 2.0 }), L('FillR', { az: 60, el: 10, dist: 1.2, ratio: 0.8, size: 2.0 }), L('FillL', { az: -60, el: 10, dist: 1.2, ratio: 0.8, size: 2.0 })], world: { strength: 0.5, color: [0.5, 0.5, 0.5] } },
  neon: { n: 28, ko: '네온', lights: [L('NeonPink', { kind: 'rect', az: 70, el: 10, ratio: 2, size: [0.05, 1.0], color: [1, 0.05, 0.6] }), L('NeonCyan', { kind: 'rect', az: -70, el: 10, ratio: 2, size: [0.05, 1.0], color: [0, 0.8, 1] })], world: { strength: 0.01, color: [0.02, 0.02, 0.08] } },
  teal_orange: { n: 29, ko: '틸 앤 오렌지', lights: [L('Key', { az: 40, el: 25, kelvin: 3000 }), L('Teal', { az: -120, el: 20, ratio: 0.6, color: [0, 0.5, 0.55] })], world: { strength: 0.5, color: [0, 0.08, 0.1] } },
  mono_red: { n: 30, ko: '모노크롬 레드', lights: [L('Key', { az: 45, el: 30, ratio: 1.2, color: [1, 0.02, 0.02] })], world: { strength: 0.3, color: [0.05, 0, 0] } },
  screen_glow: { n: 31, ko: '스크린 글로우', lights: [L('Screen', { kind: 'rect', az: 0, el: -10, dist: 0.5, ratio: 0.6, size: [0.4, 0.25], color: [0.6, 0.75, 1], fx: { flicker: 0.08, speed: 0.5 } })], world: { strength: 0.003 } },
  passing: { n: 32, ko: '패싱 라이트', lights: [L('Pass', { az: 60, el: 15, dist: 2, ratio: 2, size: 0.05, cone: 25, kelvin: 4000, fx: { pass: 48 } })], world: { strength: 0.01 } },
  strobe: { n: 33, ko: '스트로브', lights: [L('Strobe', { az: 30, el: 20, ratio: 3, kelvin: 6500, fx: { strobe: 6 } })], world: { strength: 0 } },
  theatrical: { n: 34, ko: '시어트리컬 라이트', lights: [L('Spot', { az: 15, el: 55, dist: 2.5, ratio: 3, size: 0.05, cone: 22, kelvin: 3200 })], world: { strength: 0 } },
};

export const GROUPS = [
  { id: 'portrait', ko: '인물 정석', ids: ['rembrandt', 'loop', 'butterfly', 'split', 'broad', 'short', 'soft', 'hard', 'flat', 'bounce'] },
  { id: 'natural', ko: '자연광·시간대', ids: ['golden_hour', 'window', 'blue_hour', 'moonlight', 'day_for_night', 'dappled', 'firelight'] },
  { id: 'mood', ko: '무드·대비', ids: ['low_key', 'chiaroscuro', 'high_key', 'silhouette', 'rim', 'top', 'under', 'theatrical'] },
  { id: 'color_fx', ko: '컬러·효과', ids: ['neon', 'teal_orange', 'venetian_blinds', 'volumetric', 'mono_red', 'screen_glow', 'practical', 'passing', 'strobe'] },
];

export const INFO = {
  high_key: '밝고 그림자 거의 없음, 깨끗한 광고 느낌',
  low_key: '대부분 어둡고 한쪽만 빛, 진지한 분위기',
  rembrandt: '그늘진 뺨에 빛 삼각형, 고전 초상화',
  butterfly: '정면 위에서, 코 밑 나비 그림자, 뷰티샷',
  split: '얼굴 절반만 빛, 강렬·이중성',
  loop: '가장 무난한 인물 조명, 자연스러운 입체감',
  broad: '카메라 쪽 넓은 면을 밝힘, 얼굴이 넓어 보임',
  short: '안쪽 좁은 면을 밝힘, 얼굴이 갸름해 보임',
  chiaroscuro: '극단적 명암, 카라바조 그림 같은',
  silhouette: '밝은 배경에 피사체는 검은 실루엣',
  rim: '윤곽선만 빛나게, 배경과 분리',
  hard: '칼같이 선명한 그림자, 한낮·강렬',
  soft: '부드럽게 번지는 그림자, 편안함',
  bounce: '벽·반사판에 튕긴 은은한 빛',
  top: '머리 위에서, 눈이 그늘져 미스터리',
  under: '아래에서, 공포·괴담 느낌',
  golden_hour: '해질녘 낮고 따뜻한 빛, 감성',
  blue_hour: '해 진 직후 푸르고 고요함',
  day_for_night: '선명한 그림자인데 푸르고 어두운 밤',
  moonlight: '차가운 달빛, 어두운 밤 장면',
  window: '창가의 큰 부드러운 옆빛, 일상·감성',
  practical: '화면 속 전구가 실제 광원',
  firelight: '모닥불·촛불, 따뜻하게 일렁임',
  venetian_blinds: '블라인드 줄무늬 그림자, 누아르',
  dappled: '나뭇잎 사이로 얼룩진 햇빛',
  volumetric: '안개 속 빛줄기, 신비·영화적',
  flat: '그림자 없이 균일, 증명사진·제품',
  neon: '핑크·시안 네온, 사이버펑크',
  teal_orange: '따뜻한 피부 vs 청록 그림자, 할리우드',
  mono_red: '전부 빨간빛, 긴장·위험',
  screen_glow: '모니터·폰 화면 불빛, 밤샘 작업',
  passing: '빛이 지나가며 훑음, 차 안·밤길',
  strobe: '번쩍번쩍 점멸, 클럽·긴박함',
  theatrical: '무대 스포트라이트, 바닥에 원형 빛',
};

export const LIGHT_LABELS = {
  Key: '키', Fill: '필', Rim: '림', RimR: '림 (오른쪽)', RimL: '림 (왼쪽)', Reflector: '반사판',
  Bounce: '반사광', Sun: '해', Moon: '달', Window: '창문', Lamp: '전구', Fire: '불빛',
  Back: '역광', FillR: '필 (오른쪽)', FillL: '필 (왼쪽)', NeonPink: '네온 핑크', NeonCyan: '네온 시안',
  Teal: '청록', Screen: '화면', Pass: '지나가는 빛', Strobe: '스트로브', Spot: '스포트라이트',
};

export function kelvinToRGB(k) {
  const t = k / 100;
  const r = t <= 66 ? 255 : 329.698727446 * Math.pow(t - 60, -0.1332047592);
  const g = t <= 66 ? 99.4708025861 * Math.log(t) - 161.1195681661 : 288.1221695283 * Math.pow(t - 60, -0.0755148492);
  const b = t >= 66 ? 255 : t <= 19 ? 0 : 138.5177312231 * Math.log(t - 10) - 305.0447927307;
  return [r, g, b].map((x) => Math.min(Math.max(x, 0), 255) / 255); // sRGB
}
