# CLIPS UI 디자인 시스템

## 개요

CLIPS UI는 **다크 테마**, **골드 악센트**, **한국어 가독성**을 중심으로 합니다. 구현 소스는 `app/static/css/tokens.css` 및 `components.css`, `layout.css`입니다. 새 페이지는 토큰·컴포넌트 클래스를 **재사용**하고 페이지 전용 스타일만 `pages/`에 추가합니다.

---

## 확정

### 브랜드

| 요소 | 값 |
|------|-----|
| 영문 로고 | CLIPS |
| 국문 표기 | 클립스 |
| 로고 마크 | ◈ (CSS `.logo-mark`, 향후 SVG 교체 가능) |
| 톤 | 차분한 다크 UI + 프리미엄 RPG 느낌의 골드 포인트 |
| 비공식 고지 | 푸터 disclaimer (`footer.html`) — 모든 페이지 공통 |

### 색상 (Design Tokens)

정의: `app/static/css/tokens.css`

| 토큰 | 값 | 용도 |
|------|-----|------|
| `--color-bg-primary` | `#080b12` | 페이지 배경 |
| `--color-bg-secondary` | `#10151f` | 섹션 배경 |
| `--color-bg-elevated` | `#171d29` | 카드·패널 |
| `--color-text-primary` | `#f4f1e8` | 본문·제목 |
| `--color-text-secondary` | `#a9adba` | 부제·설명 |
| `--color-text-muted` | `#717786` | 메타·캡션 |
| `--color-accent` | `#c6a15b` | CTA·링크 강조 |
| `--color-accent-hover` | `#dfbd73` | hover, badge |
| `--color-accent-soft` | `rgba(198,161,91,0.14)` | 버튼 secondary 배경 |
| `--color-border` | `rgba(255,255,255,0.1)` | 기본 테두리 |
| `--color-border-accent` | `rgba(198,161,91,0.45)` | hover 테두리 |

**대비**: 본문 `#f4f1e8` on `#080b12` — WCAG AA 목표(일반 텍스트 4.5:1). muted 텍스트는 **보조 정보에만** 사용.

### 타이포그래피

| 항목 | 규칙 |
|------|------|
| Font stack | `--font-sans`: Pretendard, Apple SD Gothic Neo, Noto Sans KR, system-ui |
| Base size | 16px (`base.css`) |
| 제목 scale | h1 2rem~2.5rem, h2 1.5rem, h3 1.25rem (페이지별 조정 가능) |
| Line height | 본문 1.6~1.75 |
| Weight | UI 600, 본문 400 |

**확정**: 웹폰트 Pretendard는 CDN 또는 self-host — **향후 결정**(self-host 권장 SEO·프라이버시).

### 간격(Spacing)

- Container max width: `--container-width: 1280px`
- Header height: `--header-height: 72px`
- 섹션 vertical padding: `clamp(2rem, 5vw, 4rem)` (layout.css 패턴)
- 카드 내부: `1.25rem` (`info-card`)
- Grid gap: `1rem` ~ `1.5rem` (홈 카드 그리드)

### Radius

| 토큰 | 값 |
|------|-----|
| `--radius-sm` | 6px — 버튼, 입력 |
| `--radius-md` | 12px — 카드 |
| `--radius-lg` | 18px — 히어로 패널 |
| pill badge | 999px |

### Shadow

- `--shadow-card`: `0 18px 50px rgba(0,0,0,0.28)` — `.info-card`
- hover 시 border + translateY(-3px), shadow는 과도하게 키우지 않음

### Motion

| 토큰 | 값 | 사용 |
|------|-----|------|
| `--transition-fast` | 160ms ease | 버튼, 링크 |
| `--transition-base` | 280ms ease | 카드 hover |
| `--transition-slow` | 600ms cubic-bezier | 히어로 등장(선택) |

**a11y**: `@media (prefers-reduced-motion: reduce)` 에서 transform·transition **비활성화**(향후 global rule 추가).

---

## 컴포넌트

### Buttons (`.btn`)

| 클래스 | 스타일 |
|--------|--------|
| `.btn` | min-height 2.75rem, padding 0.65rem 1.15rem, radius-sm |
| `.btn-primary` | 골드 그라데이션, 텍스트 `#1a1408` |
| `.btn-secondary` | accent soft 배경 + accent border |

Hover: `translateY(-1px)`, primary는 brightness.

### Cards (`.info-card`)

- elevated 배경, border, shadow-card
- hover: accent border, translateY(-3px)
- 하위: `.info-card-title`, `.info-card-text`, `.info-card-cta`

### Badges (`.badge`)

- 소형 pill, accent soft/bg, 0.78rem, semibold
- 용도: 공지/패치/이벤트 라벨 (`PLACEHOLDER_NEWS` 등)

### Inputs (향후)

- 배경 `--color-bg-secondary`, border `--color-border`
- focus: `outline 2px solid var(--color-accent)`, offset 2px
- error: border red-400 + aria-invalid

**확정 방향**: native `<input>`, `<select>` 스타일 통일; 커스텀 only when necessary.

### Empty state (`components/empty_state.html`)

- 아이콘 + 제목 + 설명 + optional CTA — 준비 중·검색无 결과 공용

---

## 레이아웃

### Header (`.site-header`)

- Sticky top, backdrop blur( layout.css )
- Logo → primary nav (`MAIN_NAV` loop)
- Mobile: `.nav-toggle` + `data-nav-toggle` (`common.js`)
- Active: `.nav-link.is-active`, `aria-current="page"`

### Footer (`.site-footer`)

- 브랜드, tagline, **비공식 disclaimer**, copyright
- 링크 확장(공식 사이트, GitHub, 문의) — **향후**

### Responsive breakpoints (확정 방향)

| 이름 | width |
|------|-------|
| sm | 640px |
| md | 768px |
| lg | 1024px |
| xl | 1280px (container) |

- `< md`: 햄버거 nav, single column cards
- `>= lg`: multi-column home grids

---

## 접근성 (a11y)

| 항목 | 규칙 |
|------|------|
| Lang | `<html lang="ko">` |
| Landmark | header, nav `aria-label`, main, footer |
| Skip link | **향후** `#main-content` |
| Focus | 키보드 focus ring visible |
| Images | `alt` 필수; 장식 `alt=""` |
| Motion | prefers-reduced-motion |

---

## 향후 결정

- 라이트 모드 / `prefers-color-scheme` 대응 (**기본 dark only**)
- 아이콘 세트 (Lucide vs inline SVG)
- 다크 모드 OG 이미지 템플릿 (1200×630)
- Design token JSON export for Figma

---

## 관련 문서

- [02-directory-structure.md](./02-directory-structure.md)
- [06-seo-strategy.md](./06-seo-strategy.md) — 이미지·CWV
