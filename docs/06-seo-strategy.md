# CLIPS SEO 전략

## 문서 목적

CLIPS는 **비공식 팬 정보 사이트**이지만, 유저가 검색으로 필요한 정보에 도달하는 것이 핵심 가치입니다. 본 문서는 Google·Naver·Bing을 포함한 **검색 엔진 최적화**, **기술 SEO**, **콘텐츠 SEO**, **운영 체크리스트**를 정의합니다. 구현 상태는 코드(`app/services/seo.py`, `seo_meta.html`, `web.py`)와 대조합니다.

---

## 확정

### SEO-first 원칙

1. **SSR HTML**에 title, meta description, canonical, robots, OG/Twitter, JSON-LD를 포함한다.
2. **준비 중·오류·중복** URL은 색인에서 제외하거나 canonical로 통합한다.
3. **출처·비공식 고지**를 푸터와 FAQ에 유지해 E-E-A-T(경험·전문성·권위·신뢰) 리스크를 줄인다.
4. **Core Web Vitals**를 배포 게이트로 모니터링한다.

### 환경 변수

| 변수 | SEO 영향 |
|------|----------|
| `APP_BASE_URL` | canonical, sitemap loc, OG url, JSON-LD url — **운영 도메인과 반드시 일치** |
| `DEFAULT_LOCALE` | `ko`, `og:locale` ko_KR |

---

## 검색 엔진별 전략

### Google

| 항목 | 정책 |
|------|------|
| 크롤링 | `robots.txt` Allow `/`, sitemap 제출 |
| 렌ndering | SSR — JS 필수 아님 |
| Structured data | schema.org JSON-LD (`WebSite`, `WebPage`; 확장은 아래) |
| Discover | 고품질 이미지·최신 소식 페이지 (향후) |
| 정책 | thin content, scraped content without added value **지양** — 요약·구조화·내부 링크로 부가가치 |

**Google Search Console (GSC)**

- Property: **URL prefix** 또는 **Domain** (Domain 권장 — 서브도메인 포함 시)
- Sitemap: `https://{domain}/sitemap.xml`
- **확정**: staging은 `noindex` 또는 Basic Auth + GSC 미등록

### Naver (네이버 검색·서치어드바이저)

| 항목 | 정책 |
|------|------|
| 수집 | HTML 메타·본문 SSR (네이버는 JS 렌더링 한계 — SSR 필수) |
| 메타 | `<title>`, `description`, `canonical` — `seo_meta.html` |
| Open Graph | og:title, og:description, og:url, og:image — 카카오·네이버 공유 |
| 사이트맵 | GSC와 동일 URL 제출 (네이버 서치어드바이저 → 요청 → 사이트맵) |
| RSS | 네이버 제출용 RSS 2.0 — **향후** `/feed.xml` |
| robots | 불필요한 경로 Disallow 최소화; 준비 중은 noindex |

**네이버 특화**

- **모바일 친화성**: viewport, 터치 타겟, 가로 스크롤 없음
- **표준 URL**: canonical로 www/non-www, http/https 통일
- **수집 제한**: 429/5xx 최소화 (크롤러 rate limit)

### Bing (Microsoft Bing Webmaster Tools)

| 항목 | 정책 |
|------|------|
| Submit | sitemap, URL inspection |
| Structured data | Google과 동일 JSON-LD (Bing schema 지원) |
| IndexNow | publish/update 시 ping — **향후 결정** (API key) |

---

## 기술 SEO

### robots.txt

**구현**: `GET /robots.txt` → `build_robots_txt()`

```
User-agent: *
Allow: /
Sitemap: {APP_BASE_URL}/sitemap.xml
```

**향후 확장 (필요 시만)**

```
Disallow: /admin
Disallow: /api/
```

**확정**: `/static` 은 Allow (이미지 SEO·OG).

### sitemap.xml

**구현**: `GET /sitemap.xml`, `SITEMAP_PUBLIC_PATHS` 현재 `("/",)` only.

| 필드 | 규칙 |
|------|------|
| loc | `settings.absolute_url(path)` |
| lastmod | UTC date ISO8601 (`current_sitemap_lastmod()`) |
| changefreq | **향후** — Google은 무시 가능; 선택적 |
| priority | **향후** — 선택적 |

**확정 정책**

- `status=published` 인 상세 URL만 포함
- preparing 페이지 **제외** (noindex와 일치)
- sitemap index 분할: URL > 50,000 또는 file > 50MB 시 `sitemap-index.xml`

**향후**: DB-driven sitemap generator service + cache TTL 15m.

### Canonical

- 템플릿: `<link rel="canonical" href="{{ seo_canonical_url }}">`
- **확정**: query string 포함 canonical **금지** (필터·utm 제거한 path만)
- 페이지네이션: page1 canonical self; page2+ `rel=canonical` to page1 **또는** each page self — **향후 결정**(콘텐츠 중복 정도에 따라)

### Metadata (title & description)

**함수**: `seo_context()` → `components/seo_meta.html`

| 필드 | 규칙 |
|------|------|
| title | 아래 **페이지별 title 규칙** 참고; **50~60자 권장** |
| description | 120~160자, 핵심 키워드 자연스럽게; 중복 title 금지 |
| robots | default `index, follow`; 404/500/preparing 예외 |
| og:locale | `ko_KR` |
| og:title | HTML `<title>`과 동일 |
| twitter:card | `summary_large_image` |

#### 페이지별 title 규칙

| 페이지 | 형식 | 예 |
|--------|------|----|
| 메인 | `CLIPS - 이클립스: 더 어웨이크닝 정보 사이트` | `DEFAULT_HOME_TITLE` |
| 목록/상세 | `{페이지 핵심 제목} \| CLIPS - 이클립스: 더 어웨이크닝` | `클래스 \| CLIPS - 이클립스: 더 어웨이크닝` |

JSON-LD:

- 사이트명(`WebSite.name` / `isPartOf.name`): **CLIPS**
- 게임명: **이클립스: 더 어웨이크닝** / **Eclipse: The Awakening**

**홈 확정 예**

- title / og:title: `CLIPS - 이클립스: 더 어웨이크닝 정보 사이트` (`DEFAULT_HOME_TITLE`)
- description: `DEFAULT_HOME_DESCRIPTION` (변경 없음)

### hreflang

- 단일 언어(ko) — **hreflang 미적용**
- 다국어 도입 시 `ko`, `en`, `x-default` — **향후 결정**

---

## Structured Data (JSON-LD)

**구현**: `build_website_json_ld`, `build_home_json_ld`; template loop `application/ld+json`.

### 확정 타입 (현재)

| @type | 용도 |
|-------|------|
| WebSite | sitelinks search box 후보 (SearchAction **향후**) |
| WebPage | 홈 페이지 |

### 확정 계획 (콘텐츠별)

| @type | 페이지 | 필수 필드 |
|-------|--------|-----------|
| BreadcrumbList | 상세 전반 | itemListElement name, item |
| Article / NewsArticle | notice, update | headline, datePublished, author(Organization CLIPS) |
| Event | event | name, startDate, endDate, location(Online) |
| FAQPage | faq | mainEntity Question/Answer |
| HowTo | guide (해당 시) | step |
| VideoObject | video embed | name, thumbnailUrl, embedUrl |
| ItemList | 목록 | itemListElement |

**금지·주의**

- FAQ schema **페이지 visible FAQ와 1:1** 일치
- Review/Rating **가짜 평점 금지**
- Game schema — 공식 IP와 혼동되지 않게 `isPartOf` WebSite only

### SearchAction (향후)

```json
"potentialAction": {
  "@type": "SearchAction",
  "target": "{base}/search?q={search_term_string}",
  "query-input": "required name=search_term_string"
}
```

검색 SSR 구현 후 추가.

---

## 색인(Indexing) 정책

| 페이지 유형 | robots | sitemap |
|-------------|--------|---------|
| 홈, published 상세 | index, follow | 포함 |
| preparing (`/news` 등) | noindex, follow | **미포함** |
| 404, 500 | noindex, nofollow | 미포함 |
| admin, api | noindex 또는 auth | 미포함 |
| 검색 결과 `?q=` | noindex, follow (권장) | 미포함 |

**follow on noindex**: 링크 equity가 내부 링크 구조로 전달되도록 preparing에서 follow 유지 (**확정**).

---

## URL 설계

| 규칙 | 예 |
|------|-----|
| 소문자, hyphen | `/guides/beginner-routes` |
| 의미 있는 slug | `/classes/warrior` |
| 깊이 | 목표 ≤ 3 segments |
| trailing slash | 없음 |
| legacy redirect | 301 map in router — **향후** |

---

## 콘텐츠 SEO

### 제목 작성

- H1 **페이지당 1개**, title tag와 **주제 일치** (완전 동일 불필요)
- 키워드 stuffing 금지; 게임명 「이클립스: 더 어웨이크닝」은 브랜드 페이지·홈에 집중

### 본문

- 최소 useful content: 상세 페이지 **300자+** 목표 (데이터 테이블·스킬 목록 포함)
- 공지: **요약 + 원문 링크**; 전문 copy는 권리·중복 이슈 검토
- 이미지: figure + figcaption where helpful
- 내부 링크: class ↔ skill ↔ boss ↔ item 교차

### 중복·얇은 콘텐츠

- preparing은 noindex로 **색인 방지**
- 크롤만 하고 요약 없는 페이지 **출시 금지**
- 동일 패치를 notice/update **중복 저장 시** canonical 하나 선택

---

## 이미지 SEO

| 항목 | 규칙 |
|------|------|
| alt | 콘텐츠 설명 (스킬명, 보스명) |
| file name | `boss-name-clips.webp` — **향후** |
| format | WebP/AVIF 우선, SVG 아이콘 |
| OG | default `/static/images/placeholders/og-default.svg`; 상세별 custom 1200×630 **향후** |
| lazy loading | below-fold `loading="lazy"` |
| dimensions | width/height attribute로 CLS 방지 |

---

## 소셜·RSS

### Open Graph / Twitter

**확정**: `seo_meta.html` og:*, twitter:* — image absolute URL via `absolute_url`.

### RSS / Atom

- **향후**: `/feed.xml` — notice + update + event (published_at desc, limit 50)
- 네이버·Feedly 제출

---

## Core Web Vitals (CWV)

| 메트릭 | 목표 (p75 mobile) | CLIPS 액션 |
|--------|-------------------|------------|
| LCP | ≤ 2.5s | SSR, hero image priority, CDN static |
| INP | ≤ 200ms | minimal JS (`common.js`, `home.js` only) |
| CLS | ≤ 0.1 | img dimensions, font-display swap |

**확정**: CSS layered load in base; blocking JS at end of body.

**모니터링**: GSC CWV report, Lighthouse CI on PR — **향후**.

---

## 로컬·국제

- Primary: **한국** (`Asia/Seoul` dates in sitemap/content)
- `inLanguage`: ko in JSON-LD

---

## 구현 체크리스트

### Google Search Console

- [ ] Domain property verification (DNS TXT)
- [ ] `APP_BASE_URL` production 값 확인
- [ ] Sitemap 제출 `/sitemap.xml`
- [ ] URL inspection — 홈 indexed
- [ ] Page indexing report — excluded `noindex` 확인
- [ ] Core Web Vitals — poor URL 조치
- [ ] Manual actions / Security issues 모니터
- [ ] Structured data rich results report (JSON-LD 추가 후)

### Naver Search Advisor (서치어드바이저)

- [ ] 사이트 등록 및 소유 확인 (HTML file or meta)
- [ ] robots.txt 수집 확인
- [ ] 사이트맵 제출
- [ ] 모바일 최적화 점검
- [ ] RSS 제출 (feed 구현 후)
- [ ] 검색 반영 — 신규 URL 요청 (선택)
- [ ] SSL HTTPS 전면 적용

### Bing Webmaster

- [ ] 사이트 추가, sitemap
- [ ] URL inspection
- [ ] IndexNow (선택)

### 배포 전 공통

- [ ] `<title>`, description 페이지별 unique
- [ ] canonical absolute HTTPS
- [ ] 404/500 noindex
- [ ] preparing noindex + sitemap 미등록
- [ ] favicon `/static/favicon/favicon.svg`
- [ ] disclaimer footer 노출
- [ ] lighthouse SEO score ≥ 90 (local)

---

## 향후 결정

- **IndexNow** key endpoint 공개 여부
- **AMP** — **도입 안 함** (기본)
- **Pagination** rel prev/next — Google deprecated but Bing may use; policy revisit
- **AI Overview** 대응: structured FAQ, clear summaries
- **Cookie consent** — analytics 도입 시
- **Official game name** in title A/B (CTR vs brand)

---

## 관련 문서

- [00-project-overview.md](./00-project-overview.md)
- [04-api-design.md](./04-api-design.md)
- [05-ui-design-system.md](./05-ui-design-system.md)

## 코드 참조 (현재)

| 기능 | 위치 |
|------|------|
| seo_context | `app/dependencies.py` |
| robots/sitemap/json-ld | `app/services/seo.py` |
| meta tags | `app/templates/components/seo_meta.html` |
| preparing noindex | `app/routers/web.py` `_preparing_page` |
| sitemap paths | `app/core/constants.py` `SITEMAP_PUBLIC_PATHS` |
