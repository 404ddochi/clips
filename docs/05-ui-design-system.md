# CLIPS UI 디자인 시스템

**상세 기준(단일 소스):** [13-clips-design-language.md](13-clips-design-language.md) (CDL)  
**테마:** [14-theme-system.md](14-theme-system.md) — Eclipse(다크) / Dawn(라이트) / System  
**쇼케이스:** `/dev/design-system` — `APP_ENV=local|development` 에서만 접근

이 문서는 UI 시스템의 **개요·진입점**이다. 토큰·컴포넌트·접근성·금지 패턴의 상세 규칙은 CDL 문서를, 테마 정책은 14번 문서를 따른다.

## 디자인 원칙 (요약)

- **정보 우선:** Dark fantasy 톤은 유지하되 가독성·속도를 최우선.
- **토큰 우선:** 색·간격·타이포는 `tokens.css` 변수만 사용.
- **접근성:** `focus-visible`, skip link, 시맨틱 HTML, `prefers-reduced-motion`.
- **비공식 고지:** 푸터 `footer_disclaimer` 전역 문구.
- **아이콘:** CLIPS inline SVG만 (이모지·외부 아이콘 라이브러리 금지).

## 구현 위치

| 영역 | 경로 |
|------|------|
| 토큰 | `app/static/css/tokens.css` |
| 베이스·타이포 역할 | `app/static/css/base.css` |
| 레이아웃 패턴 | `app/static/css/layout.css` |
| 컴포넌트 | `app/static/css/components.css` |
| 최소 유틸 | `app/static/css/utilities.css` |
| 아이콘 | `app/templates/components/icons.html` |
| 공통 조각 | `app/templates/components/*` |

## 컴포넌트 요약

| 종류 | 주요 클래스 |
|------|-------------|
| 버튼 | `.button--primary` … `--danger`, `--sm/md/lg` |
| 카드 | `.card`, `--interactive`, 슬롯 `__title` 등 |
| 배지/태그/상태 | `.badge-*`, `.tag`, `.status-*` |
| 폼·테이블 | `.form-*`, `.table-wrap` / `.table` |
| 탭·페이지 | `.tabs__*`, `.pagination__*` |
| 본문 | `.article` / `.article__body` |
| 빈 상태 | `empty_state.html` |

## 반응형·접근성

- 모바일 메뉴: `aria-expanded`, ESC·백드롭, `body.is-nav-open`
- **금지:** `href="#"`, outline 제거만 하는 CSS, hover 전용 필수 정보

## 금지 패턴

- 공식 Eclipse UI/로고 복제, 공식 이미지 hotlink
- 가짜 조회수·가짜 공지 제목, 미제공 `og:image` placeholder
- 외부 JS/CSS CDN, 외부 웹폰트, 이모지 아이콘

자세한 금지·추가 절차·QA는 [CDL §22–25](13-clips-design-language.md)를 참고한다.
