# 07. 크롤링 전략

CLIPS는 **이클립스: 더 어웨이크닝** 관련 **공개 정보**를 수집·정리해 사용자에게 **요약과 원문 링크**를 제공한다. 본 문서는 수집 범위, 법·정책 준수, 데이터 품질, 운영 흐름을 정의한다.

**범례**

| 표기 | 의미 |
|------|------|
| **확정** | 초기 설계에서 반드시 지킬 원칙·구조 |
| **향후 결정** | 공식 채널·약관·구현 단계에 따라 구체화 |

---

## 1. 목표와 원칙

### 확정

- 크롤링은 **서버 스케줄·관리자 수동 실행**으로만 수행한다. **일반 사용자 요청 시 실시간 크롤링은 하지 않는다.**
- 수집 결과는 **CLIPS DB에 메타데이터·짧은 요약·원문 URL** 위주로 저장한다.
- 모든 공개 페이지에 **출처(원문 링크, 수집 시각, 비공식 사이트 고지)** 를 표시한다.
- 공식 사이트·퍼블리셔를 **CLIPS로 오인하지 않도록** 제목·UI에 “비공식” 맥락을 유지한다.

### 향후 결정

- 공식 API 또는 RSS가 제공될 경우 HTML 크롤링 대비 **우선 채널**로 전환할지 여부
- 다국어(영문 공지 등) 병렬 수집 범위

---

## 2. 수집 대상 유형

### 2.1 공식 공지 (notices)

**확정**

- 카테고리: 운영 공지, 점검, 업데이트 안내 등 **공식 채널 게시판/공지 목록**
- 저장 필드(개념): `category`, `title`, `summary`, `excerpt`(선택), `source_url`(UNIQUE), `source_post_id`, `published_at`, `crawled_at`, `content_hash`(향후 컬럼)
- 목록 API/HTML 파싱 실패 시 **해당 카테고리만 스킵**하고 다른 카테고리는 계속 처리

**향후 결정**

- Eclipse 공식 사이트·런처·커뮤니티 중 **1차 소스 URL** 확정 (구현 5단계 전 채널 목록 문서화)

### 2.2 이벤트 (events)

**확정**

- 이벤트 기간(`starts_at`, `ends_at`) 파싱 가능 시 저장; 불가 시 `published_at`만 사용
- 종료된 이벤트는 **아카이브 노출**하되 SEO `noindex` 여부는 SEO 문서(06)와 연동 검토

**향후 결정**

- 진행 중/예정/종료 상태 자동 분류 규칙

### 2.3 GM 노트 / 개발자 노트 (gm-notes, dev-notes)

**확정**

- GM·운영진 공개 글을 **공지와 동일 파이프라인**으로 처리 (카테고리만 분리)
- 제목에 `[GM]` 등 접두어가 있어도 **원문 제목을 우선** 저장

**향후 결정**

- GM 노트 전용 필터(태그, 작성자 표시) 필요 여부

### 2.4 미디어 (media)

**확정**

- **동영상·트레일러 메타만** 수집: 제목, 설명 요약, 썸네일 URL(외부 CDN 참조), 재생/원문 URL
- 영상 파일·고해상도 이미지 **재호스팅·로컬 저장 금지** (저작권·대역폭)

**향후 결정**

- YouTube/공식 미디어 페이지 등 **허용 도메인 화이트리스트**

---

## 3. 출처 표기 (attribution)

### 확정

- 상세 페이지 상단 또는 본문 직전에:
  - **원문 보기** 링크 (`source_url`, `rel="noopener noreferrer"`, 새 탭)
  - **마지막 반영 시각** (`crawled_at`, KST 표시)
  - **“CLIPS는 비공식 정보 사이트입니다”** 고지 (푸터와 일관)
- JSON-LD `Article` 사용 시 `isBasedOn` 또는 `url`에 원문 연결 (SEO 06 참고)

### 향후 결정

- 퍼블리셔명·로고 표기 방식 (상표 사용 가이드 확인 후)

---

## 4. 중복 방지 (dedup)

### 확정

- **1차 키:** `source_url` UNIQUE (정규화: trailing slash, 쿼리 정렬 규칙은 구현 시 단일 함수로 통일)
- **2차 키:** `source_post_id` + `category` (동일 글이 URL만 바뀐 경우 대비, 향후 마이그레이션)
- Upsert: `ON CONFLICT(source_url) DO UPDATE` — 제목·요약·날짜·해시 갱신, **관리자 고정(`is_pinned`)·수동 숨김은 덮어쓰지 않음**

### 향후 결정

- 제목 유사도 기반 중복 병합(퍼지 매칭) — 오탐 위험으로 초기에는 비활성

---

## 5. 변경 감지 (change detection)

### 확정

- 목록/상세에서 추출한 **본문 발췌 plain text** 또는 핵심 필드(title + published_at + excerpt)로 **SHA-256 `content_hash`** 계산
- 해시 변경 시: `updated_at` 갱신, **관리자 알림(로그·대시보드 배지)** — 향후 이메일/Slack은 선택
- 해시 동일 시: `crawled_at`만 갱신(선택) 또는 skip으로 부하 절감 — **향후 결정** 중 하나를 구현 단계에서 고정

### 향후 결정

- 상세 URL 별도 fetch 도입 여부 (부하·robots와 trade-off)

---

## 6. 실패 재시도 (retries)

### 확정

- HTTP: **timeout 20초**, 카테고리 간 **delay ≥ 1.0초** (기본)
- 일시 오류(429, 502, 503, timeout): **지수 백오프** 최대 3회 (1s → 2s → 4s), 카테고리 단위
- 영구 오류(404, 403, HTML 구조 변경): **로그 + `crawl_run` 실패 기록**, 기존 DB 데이터 유지
- 한 run 전체 실패해도 **이전 스냅샷으로 서비스 지속**

### 향후 결정

- 429 시 `Retry-After` 헤더 존중
- Dead letter 큐(재처리 대기 URL 테이블)

---

## 7. 수집 주기 (schedule)

### 확정

- **자동:** 앱 기동 후 **초기 1회**(지연 3~10초) + **주기 실행**(기본 **1시간**, env로 조정)
- **수동:** 관리자 `POST /admin/crawl/refresh` (CSRF + 확인 UI)
- 스케줄러는 **단일 프로세스** 가정; 다중 worker 시 **중복 run 방지**(DB advisory lock 또는 분산 락) — **향후 결정**이나 운영 전 필수 검토

### 향후 결정

- 공지/이벤트/미디어별 **서로 다른 cron**
- 점검 시간대 crawl 일시 중지

---

## 8. robots.txt 및 이용 정책 준수

### 확정

- 크롤 대상 도메인의 **robots.txt를 주기적으로 확인**하고, `Disallow` 경로는 **요청하지 않음**
- **User-Agent** 문자열에 CLIPS 연락처(향후 `CRAWLER_CONTACT_URL` env) 명시
- 요청 빈도는 **인간적 수준**으로 제한 (delay, 시간당 run 1회 수준)
- 이용약관·커뮤니티 가이드에서 **자동 수집 금지** 명시 시 해당 소스 **즉시 중단**하고 문서·코드에서 소스 비활성화

### 향후 결정

- robots 캐시 TTL
- 공식 **데이터 사용 허가** 협의 시 허용 범위 문서화

---

## 9. 전문 무단 복제 방지

### 확정

- **공식 게시글 HTML 전체·이미지·첨부 파일을 DB에 저장하지 않는다.**
- 허용 저장:
  - `title`, `summary` (~120자 목록용)
  - `excerpt` (~450자 이하 발췌, plain text)
  - 검색용 `content` 필드는 **발췌 수준 텍스트만** (전문 대체 금지)
  - `thumbnail_url`: **외부 URL 참조만** (CDN hotlink, 재업로드 금지)
- 상세 페이지 UX: **요약 + “원문에서 전체 보기”** CTA

### 향후 결정

- 발췌 최대 길이 env 튜닝
- 사용자 제보·위키형 **자체 작성 공략**은 크롤링 정책과 별도 라이선스/출처 정책(7단계)

---

## 10. 요약 및 원문 링크 전략

### 확정

- 목록: `title` + `summary` + `published_at` + 카테고리 배지
- 상세: `excerpt` + 원문 링크 + (선택) 목록에 있던 썸네일
- Open Graph `description`은 summary/excerpt 기반, **원문 URL을 canonical 대체하지 않음** — CLIPS 페이지 canonical은 CLIPS URL, 원문은 `sameAs`/`url` 보조

### 향후 결정

- iframe/embed 공식 플레이어 허용 여부

---

## 11. 관리자 검수 흐름

### 확정

- 크롤 직후 기본 상태: **`published` 또는 `pending_review`** — **향후 결정**하되, 초기에는 `published` + 관리자 **숨김/고정**으로 운영 가능
- 관리자 기능(8단계 문서 연동):
  - 글 **숨김/공개**, **상단 고정**, **제목·요약 수동 수정**(원문 링크는 유지)
  - **수동 크롤 실행** + 최근 run 로그(성공/실패 건수, 소요 시간)
  - 변경 감지 시 **“검수 필요”** 플래그 목록
- 수동 수정 필드는 다음 크롤 upsert에서 **보호** (`manual_override`, `is_hidden`, `is_pinned`)

### 향후 결정

- 신규 글만 pending, 업데이트는 auto-publish
- 2인 승인 워크플로

---

## 12. 아키텍처 개요

### 확정

```
scheduler / admin trigger
    → crawl_service (카테고리별 fetch + parse)
    → normalize (URL, dates, text)
    → dedup + hash
    → repository upsert
    → crawl_run log + admin_audit
```

- 구현 위치(예상): `app/services/crawl_service.py`, `app/repositories/`, `app/models/crawl_run.py`
- 파서는 **소스별 adapter** (`NoticesAdapter`, …)로 분리해 HTML/API 변경 격리

### 향후 결정

- Celery/APScheduler vs asyncio 내장 scheduler
- httpx vs aiohttp

---

## 13. 관측·로깅

### 확정

- run 단위: 시작/종료 시각, 카테고리별 inserted/updated/skipped/failed
- **원문 본문 전체·쿠키·Authorization 헤더는 로그에 남기지 않음**
- 구조 변경 의심 시: 파싱 selector miss 카운트 WARN

### 향후 결정

- Prometheus 메트릭, Sentry 연동

---

## 14. 테스트 (10-testing-strategy.md 연동)

### 확정

- 단위: 날짜 파싱, URL 정규화, hash, upsert 충돌, pinned 보호
- 통합: **저장된 fixture HTML**로 파서 테스트 (실네트워크 CI 금지)
- 관리자: 수동 crawl API는 CSRF·권한 mock

### 향후 결정

- 계약 테스트(recorded HTTP cassette) 도입

---

## 15. 관련 문서

- [03-database-design.md](03-database-design.md) — posts, crawl_runs, sources
- [08-admin-design.md](08-admin-design.md) — 크롤 관리 UI
- [09-security-strategy.md](09-security-strategy.md) — SSRF, rate limit
- [06-seo-strategy.md](06-seo-strategy.md) — Article, canonical

---

## 변경 이력

| 날짜 | 요약 |
|------|------|
| 2026-07-27 | 초안 작성 (1단계 설계) |
