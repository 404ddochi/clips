# 14. CLIPS Dual Theme System

**상태:** Phase 3.8 확정  
**관련:** [13-clips-design-language.md](13-clips-design-language.md)

## 테마 개요

CLIPS는 **Dual Theme**을 지원한다.

| 내부 콘셉트 | 사용자 라벨 | `data-theme` |
|-------------|-------------|--------------|
| Eclipse | 다크 모드 | `dark` |
| Dawn | 라이트 모드 | `light` |
| (OS) | 시스템 설정 | 해석된 dark/light |

사용자 preference는 `data-theme-preference="system|light|dark"`.

기본값: **system**

## Eclipse / Dawn

- **Eclipse:** 깊은 남색 아카이브, 샴페인 골드. 기존 CDL 다크.
- **Dawn:** Ivory · Warm Beige · Champagne/Bronze Gold · Deep Navy 텍스트. 순백(#fff) 중심 금지.

## 정책

1. `system` → `prefers-color-scheme`로 해석  
2. `light` / `dark` → OS 무시  
3. `system`일 때만 OS 변경 리스너 반영  
4. 저장: `localStorage["clips-theme"]` (쿠키/DB 없음)  
5. 저장 실패 시 세션 내 적용 + 안전 폴백

## 토큰 구조

`app/static/css/tokens.css`

- 공유: 타이포·간격·radius·z-index  
- `:root, html[data-theme="dark"]` → Eclipse  
- `html[data-theme="light"]` → Dawn  
- Atmosphere 토큰: Hero/strip/body glow (`--hero-*`, `--eclipse-*`, `--info-strip-surface` …)

컴포넌트는 의미 토큰만 사용. 테마별 `.card` 재정의 금지.

## 초기 로딩

`base.html` `<head>` 인라인 스크립트:

1. localStorage 읽기  
2. system이면 prefers-color-scheme  
3. `data-theme` / `data-theme-preference` / `colorScheme` 설정  

이후 `theme.js`가 컨트롤·저장·meta theme-color 갱신.

## UI

헤더 `theme-control` 팝오버:

- 시스템 설정 / 라이트 모드 / 다크 모드  
- 아이콘: `theme-system`, `theme-light`, `theme-dark` + `check`  
- `aria-expanded`, ESC, 외부 클릭, 44px 터치  

## 접근성

- 버튼 이름: `테마 설정, 현재 {시스템 설정|라이트 모드|다크 모드}`  
- 체크 + 텍스트로 선택 상태  
- focus-visible, reduced motion 유지  

## 테마 추가 절차

1. tokens에 새 `data-theme` 블록  
2. atmosphere 토큰 매핑  
3. 쇼케이스·헤더 검수  
4. docs 갱신  

## 금지 패턴

- 순백 관리자 UI / 양피지 과장  
- 컴포넌트별 라이트 하드코딩  
- 이모지 테마 아이콘  
- 서버 DB 테마 저장(이번 단계)

## QA 체크리스트

- [ ] FOUC 최소화  
- [ ] 새로고침 후 설정 유지  
- [ ] system + OS 변경  
- [ ] Dawn 대비·카드 구분·골드  
- [ ] Hero graphic (Eclipse disc)  
- [ ] 모바일 가로 스크롤·팝오버 잘림 없음  
- [ ] 메인 / coming soon / 404 / design-system  
