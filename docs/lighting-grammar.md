# 조명 문법 (Lighting Grammar)

AI가 "고급스러운 향수 광고"나 "공포 영화 느낌" 같은 말을 조명 결정으로 바꿀 때 쓰는 규칙집. 규칙마다 출처와 근거 수준을 붙였다.

**근거 수준**
- **[실험]** 참가자를 모아 측정한 연구 결과. 표본 크기를 같이 적었다
- **[관습]** 실무자들이 쓰는 규칙을 논문이 인용·정리한 것
- **[계산]** 그래픽스 논문에서 이미지 품질 지표로 정의해 쓴 것
- **[해석]** 위 근거를 Renderlight 좌표계(az / el / ratio / softness)로 옮긴 우리 판단. 근거가 아니라 출발값이다

모든 출처는 무료로 전문을 볼 수 있다. 예외는 따로 표시했다.

---

## 1. 공통 규칙

### 1.1 키라이트 방향
- **45° 근처가 기준이다.** 45° 조명은 얼굴 전체를 드러내는 기준 조건이다. 실루엣 조명(뒤에서), 언더라이트(아래에서), 탑라이트(위에서)는 45° 조명보다 초기 후방 음전위(EPN)를 더 강하게 일으켰다. 즉 얼굴을 숨기거나 왜곡하는 조명은 감정 반응을 무의식 단계에서부터 바꾼다. **[실험, EEG 파일럿 n=9: 근거 약함]** (Huttunen 2025)
- **위에서 오는 빛이 기본값이다.** 자동 조명 설계에서 광원의 고도 목표를 45°로 두어 위쪽에서 비추도록 유도한다. **[계산]** (Shacked & Lischinski 2001)
- [해석] 기본 키는 `az ±30–50°, el 30–45°`. 공포·미스터리처럼 불편함이 목적일 때만 `el < 0`(언더)나 `el > 75°`(탑)를 쓴다.

### 1.2 그림자
- **그림자를 없애는 게 능사가 아니다.** 그림자가 있으면 표정의 진정성(genuineness) 평가가 올라갔고, 분노·슬픔은 더 강하게, 기쁨은 더 약하게 느껴졌다. **[실험, n 미기재]** (Zhan 2022)
- 키라이트 밝기와 그림자 강도는 캐릭터 감정의 강도와 호감도에 영향을 준다. 어두운 그림자는 기쁨의 강도를 낮췄다. **[실험]** (Wisessing et al. 2020, Zhan 2022에서 재인용)
- **제품 그림자는 고급감을 높인다.** 광고 속 제품에 그림자가 있으면 시각적 선명도가 올라가고, 그게 고급스럽다는 인식으로 이어졌다. **[실험, 3개 연구]** (Sharma 2016. ⚠️ 본문 유료, 초록 기준)
- [해석] 밝고 행복한 톤이 목적이면 `fill ratio 0.4–0.7`로 그림자를 연하게. 진지함·긴장·고급감이 목적이면 `fill ≤ 0.2`. 제품은 바닥 그림자를 지우지 않는다.

### 1.3 확산광 + 방향광
- **제품은 섞는 게 낫다.** 확산광만 / 방향광만 / 둘 다 / 둘 다 + 밝게, 네 조건을 비교한 결과, 지각된 품질은 둘을 섞었을 때 가장 높았다. **[실험, n=113]** (Bakker 2019)
- 광택 있는 물체를 반짝이게 하고 하이라이트와 그림자를 만들려면 방향광이 필요하다. 흔히 쓰는 라이트박스는 확산광만 만들어서 부족하다. **[실험 + 저자 권고]** (Bakker 2019)
- 제품 사진은 단단한 그림자를 부드럽게 하려고 필라이트를 쓰는 경우가 많다. **[관습]** (Usta et al. 2022)
- [해석] 제품 기본 = 크고 부드러운 소스 1개(`size ≥ 1.0`, 확산 역할) + 작고 선명한 소스 1개(`size ≤ 0.2`, 방향 역할).

### 1.4 하이키 / 로우키
- **로우키는 "무서움"이 아니라 "감정 강도"다.** 로우키 영상을 본 참가자는 미스터리, 서스펜스, 악의 같은 불안한 감정을 유의미하게 더 많이 보고했다. 그런데 예상과 달리 행복하고 긍정적인 감정도 더 강하게 느꼈다. **[실험, n=162]** (Poland 2015)
- [해석] 로우키는 공포만이 아니라 "깊이 있는 / 진지한 / 고급스러운" 요청에도 후보로 올린다. 하이키는 밝고 가벼운 요청의 기본값이지만, 근거는 아직 이론 예측 수준이다. Poland의 초록은 하이키 결과를 따로 보고하지 않았다.

---

## 2. 재질 규칙

### 2.1 유리 (향수병, 와인잔, 화장품 병)
- **윤곽만 밝히고 몸통 가운데는 비운다.** 사진가들은 보통 유리의 윤곽에만 하이라이트를 주고, 가운데에는 반사 하이라이트를 두지 않으며, 배경은 단순한 검정이나 흰색을 쓴다. **[관습]** (Usta et al. 2022이 Hunter et al.을 인용)
- **방식을 섞지 않는다.** 유리 조명은 밝은 배경에 어두운 윤곽(브라이트필드)과 어두운 배경에 밝은 윤곽(다크필드) 두 가지가 기본이다. 유리 촬영 실패의 대부분은 두 방식을 동시에 쓰는 데서 나온다. **[관습]** (Hunter et al., *Light — Science & Magic* 6판 7장. ⚠️ 유료 책, O'Reilly 공개 미리보기 기준)
- 제품 연출 목적에 따라 몸통에 하이라이트를 하나 넣는 것도 괜찮다. **[관습]** (Usta et al. 2022)
- 유리는 반사와 굴절을 동시에 해서, 모양이 복잡하면 재질이 애매하게 보일 수 있다. **[실험, 재인용]** (Usta et al. 2022이 Todd & Norman 인용)
- [해석]
  - **다크필드**: 검은 배경, 피사체 양옆 뒤에 길쭉한 라이트(`az ±120–150°, el 0–20°, size (0.1, 1.5)`), 정면 라이트 없음
  - **브라이트필드**: 피사체 바로 뒤에 크고 밝은 면광원(`az 180°`, 배경을 비추는 큰 소스), 정면 라이트 없음

### 2.2 광택 재질 (플라스틱, 도자기, 코팅된 표면)
- **대비와 선명도가 광택을 만든다.** 하이라이트의 대비와 선명도는 광택을 느끼게 하는 가장 효과적인 단서다. **[실험, 재인용]** (Usta et al. 2022이 Pellacini et al. 2000, Wills et al. 2009 인용)
- **하이라이트는 음영과 맞아야 한다.** 하이라이트가 확산 음영과 어긋나면 광택감이 약해진다. **[실험, 재인용]** (Usta et al. 2022이 Kim et al. 2011, Sawayama & Nishida 2018 인용)
- 흐린 환경 조명은 광택 재질을 무광처럼 보이게 한다. **[실험, 재인용]** (Usta et al. 2022이 Doerschner et al. 2007 인용)
- [해석] 광택을 살리려면 작고 선명한 소스(`size ≤ 0.15`)로 하이라이트를 만든다. 무광 느낌을 원하면 반대로 크게.

### 2.3 금속, 거울면
- 사람은 거울 같은 물체의 형태를 반사가 일그러진 모양으로 읽는다. **[실험, 재인용]** (Usta et al. 2022이 Fleming et al. 2004 인용)
- [해석] 금속은 직접광보다 "무엇이 비치는가"가 중요하다. 스튜디오 배경을 켜고, 크고 단순한 면광원(rect)을 비치게 해서 반사에 형태를 준다.

### 2.4 무광 재질 (천, 종이, 점토, 피부의 확산 성분)
- 확산 재질은 들어오는 빛을 뭉개서 보여주기 때문에, 반사 재질보다 조명으로 겉모습을 바꾸기 어렵다. **[계산, 재인용]** (Usta et al. 2022이 Durand et al. 2005 인용)
- [해석] 무광 물체는 방향(그림자 모양)과 대비로 승부한다. 하이라이트 조정에 시간을 쓰지 않는다.

---

## 3. 장르 레시피

[해석] 1–2장의 규칙을 조합한 출발점이다. 장르를 콕 집은 학술 근거는 거의 없다는 점을 사용자에게도 숨기지 않는다.

| 요청 예시 | 조합 | 근거가 된 규칙 |
|---|---|---|
| 고급 향수 / 화장품 병 | 다크필드(검은 배경 + 양옆 뒤 띠 조명) · 정면 필 없음 · 바닥 그림자 유지 | 2.1, 1.2(제품 그림자), 1.4(로우키) |
| 깨끗한 화장품 / 의료 | 브라이트필드(밝은 배경) · 윤곽만 어둡게 | 2.1 |
| 전자제품 / 광택 플라스틱 | 큰 소프트박스 + 작은 하드 소스 · 선명한 하이라이트 | 1.3, 2.2 |
| 금속 시계 / 주얼리 | 큰 면광원 반사 + 작은 포인트 하이라이트 · 어두운 배경 | 2.2, 2.3 |
| 인물, 친근함 / 밝음 | 키 `az 35°, el 30°` · 필 0.4–0.6 · 하이키 | 1.1, 1.2 |
| 인물, 진지함 / 깊이 | 렘브란트 · 필 ≤ 0.15 · 로우키 | 1.1, 1.2, 1.4 |
| 공포 / 불안 | 언더 또는 탑 · 필 없음 · 로우키 | 1.1(EPN), 1.4 |
| 실루엣 / 미스터리 | 역광만 · 얼굴 숨김 | 1.1(EPN) |

---

## 4. 렌더 점검 항목

AI가 렌더를 사용자에게 보여주기 전에 확인한다. 숫자는 코드로 재고, 나머지는 이미지를 보고 판단한다.

**피사체 영역 밝기 통계** (Shacked & Lischinski 2001의 품질 함수 항목. 0–255 휘도 기준) **[계산]**
- **평균 밝기**: 일반 장면 목표 ≈ 150, 어두운 표면이 많으면 ≈ 124. [해석] 로우키 장르에서는 의도적으로 낮게 두되, 피사체의 형태가 읽히는지 따로 확인한다
- **표준편차**: 목표 ≈ 40–45. 너무 낮으면 평평하고(형태가 안 읽힘), 너무 높으면 대비가 과하다
- **경계선 선명도**: 물체의 윤곽과 면이 꺾이는 곳에서 밝기 차이가 충분해야 한다
- **음영 기울기**: 곡면 위로 밝기가 부드럽게 변해야 입체감이 생긴다
- **히스토그램**: 한쪽으로 몰리지 않고 넓게 퍼질수록 좋다 (일반 장면 기준)

**재질 점검** **[관습 / 실험, 재인용]**
- 유리: 몸통 가운데에 큰 하이라이트가 있는가? 다크필드와 브라이트필드가 섞였는가? (2.1)
- 광택: 하이라이트가 충분히 선명하고 대비가 있는가? 음영 방향과 하이라이트 위치가 맞는가? (2.2)

**공통 실패** [해석]
- 하얗게 날아간 픽셀 비율. 피사체 영역의 2%를 넘으면 노출이나 키 밝기를 낮춘다
- 피사체와 배경의 밝기 차이가 너무 작아 윤곽이 묻히지 않는가 → 림 라이트 추가 후보

---

## 5. AI가 이 문서를 쓰는 방식

- **3가지 안을 낸다.** 사용자가 고를 수 있게 서로 지각적으로 다른 후보를 보여주는 방식이다. 하나의 정답을 내미는 대신 갤러리에서 고르게 한다. (Marks et al. 1997, Design Galleries)
- **안끼리는 축이 다르게 만든다.** 예: 다크필드 vs 브라이트필드, 로우키 vs 하이키, 따뜻함 vs 차가움.
- **근거 수준을 같이 말한다.** "이건 실험 결과가 있는 규칙", "이건 업계 관습"처럼 구분해서 설명한다.
- **나중에 붙일 기능의 근거**: 사용자가 원하는 빛을 칠하면 시스템이 그에 맞는 라이트 배치를 찾는 방식(Pellacini et al. 2007)은 레퍼런스 사진 따라 하기의 출발점이 된다.

---

## 참고 문헌

- Bakker, A. (2019). *Lighting up your product! The influence of retail lighting on product perception.* 석사논문, TU Delft. https://repository.tudelft.nl/record/uuid:8e02987b-0128-40f2-8511-b851b9d2e14a
- Huttunen, S. (2025). Faces in shadows: silhouette light, underlight and toplight elicit increased early posterior negativity. *Frontiers in Neuroscience*, 19. https://doi.org/10.3389/fnins.2025.1553977
- Hunter, F., Biver, S., Fuqua, P., & Reid, R. (2021). *Light — Science & Magic* (6판). Routledge. ⚠️ 유료. O'Reilly 공개 미리보기와 Usta et al. (2022)의 인용으로만 확인
- Marks, J., et al. (1997). Design Galleries: A general approach to setting parameters for computer graphics and animation. *SIGGRAPH 97*, 389–400. https://www.merl.com/publications/TR97-14
- Pellacini, F., Battaglia, F., Morley, R. K., & Finkelstein, A. (2007). Lighting with paint. *ACM TOG*, 26(2). https://gfx.cs.princeton.edu/pubs/Pellacini_2007_LWP/lighting_with_paint.pdf
- Poland, J. L. (2015). *Lights, Camera, Emotion!: An examination on film lighting and its impact on audiences' emotional response.* 석사논문, Cleveland State University. https://engagedscholarship.csuohio.edu/etdarchive/379/
- Shacked, R., & Lischinski, D. (2001). Automatic lighting design using a perceptual quality metric. *Computer Graphics Forum*, 20(3), 215–227. https://pages.cs.huji.ac.il/danix-lab/cglab/research/ldesign/Shacked-eg2001.pdf
- Sharma, N. (2016). Luxury implications of showcasing a product with its "cast" shadow. *Journal of Consumer Marketing*, 33(7), 507–516. ⚠️ 유료, 초록 기준
- Usta, B., Pont, S., & Eisemann, E. (2022). Targeting shape and material in lighting design. *Computer Graphics Forum*, 41(7), 299–309. https://repository.tudelft.nl/record/uuid:79e4dfcd-ff32-4250-8865-81203163132b
- Wisessing, P., Zibrek, K., Cunningham, D. W., Dingliana, J., & McDonnell, R. (2020). Enlighten me: Importance of brightness and shadow for character emotion and appeal. *ACM TOG*. (Zhan 2022를 통해 재인용)
- Zhan (2022). 캐릭터 조명과 감정 지각에 관한 석사논문, Trinity College Dublin. https://publications.scss.tcd.ie/theses/diss/2022/TCD-SCSS-DISSERTATION-2022-061.pdf

**아직 원문을 못 연 자료**: Bousseau et al. (2011) *Optimizing environment maps for material depiction*. 재질별 조명 원칙을 다룬 핵심 논문인데, 무료 저장소(HAL)가 자동 접근을 막고 있다. 지금은 Usta et al. (2022)의 정리를 통해서만 반영했다.
