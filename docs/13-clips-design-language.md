# 13. CLIPS Design Language (CDL)

**상태:** Phase 3.7 확정 (2026-07-28)  
**약칭:** CDL  
**쇼케이스:** `/dev/design-system` (local / development만)

이 문서는 CLIPS UI의 **단일 기준**입니다. 개요·링크는 [05-ui-design-system.md](05-ui-design-system.md)를 참고하세요.  
테마(Eclipse/Dawn/System)는 [14-theme-system.md](14-theme-system.md)를 따릅니다.  
UX·정보 우선 원칙은 [design-philosophy.md](design-philosophy.md)를 따릅니다.

---

## 1. CDL 개요

CLIPS Design Language는 「이클립스: 더 어웨이크닝」 **비공식 정보 플랫폼**을 위한 공통 시각·컴포넌트 체계다.

목표:

1. 모든 페이지의 시각적 일관성  
2. 컴포넌트 재사용  
3. 신규 기능 추가 시 디자인 고민 최소화  
4. 모바일·PC 공통 사용성  
5. 접근성 유지  
6. 정보 밀도와 가독성 균형  
7. 공식 홈이 아닌 **정보 아카이브**다운 UI  
8. 판타지 정보 아카이브 분위기

핵심 키워드: **Dark Archive · Eclipse · Rune · Information · Precision · Premium · Compact · Readable**

---

## 2. 핵심 디자인 원칙

- **Information First:** 장식보다 공지·이벤트·패치·쿠폰·공략 정보가 먼저 보인다.
- **Token first:** 색·간격·타이포는 `tokens.css` 변수만 사용한다.
- **No emoji icons:** 운영 UI 아이콘은 inline SVG만 사용한다.
- **Accessible by default:** 키보드, focus-visible, 터치 44px, 색+텍스트 상태.
- **Compact premium:** 얇은 테두리, 은은한 골드, 과한 glow 금지.
- **Unofficial clarity:** 공식 서비스로 오해될 UI 복제·공식 에셋 사용 금지.

---

## 3. 브랜드 계층

1. **게임명(영문 eyebrow)** — Eclipse: The Awakening  
2. **CLIPS** — 플랫폼 브랜드  
3. **게임명(한글 H1)** — 이클립스: 더 어웨이크닝  
4. **정보 콘텐츠** — 공지·이벤트·데이터  

푸터에 비공식 고지(`footer_disclaimer`)를 항상 둔다.

---

## 4. 색상

정의: `app/static/css/tokens.css`

| 범주 | 토큰 | 용도 |
|------|------|------|
| 배경 | `--color-bg-root` ~ `overlay` | 캔버스·헤더 스크림 |
| 표면 | `--color-surface*` | 카드·컨트롤 |
| 텍스트 | `--color-text-*` | 본문·보조·비활성 |
| 액센트 | `--color-accent*` / `--color-accent-glow` | CTA·아이콘·포커스 |
| 테두리 | `--color-border*` / `--color-divider` | 구분선 |
| 상태 | success / warning / danger / info | 배지·토스트·상태 문구 |

상태색만으로 의미를 전달하지 않는다. **항상 텍스트**를 포함한다.

---

## 5. 타이포그래피

스택: Apple SD Gothic Neo / Noto Sans KR / Malgun Gothic / system-ui (외부 웹폰트 없음)

역할 클래스 (`base.css`):

| 역할 | 클래스 |
|------|--------|
| Display | `.text-display` |
| Page Title | `.text-page-title` |
| Section Title | `.text-section-title` |
| Card Title | `.text-card-title` |
| Body | `.text-body` |
| Supporting | `.text-supporting` |
| Caption | `.text-caption` |
| Eyebrow | `.text-eyebrow` |
| Metadata | `.text-meta` |
| Label | `.text-label` |
| Code / Numeric | `.text-code` |

한글 원칙:

- `word-break: keep-all`
- `overflow-wrap: break-word` (긴 URL/식별자)
- 제목: `text-wrap: balance`, 본문: `pretty`

---

## 6. 간격

8px 기반 `--space-1` … `--space-24`.  
섹션 간격은 정보 사이트답게 **과하게 넓히지 않는다**.

---

## 7. 레이아웃

| 패턴 | 클래스 |
|------|--------|
| Container | `.container` / `.container--narrow` |
| Section | `.section` / `.section-muted` |
| Stack | `.stack` / utilities `.stack-sm` `.stack-md` |
| Cluster | `.cluster` |
| Split | `.split` |
| Sidebar | `.sidebar-layout` |
| Dashboard grid | `.dashboard-grid` |
| Card grid | `.card-grid*` |
| Detail | `.detail-layout` |
| Empty | `.empty-layout` |

컨테이너: 1280px / narrow 720px / readable `--content-readable-width` 42rem.

---

## 8. 아이콘

파일: `app/templates/components/icons.html`

규격:

- viewBox `0 0 24 24`
- stroke-width `1.8`
- round caps/joins
- fill `none` (도트 등 예외만 fill)
- `currentColor`
- 기본 20px · 소형 16 · 대형 24 · 장식 32+

구현된 이름: home, notice/news, event, update/patch, coupon, class, content, item, boss, map, guide, search, menu, close, arrow/arrow-right/more, external, tag, time/clock, filter, chevron-down, check, warning, info

후보(문서만): admin, edit, delete, restore, upload, download, calendar, eye, user, sort

금지: 이모지, `→` 등 유니코드 기호를 아이콘 대용으로 사용.

---

## 9. 버튼

`.button` + 변형:

- `--primary` `--secondary` `--ghost` `--text` `--danger` `--icon`
- 크기: `--sm` `--md` `--lg`
- 상태: hover / active / focus-visible / disabled / `.is-loading` / `.is-selected`

규칙: 이동=`<a>`, 동작=`<button>`, disabled 링크 금지, 터치 최소 44px.

---

## 10. 카드

`.card` + `--interactive` `--featured` `--compact` `--selected` `--danger` `--empty`

슬롯: `__header` `__icon` `__title` `__description` `__meta` `__body` `__footer` `__actions`

hover: `translateY` 최대 **-3px**, 금색 테두리, 은은한 glow.

---

## 11. 배지·태그·상태

- Badge: 카테고리/상태 라벨 (`.badge--notice` 등)
- Tag: 분류 키워드 (`.tag` / `--interactive` / `--selected`)
- Status: `.status--success|warning|danger|info|neutral` + `__dot`

---

## 12. 폼

구조만 준비: `.form-field` `.form-label` `.form-input` `.form-select` `.form-textarea` `.form-help` `.form-error` `.form-actions`

상태: default / hover / focus / disabled / readonly / invalid / success  
`aria-describedby`로 help·error 연결.

---

## 13. 테이블

`.table-wrap` > `.table`  
`__cell--numeric` / `__cell--actions` / sticky thead / `__empty`  
모바일: 단순 목록은 카드 전환을 우선 검토. 열 구조가 필수일 때만 가로 스크롤.

---

## 14. 탭·필터·페이지네이션

- Tabs: `.tabs__list` `.tabs__button` + `.is-active` / `aria-selected`
- Filter: `.filter-bar` `.filter-chip` `.filter-reset`
- Pagination: `nav.pagination` + `aria-current="page"`

실제 정렬·필터·페이지 데이터 로직은 이후 단계에서 구현한다.

---

## 15. 모달·드로어·토스트

CSS 구조만 존재. JS focus trap / ESC / scroll lock은 **기능 단계에서 구현**.

- Modal: `.modal__backdrop` `.modal__dialog` …
- Drawer: `.drawer__panel`
- Toast: `.toast-region` `.toast--success|error|info` (`aria-live`)

현재 모바일 메뉴(`common.js`)를 모달 시스템으로 과도하게 추상화하지 않는다.

---

## 16. 상세 콘텐츠

`.article` + `__header` `__title` `__summary` `__meta` `__body` `__source` `__related`

본문 요소: h2/h3, p, lists, blockquote, table, code/pre, figure, hr, links.

---

## 17. 상태 화면

Empty / Loading / Error / No Results / Permission / Maintenance / Coming Soon  
템플릿: `empty_state.html`, `coming_soon.html`, `errors/*`  
아이콘만 사용 (이모지 금지).

---

## 18. 반응형

주요 브레이크포인트: 768 / 1024 (+ 홈 히어로 세부).  
가로 스크롤 금지(의도된 테이블 wrap 제외).  
모바일에서도 hover 없이 계층이 이해되어야 한다.

---

## 19. 접근성

- WCAG AA 명도 대비 지향
- focus-visible, 키보드 접근
- 최소 터치 44px
- 장식 SVG `aria-hidden`
- 아이콘 버튼 접근 가능한 이름
- heading 계층, form label, error 연결
- `prefers-reduced-motion`
- `href="#"` 금지, 클릭 가능한 div 금지

---

## 20. 애니메이션

허용: opacity, transform, border/background-color, shadow  
시간: fast / base / slow  

금지: 정보 지연, 레이아웃 점프, 무한 회전(로딩 스피너 예외), 과한 glow, 텍스트 반짝임, 자동 슬라이드, hover-only 필수 기능.

---

## 21. 클래스 명명 규칙

- 블록: `.card`
- 요소: `.card__title`
- 변형: `.card--compact`
- 상태: `.is-active`
- JS hook: `[data-nav-toggle]` (클래스와 분리)

신규·수정 컴포넌트부터 적용. 전역 강제 리네임 금지.

---

## 22. 컴포넌트 추가 절차

1. 토큰으로 표현 가능한지 확인  
2. `components.css`에 블록 추가  
3. 필요 시 `icons.html`에 SVG 추가 (후보만 문서화하지 빈 SVG 금지)  
4. `/dev/design-system`에 정적 예시 추가  
5. 이 문서 표 갱신  
6. pytest로 noindex·클래스·아이콘 규격 확인  

---

## 23. 금지 패턴

- 공식 Eclipse UI/로고 복제, 공식 이미지 hotlink  
- 이모지·유니코드 기호 아이콘  
- 가짜 조회수·가짜 공지처럼 보이는 수치  
- 외부 JS/CSS/아이콘 CDN, 외부 웹폰트  
- Tailwind급 유틸 폭증  
- disabled `<a>`  
- 카드 안 중첩 링크  

---

## 24. 코드 예시

```html
<a class="button button--primary" href="/news">최신 소식</a>
<article class="card card--featured">
  <h3 class="card__title">샘플 제목</h3>
  <p class="card__description">보조 설명</p>
</article>
<span class="badge badge--soon">준비 중</span>
{{ icon("notice") }}
```

---

## 25. QA 체크리스트

- [ ] 메인·준비 중·404 시각 퇴행 없음  
- [ ] `/dev/design-system` local 200, production 404  
- [ ] sitemap 미포함, robots noindex,nofollow  
- [ ] 아이콘 viewBox·stroke 1.8  
- [ ] 이모지 없음  
- [ ] 빈 `href="#"` 없음  
- [ ] 모바일 가로 스크롤 없음  
- [ ] pytest / ruff / mypy 통과  

---

## CSS 파일 구조

```
app/static/css/
├── reset.css
├── tokens.css
├── base.css
├── layout.css
├── components.css
├── utilities.css
└── pages/
    ├── home.css
    └── design-system.css
```
