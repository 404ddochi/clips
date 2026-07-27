# CLIPS 디렉터리 구조

## 개요

저장소 루트(`/Users/leehyeongcheol/Desktop/clips`) 기준 폴더 역할, **의존성 방향**, 기능 추가 절차, 피해야 할 패턴을 정리합니다.

---

## 확정

### 루트 레이아웃

```
clips/
├── app/                 # 애플리케이션 패키지 (배포 단위)
├── alembic/             # DB 마이그레이션
├── alembic.ini
├── docs/                # 프로젝트 문서 (본 디렉터리)
├── scripts/             # dev/lint/test 셸 스크립트
├── tests/               # pytest
├── pyproject.toml
├── .env.example
└── LICENSE
```

### `app/` 상세

| 경로 | 역할 |
|------|------|
| `main.py` | FastAPI factory, lifespan, static mount, exception handlers |
| `config.py` | Pydantic Settings, `absolute_url()`, production validation |
| `database.py` | Engine, SessionLocal, `Base`, `get_db()` |
| `dependencies.py` | Jinja templates, `seo_context()` |
| `routers/` | HTTP 라우트 (web, seo, health; 향후 admin, api, crawler) |
| `services/` | 비즈니스·SEO·집계 로직 |
| `repositories/` | DB 접근 (향후 도메인별 모듈) |
| `models/` | SQLAlchemy ORM (향후) |
| `schemas/` | Pydantic models (향후 API) |
| `core/` | constants, middleware, logging, security, exceptions |
| `templates/` | Jinja2 (base, components, pages, errors) |
| `static/` | css/js/images/favicon — CDN 친화적 경로 |

### `templates/` 규칙

- `base.html`: 공통 `<html>`, CSS 링크, `{% block content %}`
- `components/`: header, footer, seo_meta, empty_state — **재사용 조각**
- 페이지별 템플릿: `home.html`, `preparing.html`, `errors/*`
- SEO 메타는 **`seo_context()` 키**와 `components/seo_meta.html` 계약을 따름

### `static/css/` 계층 (확정)

```
reset.css → tokens.css → base.css → layout.css → components.css → pages/*.css
```

디자인 토큰은 **`tokens.css` 단일 소스** (`05-ui-design-system.md` 참조).

### `tests/`

- `conftest.py`: TestClient, settings override 패턴
- `test_health.py`, `test_home.py`: 스모크·SEO 메타 존재 여부

### `scripts/`

- `dev.sh`, `lint.sh`, `test.sh`: 로컬 워크플로우 (CI에서 동일 명령 재사용 권장)

### 의존성 방향

```
routers  →  services  →  repositories  →  models
   ↓            ↓
dependencies   core (constants, exceptions)
   ↓
templates / static (데이터는 router/service가 주입)
```

**금지(확정)**:

- `models` → `routers`
- `repositories` → `templates`
- `core` → `services`

### 새 기능 추가 절차 (체크리스트)

1. **도메인 정의**: `03-database-design.md`에 테이블·관계 반영(또는 기존 도메인 확장).
2. **Model + Alembic revision**: `app/models/`, `alembic revision --autogenerate`.
3. **Repository**: 목록·상세·slug 조회, 페이지네이션.
4. **Service**: 권한·가시성·SEO title/description 생성.
5. **Schema** (API/폼 필요 시): 입력 검증.
6. **Router**: `web.py` 또는 `routers/admin.py` 등 — **한 라우터 = 한 관심사**.
7. **Template + CSS**: `pages/` 전용 스타일은 `static/css/pages/`에만.
8. **SEO**: `seo_context`, sitemap 경로 목록(`SITEMAP_PUBLIC_PATHS` 또는 DB driven), JSON-LD 타입 선택.
9. **Test**: 최소 1개 integration (200, canonical, h1 존재).
10. **Docs**: API·DB 문서 해당 절 업데이트.

### 라우터 분할 가이드 (확정 방향)

| 파일 | prefix | 용도 |
|------|--------|------|
| `web.py` | `/` | 공개 SSR |
| `seo.py` | `/robots.txt`, `/sitemap.xml` | 크롤러 |
| `health.py` | `/health` | probes |
| `admin.py` (향후) | `/admin` | SSR 또는 API |
| `api/internal.py` (향후) | `/api/v1` | JSON for HTMX/미래 클라이언트 |
| `api/crawler.py` (향후) | `/api/crawler/v1` | HMAC·토큰 보호 |

---

## 향후 결정

- `app/domain/` **DDD 스타일** 패키지로 services+repos+models 묶기 여부
- 프론트 빌드 도구(Vite) 도입 vs 순수 static
- `frontend/` 분리 monorepo 여부
- i18n: `templates/locales/` vs gettext

---

## 안티패턴

| 안티패턴 | 문제 | 대안 |
|----------|------|------|
| Router에서 raw SQL | 테스트·재사용 불가 | Repository |
| Template 안 비즈니스 분기 | SEO·로직 분산 | Service + context |
| 전역 mutable settings | race, 테스트 오염 | `get_settings()` only |
| 섹션마다 inline CSS | 디자인 드리프트 | tokens + components |
| placeholder 페이지 `index` | thin content 패널티 | `noindex, follow`(현재 preparing) |
| sitemap에 미구현 URL 대량 등록 | Crawl budget 낭비 | publish 플래그 후만 loc 추가 |
| `SECRET_KEY` 커밋 | 보안 사고 | `.env`, `.env.example`만 |

---

## 관련 문서

- [01-architecture.md](./01-architecture.md)
- [04-api-design.md](./04-api-design.md)
- [05-ui-design-system.md](./05-ui-design-system.md)
