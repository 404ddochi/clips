# 15. Information Pages (Mock UI)

CLIPS Phase 4 — 데이터베이스 없이 **정보 페이지 UI + Mock 데이터 구조**를 제공한다.

**상태:** Mock / noindex  
**실데이터 전환 시:** robots·sitemap·본문 출처 정책을 재검토한다.

---

## 페이지 IA

| 영역 | URL | 역할 |
|------|-----|------|
| 소식 허브 | `/news` | 카테고리 탭, 주요 소식, 최신 3종, 전체 목록 |
| 공지 목록 | `/news/notices` | 공지 List Row |
| 이벤트 목록 | `/news/events` | 이벤트 List Row |
| 패치노트 목록 | `/news/patch-notes` | 패치노트 List Row |
| 공지 상세 | `/news/notices/{slug}` | Article Layout |
| 이벤트 상세 | `/news/events/{slug}` | Article Layout |
| 패치노트 상세 | `/news/patch-notes/{slug}` | Article Layout |
| 쿠폰 목록 | `/coupons` | Coupon Row 고밀도 리스트 + SSR 필터 |
| 쿠폰 상세 | `/coupons/{slug}` | 코드·기간·주의 |

준비 중 유지: `/classes`, `/contents`, `/items`, `/bosses`, `/maps`, `/guides`

---

## URL · 라우트 name

| name | path |
|------|------|
| `news` | `/news` |
| `news_notices` | `/news/notices` |
| `news_events` | `/news/events` |
| `news_patch_notes` | `/news/patch-notes` |
| `news_notice_detail` | `/news/notices/{slug}` |
| `news_event_detail` | `/news/events/{slug}` |
| `news_patch_detail` | `/news/patch-notes/{slug}` |
| `coupons` | `/coupons` |
| `coupon_detail` | `/coupons/{slug}` |

템플릿은 `url_for`를 사용한다. 카테고리 탭은 JS 탭이 아니라 **링크형 내비게이션**이다.

---

## 데이터 구조

모듈:

- `app/services/content_types.py` — `NewsItem`, `CouponItem`, `ArticleBlock`, 탭·메타 상수
- `app/services/news_mock_data.py` — 고정 datetime Mock 소식
- `app/services/coupon_mock_data.py` — SAMPLE / CLIPS-DEMO / 준비 중 코드만

주요 필드 (`NewsItem`):

`slug`, `category`, `title`, `summary`, `published_at`, `updated_at`, `source_name`, `source_url`, `is_featured`, `status_label`, `body`, `badge_*`

주요 필드 (`CouponItem`):

`slug`, `code`, `title`, `reward_summary`, `valid_from`, `valid_until`, `status`, `status_label`, `source_*`, `body`, `usage_notes`

날짜는 **고정 상수**이며 요청 시점 실시간 생성하지 않는다.

---

## 목록 구조

공통:

- breadcrumb, compact page header, content tabs
- 검색·필터·정렬 Mock (`disabled` + “기능 준비 중”)
- List Row (`news-row`): badge, title, summary, date, source, status, arrow
- 페이지네이션은 **1페이지만 활성**인 구조 표시 (실제 분할 없음)

---

## 상세 구조

공통 Article:

- badge, H1, summary, meta (`<time datetime>`), body blocks
- 원문 링크는 `source_url`이 있을 때만
- 이전/다음, 목록으로, 관련 콘텐츠, source notice

본문 블록: paragraph, heading2/3, list, olist, quote, callout, note

---

## 쿠폰 구조

대표 컴포넌트: **Coupon Row** (고밀도 가로 리스트)

- 목적: 코드를 찾고 복사한다 (`Find Faster`)
- SSR 필터: `?status=all|available|expiring|expired` (링크형 세그먼트)
- 정보 우선순위: 상태 → 코드 → 보상 → 기간 → 출처 → 복사
- 종료 쿠폰: 복사 버튼 **disabled 유지**(숨기지 않음) — 액션 존재와 사유를 명확히 알리기 위함
- 복사: `common.js`의 `data-copy-text` (clipboard + fallback), JS 없이도 코드 텍스트 선택 가능
- SEO title: `쿠폰 - CLIPS | 이클립스: 더 어웨이크닝 정보 사이트` · robots `noindex, follow`
- UX 원칙: [design-philosophy.md](design-philosophy.md)

---

## SEO 정책

| 구분 | 정책 |
|------|------|
| 목록 title | `{주제} \| CLIPS - 이클립스: 더 어웨이크닝` |
| 상세 title | `{문서 제목} \| CLIPS` |
| robots (Mock) | `noindex, follow` |
| sitemap | Mock 정보 경로 **미포함** (홈만) |
| JSON-LD | BreadcrumbList + Article (publisher=`CLIPS`, author=`CLIPS Mock`) |

실데이터 전환 시:

1. robots를 `index, follow`로 전환 가능 여부를 카테고리별로 검토
2. sitemap에 목록·공개 상세 추가
3. 공식 관계/발행자를 암시하지 않도록 Article 메타 유지

---

## Mock → DB 전환

1. `NewsItem` / `CouponItem` 필드를 SQLAlchemy 모델 컬럼으로 매핑
2. `list_*` / `get_*_by_slug`를 리포지토리로 교체
3. 라우터·템플릿 시그니처는 유지
4. Alembic migration 후 Mock 모듈은 seed 또는 제거

## Mock → 크롤러 전환

1. 수집 결과를 동일 필드에 적재
2. `source_url` / `source_name` 필수화
3. 본문은 요약·구조화 후 원문 링크 우선
4. 공식 문구 복제 금지 정책 유지

---

## 접근성

- 페이지당 H1 1개
- breadcrumb / category nav / pagination `aria-label`
- `aria-current="page"` on active tab
- disabled 컨트롤 명시, `href="#"` 금지
- 날짜 `<time datetime>`

## 반응형

확인 폭: 1440 · 1366 · 1280 · 1024 · 768 · 430 · 390 · 360  
List row는 모바일에서 세로 스택, 탭은 wrap.

## 테스트

`tests/test_information_pages.py` — 목록/상세 200·404, noindex, 카테고리 링크, 쿠폰 Coupon Row·필터·복사 버튼, 홈 연계, sitemap 제외, coming soon 유지.

## 완료 조건

- [x] 소식 허브·카테고리 목록·상세
- [x] 쿠폰 목록·상세
- [x] Mock 데이터 분리·타입
- [x] 메인 데이터 연계
- [x] Dark/Light 토큰
- [x] SEO noindex
- [x] pytest / ruff / mypy
- [x] 본 문서
