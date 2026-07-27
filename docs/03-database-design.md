# CLIPS 데이터베이스 설계

## 개요

CLIPS는 게임 정보·운영·SEO·크롤링을 **도메인 단위 테이블**로 분리합니다. ORM 베이스(`app/database.py`의 `Base`)와 Alembic은 **확정**이며, 아래 테이블 정의는 **스키마 설계(구현 진행 중)** 입니다. 컬럼 타입은 PostgreSQL 기준으로 기술하고, SQLite 호환을 위해 JSON·ENUM은 SQLAlchemy 추상 타입으로 매핑합니다.

### 공통 컬럼(확정)

대부분의 콘텐츠·마스터 테이블:

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | BIGINT PK | surrogate key |
| `slug` | VARCHAR(120) UNIQUE | URL-safe, SEO |
| `status` | ENUM | `draft`, `published`, `archived` |
| `created_at` | TIMESTAMPTZ | 생성 |
| `updated_at` | TIMESTAMPTZ | 수정 |
| `published_at` | TIMESTAMPTZ NULL | 공개 시각 |

---

## 확정

### 설계 원칙

1. **출처(source) 분리**: 공식·비공식 출처 URL과 크롤 메타는 `source`, `crawl_log`에 집중.
2. **slug 기반 URL**: 상세 페이지 `/classes/{slug}` 형태와 1:1.
3. **soft delete**: `status=archived` 우선; hard delete는 관리자·GDPR 대응 시만.
4. **한국어 기본**: `title_ko`, `body_ko` 필드명 또는 단일 `locale` row per entity — **향후 결정** (아래 다국어 절).

---

## 도메인별 설계

### user (회원·인증)

**책임**: 선택적 회원 기능(북마크, 알림, UGC). MVP에서는 **미구현 가능**.

| 컬럼 | 설명 |
|------|------|
| `email` | UNIQUE, nullable until OAuth |
| `password_hash` | nullable (OAuth only user) |
| `display_name` | 표시명 |
| `role` | `user`, `moderator`, `admin` |
| `is_active` | bool |
| `last_login_at` | |

**관계**: `bookmark` → guide/video (향후), `admin_audit` actor FK.

---

### admin (운영·감사)

**책임**: 관리자 계정은 `user.role=admin`으로 통합하거나 별도 `admin_user` — **향후 결정**.

| 테이블 | 책임 |
|--------|------|
| `admin_audit_log` | `actor_id`, `action`, `entity_type`, `entity_id`, `payload_json`, `ip` |

---

### notice (공지)

**책임**: 공식 공지 아카이브·요약·링크.

| 컬럼 | 설명 |
|------|------|
| `title` | |
| `summary` | SEO description 후보 |
| `body_html` | sanitized HTML 또는 markdown 렌더 결과 |
| `official_url` | canonical 대체 아님 — **원문 링크** |
| `source_id` | FK → source |
| `notice_type` | `maintenance`, `general`, `urgent` |
| `posted_at` | 공식 게시일 |

**관계**: N:1 `source`. M:N `tag` (향후).

---

### event (이벤트)

**책임**: 기간型 이벤트, 보상 요약.

| 컬럼 | 설명 |
|------|------|
| `title`, `summary`, `body_html` | |
| `starts_at`, `ends_at` | |
| `event_kind` | `ingame`, `web`, `collab` |
| `official_url`, `source_id` | |
| `banner_image_url` | OG 보조 |

**관계**: optional FK → `banner` (프로모션 슬롯).

---

### update (패치·업데이트)

**책임**: 패치 노트 버전별 정리.

| 컬럼 | 설명 |
|------|------|
| `version` | e.g. `1.2.3` |
| `title` | |
| `summary` | 한 줄 패치 요약 |
| `body_html` | 변경 목록 |
| `released_at` | |
| `official_url`, `source_id` | |

**관계**: 1:N `update_change_item` (category, description) — **향후 결정**(JSON vs 자식 테이블).

---

### class (클래스·직업)

**책임**: playable class 마스터.

| 컬럼 | 설명 |
|------|------|
| `name_ko`, `name_en` | |
| `role` | tank, dps, support, hybrid |
| `description` | |
| `icon_url` | |
| `sort_order` | |

**관계**: 1:N `skill`, M:N `guide` (recommended).

---

### skill (스킬)

**책임**: 클래스별 스킬·레벨 정보.

| 컬럼 | 설명 |
|------|------|
| `class_id` | FK |
| `name_ko` | |
| `skill_type` | active, passive, ultimate |
| `cooldown_sec`, `mana_cost` | nullable — 데이터 출처 명시 |
| `description` | |
| `max_level` | |
| `source_id` | 공식 툴팁 출처 |

**관계**: N:1 `class`, N:1 `source`.

---

### item (아이템)

**책임**: 장비·소모품·재료.

| 컬럼 | 설명 |
|------|------|
| `name_ko` | |
| `item_type` | weapon, armor, material, consumable |
| `grade` | common ~ legendary (게임 정의 따름) |
| `description` | |
| `icon_url` | |
| `stack_max` | |
| `tradable` | bool |

**관계**: M:N `boss` (drop), M:N `region` (gather), FK `source`.

---

### boss (보스)

**책임**: 보스·레이드 대상.

| 컬럼 | 설명 |
|------|------|
| `name_ko` | |
| `boss_type` | field, dungeon, raid |
| `level` | recommended level |
| `hp`, `phases` | JSON 또는 normalized phase table |
| `description` | |
| `image_url` | |

**관계**: M:N `item` (drop table), M:N `map` (spawn), 1:N `guide`.

---

### region (지역)

**책임**: 월드 지역·챕터.

| 컬럼 | 설명 |
|------|------|
| `name_ko` | |
| `region_type` | continent, zone, dungeon |
| `parent_id` | self FK (계층) |
| `level_min`, `level_max` | |
| `description` | |

**관계**: 1:N `map`, M:N `item` (local drops).

---

### map (맵·좌표)

**책임**: 인터랙티브 맵 핀·채집 위치(향후).

| 컬럼 | 설명 |
|------|------|
| `region_id` | FK |
| `name_ko` | |
| `map_image_url` | |
| `width`, `height` | 픽셀 기준 |
| `meta_json` | pins, layers |

**관계**: N:1 `region`.

---

### guide (공략)

**책임**: 에디토리얼·팬 작성 공략.

| 컬럼 | 설명 |
|------|------|
| `title` | |
| `summary` | |
| `body_html` | |
| `author_name` | 또는 `user_id` |
| `guide_type` | beginner, class, boss, patch |
| `view_count` | denormalized — `view_stats`와 동기 |

**관계**: M:N `class`, `boss`, `tag`.

---

### coupon (쿠폰)

**책임**: 프로모 코드·유효기간.

| 컬럼 | 설명 |
|------|------|
| `code` | |
| `reward_summary` | |
| `starts_at`, `expires_at` | |
| `official_url` | |
| `is_active` | |

**관계**: FK `source`.

---

### video (영상)

**책임**: YouTube 등 외부 embed 메타.

| 컬럼 | 설명 |
|------|------|
| `platform` | youtube, twitch |
| `external_id` | |
| `title` | |
| `channel_name` | |
| `published_at` | |
| `thumbnail_url` | |

**관계**: M:N `guide`, `boss` (관련 콘텐츠).

---

### banner (배너)

**책임**: 홈·섹션 프로모 슬롯.

| 컬럼 | 설명 |
|------|------|
| `title` | |
| `image_url` | |
| `link_url` | |
| `placement` | home_hero, sidebar |
| `starts_at`, `ends_at` | |
| `sort_order` | |

---

### faq

**책임**: 정적 FAQ SSR·FAQPage JSON-LD.

| 컬럼 | 설명 |
|------|------|
| `question` | |
| `answer_html` | |
| `category` | |
| `sort_order` | |

---

### search_term (검색어 통계)

**책임**: 내부 검색 로그·인기 검색어.

| 컬럼 | 설명 |
|------|------|
| `term` | normalized |
| `hit_count` | |
| `last_searched_at` | |
| `result_count_avg` | 품질 모니터 |

**관계**: standalone; 집계 테이블 `search_term_daily` — **향후 결정**.

---

### view_stats (조회 통계)

**책임**: 페이지뷰·unique visitor 근사.

| 컬럼 | 설명 |
|------|------|
| `entity_type` | guide, notice, class, … |
| `entity_id` | |
| `view_date` | date |
| `views` | |
| `unique_visitors` | salted hash 기반 — **향후 결정** |

**인덱스**: `(entity_type, entity_id, view_date)` UNIQUE.

---

### crawl_log (크롤 로그)

**책임**: 크롤러 실행·성공/실패·지연.

| 컬럼 | 설명 |
|------|------|
| `source_id` | FK |
| `started_at`, `finished_at` | |
| `status` | success, partial, failed |
| `http_status` | |
| `items_created`, `items_updated` | |
| `error_message` | text |
| `payload_hash` | 변경 감지 |

---

### source (출처)

**책임**: 공식 사이트·포럼·위키 등 메타.

| 컬럼 | 설명 |
|------|------|
| `name` | e.g. official_notice |
| `base_url` | |
| `source_kind` | official, community, internal |
| `crawl_enabled` | bool |
| `crawl_config_json` | selectors, rate limit |
| `last_success_at` | |

**관계**: 1:N notice, event, update, crawl_log.

---

## ER 개요 (논리)

```
source ──< notice, event, update, crawl_log
class ──< skill
region ──< map
class ──< guide >── boss
boss ──< drop >── item
region ──< item (gather)
view_stats ── entity (polymorphic)
```

---

## 인덱스·성능 (확정 방향)

- 모든 `slug` UNIQUE + `status=published` partial index (PostgreSQL).
- 목록: `(published_at DESC)` on notice, event, update.
- FK columns indexed by default.

---

## 향후 결정

| 항목 | 선택지 |
|------|--------|
| 다국어 | row per locale vs JSONB translations |
| Full-text search | PostgreSQL `tsvector` vs Meilisearch |
| `tag` / `category` | 통합 taxonomy 테이블 |
| `build` / loadout | 유저 빌드 공유 |
| `price` / market | 경매장 시세 (API 없으면 보류) |
| 이미지 저장 | DB URL only vs S3/R2 upload |
| `revision` | guide/version history 테이블 |

---

## 마이그레이션 운영

- **확정**: Alembic revision은 PR 단위; production은 `upgrade head` 전 백업.
- SQLite → PostgreSQL 이전 시 `DATABASE_URL`만 교체 + migration replay.

---

## 관련 문서

- [04-api-design.md](./04-api-design.md)
- [01-architecture.md](./01-architecture.md)
