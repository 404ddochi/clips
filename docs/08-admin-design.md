# 08. 관리자 설계

CLIPS 관리자 영역은 **콘텐츠·크롤·SEO·운영 설정**을 안전하게 다루기 위한 **별도 URL 네임스페이스**(`/admin/*`)로 제공한다. 본 문서는 인증, 권한, 메뉴, 감사, 삭제 정책을 정의한다.

**범례:** **확정** / **향후 결정**

---

## 1. 설계 목표

### 확정

- 관리 기능은 **인증된 관리자만** 접근
- 모든 **상태 변경·삭제·크롤 실행**은 **감사 로그**에 남김
- 공개 SSR 페이지와 **템플릿·정적 자산 분리**(관리자 전용 레이아웃)
- CSRF·세션·Rate limit은 [09-security-strategy.md](09-security-strategy.md) 준수

### 향후 결정

- 다중 테넌트·외부 편집자 초대
- 2FA(TOTP)

---

## 2. 인증 (auth)

### 확정

- **세션 기반** 로그인 (서버 사이드 세션 ID, HttpOnly 쿠키)
- 라우트:
  - `GET /admin/login` — 로그인 폼
  - `POST /admin/login` — 자격 증명 검증
  - `POST /admin/logout` — 세션 폐기 (**CSRF 필수**)
  - `GET /admin/logout` — **세션 변경 없음**, dashboard 또는 login으로 redirect만 (GET CSRF 우회 방지)
- 로그인 실패: 동일 IP **5회 / 10분** 임시 차단 (앱 메모리; 운영 Nginx `limit_req` 병행 권장)
- 운영 쿠키: `Secure`, `SameSite=Lax`, `Path=/admin` 또는 `/` — **향후 결정** (Path=/admin 권장)

### 향후 결정

- `ADMIN_SESSION_MAX_AGE_SECONDS` (기본 8시간)
- idle timeout
- Redis 세션 저장 (다중 worker)

### 환경변수 (예정)

| 변수 | 용도 | 상태 |
|------|------|------|
| `ADMIN_USERNAME` | 초기 관리자 ID | 향후 결정 |
| `ADMIN_PASSWORD_HASH` | bcrypt/argon2 해시 | 향후 결정 |
| `ADMIN_SESSION_MAX_AGE_SECONDS` | 세션 수명 | 향후 결정 |

초기 3단계에서는 **DB `admin_users` 테이블** + bcrypt를 **확정** 방향으로 설계 ([03-database-design.md](03-database-design.md)).

---

## 3. 역할 (roles)

### 확정

| 역할 | 코드 | 권한 |
|------|------|------|
| 최고 관리자 | `superadmin` | 전 기능 + 계정·설정 |
| 콘텐츠 편집 | `editor` | 게시물·배너·쿠폰·SEO 메타 |
| 운영 | `operator` | 크롤 실행·로그 조회·배너 ON/OFF |
| 읽기 전용 | `viewer` | 대시보드·로그 조회만 |

- 역할은 **RBAC** — 라우트/액션마다 `require_role("editor")` 의존성
- **최소 1명 superadmin** 유지

### 향후 결정

- 커스텀 역할·permission 세트
- API 토큰(기계 계정) for cron

---

## 4. 메뉴 구조

### 확정 (IA)

```
/admin/dashboard          대시보드 (요약, 최근 감사, 크롤 상태)
/admin/posts              게시물 (공지·이벤트·업데이트·GM)
/admin/crawl              크롤 관리 (소스, 수동 실행, run 이력)
/admin/banners            배너·팝업
/admin/coupons            쿠폰
/admin/seo                SEO (robots/sitemap 재생성, 메타 프리셋)
/admin/media              미디어 메타 (링크형)
/admin/audit-logs         감사 로그
/admin/activity           사용자 활동 (공개 API 집계)
/admin/settings           사이트 설정 (APP_BASE_URL 검증 등)
/admin/users              관리자 계정 (superadmin)
```

- 공통: 좌측 네비(데스크톱), 상단 햄버거(모바일), **현재 환경 배지** (local/staging/prod)
- Breadcrumb: `관리자 > 게시물 > 수정`

### 향후 결정

- 클래스·아이템·보스 DB 편집 메뉴 (6단계 이후 `/admin/game-data/*`)

---

## 5. 게시물 관리 (content)

### 확정

- CRUD: 제목, summary, excerpt, category, published_at, source_url, 공개/숨김, 고정
- **크롤링 글:** `source_url` 변경 불가(삭제 후 재등록만), `manual_override` 시 upsert 스킵 필드 표시
- 목록: 필터(category, status, keyword), 페이지네이션(20), 정렬(최신·고정 우선)
- WYSIWYG **미사용** — plain textarea + 미리보기(escape)로 XSS 완화
- 일괄: 숨김/공개, (superadmin) soft delete

### 향후 결정

- Markdown 지원
- 예약 발행

---

## 6. 크롤링 관리

### 확정

- 소스 ON/OFF, 마지막 성공/실패 시각, 다음 예정 run
- `POST /admin/crawl/refresh` — CSRF + `data-confirm` 확인
- run 상세: 카테고리별 통계, 에러 메시지(스택 트레이스 **관리자에게만**, 공개 노출 금지)
- [07-crawling-strategy.md](07-crawling-strategy.md) 정책 링크 고정

### 향후 결정

- 소스별 adapter 설정 UI (selector JSON)
- dry-run 모드

---

## 7. 배너 관리

### 확정

- 필드: 제목(내부), 이미지 URL 또는 업로드, 링크 URL, 노출 기간, `is_active`, sort_order
- **홈/특정 페이지 슬롯** enum (`hero`, `sidebar`, `popup`)
- 팝업: `frequency` (session/day), `dismissible`

### 향후 결정

- A/B 테스트
- 업로드 vs 외부 URL only (초기는 placeholder + URL **확정** 가능)

---

## 8. 쿠폰 관리

### 확정

- 코드, 설명, 보상 요약, `starts_at`/`ends_at`, `is_active`, source_url(선택)
- 만료 쿠폰 자동 `is_active=false` (일 배치 또는 조회 시 lazy)
- 공개 페이지는 **활성만** 노출; 관리자는 전체

### 향후 결정

- 코드 마스킹(부분만 공개)
- 사용자 제보 쿠폰 승인 큐

---

## 9. SEO 관리

### 확정

- 페이지별 override: title, description, robots, og_image (DB `seo_overrides` 또는 posts 확장)
- **sitemap/robots 재생성** 트리거 (캐시 bust는 APP_BASE_URL 기준)
- noindex 일괄(검색 결과, admin, 준비 중 페이지) — [06-seo-strategy.md](06-seo-strategy.md)와 일치

### 향후 결정

- Search Console API 연동
- structured_data JSON 편집 (고급)

---

## 10. 사용자 활동 로그 (activity)

### 확정

- **익명·집계** 중심: 페이지뷰, 검색어(정규화), 404 URL top N
- **PII 최소화** — IP 전체 저장 지양, /24 해시 또는 미저장
- 보관: **90일** 기본 prune (job)

### 향후 결정

- 로그인 사용자(향후 커뮤니티) 활동 분리
- GDPR/개인정보처리방침 연동 문구

---

## 11. 감사 로그 (audit)

### 확정

- 테이블 `admin_audit_logs`: `id`, `admin_user_id`, `action`, `target_type`, `target_id`, `detail`(JSON), `ip`, `created_at`
- 기록 대상:
  - 로그인 성공/실패/차단, 로그out
  - 게시물·배너·쿠폰 CRUD
  - 크롤 수동 실행, SEO 재생성
  - 관리자 계정 변경
- **기록 금지:** 비밀번호, CSRF 토큰, 세션 ID, `.env` 값
- UI: `/admin/audit-logs` — action, target_type, keyword, days, limit 필터
- 보관 **180일** — `prune_old_admin_audit_logs` + 일일 03:00 KST job (**향후 결정** cron, 원칙만 확정)

---

## 12. 삭제 및 복구

### 확정

- 게시물·배너·쿠폰: **soft delete** (`deleted_at`, `deleted_by`)
- superadmin: **복구** (deleted_at NULL), **영구 삭제**(hard) — 확인 문구 2단계
- 크롤 원본 연동 글 soft delete 시 **다음 crawl이 자동 resurrect 하지 않음** (`is_hidden` 또는 `manual_deleted` 플래그)
- 감사 로그·활동 로그는 **삭제 불가**(prune만)

### 향후 결정

- 휴지통 UI retention (30일)
- DB backup에서 point-in-time 복구 절차 ([11-deployment-strategy.md](11-deployment-strategy.md))

---

## 13. UI/UX 원칙

### 확정

- 관리자도 **다크 테마**·CLIPS 토큰 공유 ([05-ui-design-system.md](05-ui-design-system.md))
- 파괴적 액션: primary danger + confirm modal
- flash 메시지: success/error, XSS escape
- 테이블: 키보드 포커스, form label 필수

### 향후 결정

- HTMX partial vs full page POST

---

## 14. API 형태

### 확정

- 관리자는 **HTML form + redirect** 우선 (SSR 일관)
- JSON API는 **향후** `/admin/api/v1/*` — CSRF 또는 Bearer 분리

---

## 15. 구현 단계 매핑

| 로드맵 | 관리자 범위 |
|--------|-------------|
| 3단계 | login, dashboard 골격, audit 기본 |
| 4단계 | posts CRUD |
| 5단계 | crawl 관리 |
| 6~7단계 | game-data, community moderation |
| 8단계 | SEO admin 고도화 |

---

## 변경 이력

| 날짜 | 요약 |
|------|------|
| 2026-07-27 | 초안 작성 |
