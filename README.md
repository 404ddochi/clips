# CLIPS (클립스)

**CLIPS**는 MMORPG **이클립스: 더 어웨이크닝(Eclipse: The Awakening)**의 공지, 이벤트, 클래스, 콘텐츠, 공략, 아이템, 보스, 지도, 쿠폰 등 게임 정보를 모아 제공하는 **비공식** 정보 플랫폼입니다.

> 본 프로젝트는 공식 서비스가 아닙니다. 게임명 및 관련 자산은 각 권리자에게 귀속됩니다.

## 기술 스택

| 구분 | 기술 |
|------|------|
| 백엔드 | Python 3.13+, FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, Pydantic Settings |
| 템플릿 | Jinja2 (SSR) |
| DB (로컬) | SQLite |
| DB (운영 예정) | PostgreSQL |
| 테스트/품질 | pytest, httpx, BeautifulSoup4, Ruff, mypy, pre-commit |

## 현재 UI

- **메인 (`/`):** Information First — 히어로, Information Strip, 최신 소식, 빠른 메뉴, 플랫폼, 아카이브, CTA
- **소식 (Mock):** `/news`, `/news/notices`, `/news/events`, `/news/patch-notes` (+ 상세 slug)
- **쿠폰 (Mock):** `/coupons`, `/coupons/{slug}` — SAMPLE/CLIPS-DEMO 데모 코드만
- **준비 중:** `/classes`, `/contents`, `/items`, `/bosses`, `/maps`, `/guides`
- **디자인 시스템:** `/dev/design-system` — local/development 전용 CDL 쇼케이스 (`noindex`)
- **테마:** Eclipse(다크) / Dawn(라이트) / System — 헤더에서 전환, `localStorage`
- **API/SEO:** `/health`, `/robots.txt`, `/sitemap.xml` (Mock 정보 페이지는 noindex, sitemap 제외)
- **CDL 문서:** [docs/13-clips-design-language.md](docs/13-clips-design-language.md)
- **테마 문서:** [docs/14-theme-system.md](docs/14-theme-system.md)
- **정보 페이지:** [docs/15-information-pages.md](docs/15-information-pages.md)
- **디자인 철학:** [docs/design-philosophy.md](docs/design-philosophy.md) — Find Faster. Read Less. Play More.

## 요구 환경

- macOS 또는 Linux
- Python **3.13 이상**
- (권장) `git`, `curl`

## 시작하기

프로젝트 루트(`clips/`)에서 다음을 실행합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

### 환경변수

`.env.example`을 복사한 뒤 필요 시 값을 수정합니다. `.env`는 Git에 포함하지 않습니다.

주요 변수:

- `APP_BASE_URL` — canonical, sitemap, Open Graph 절대 URL 생성에 사용
- `DATABASE_URL` — SQLAlchemy 연결 문자열
- `SECRET_KEY` — 운영 환경에서는 반드시 변경 (기본값 `change-me`는 운영에서 시작 차단)

### 개발 서버 실행

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

또는 (가상환경 활성화 후):

```bash
./scripts/dev.sh
```

브라우저: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 테스트

```bash
./scripts/test.sh
# 또는
pytest
```

### Ruff / mypy

```bash
ruff check app tests
ruff format app tests
mypy app
```

한 번에:

```bash
./scripts/lint.sh
```

스크립트 실행 권한이 없다면:

```bash
chmod +x scripts/*.sh
```

### Alembic

```bash
# 마이그레이션 생성 (모델 추가 후)
alembic revision --autogenerate -m "describe change"

# 적용
alembic upgrade head
```

현재 단계에서는 ORM 모델이 없어 autogenerate 결과가 비어 있을 수 있습니다.

### pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

## 디렉터리 구조 (요약)

```
clips/
├── app/           # FastAPI 애플리케이션 (routers, templates, static, core)
├── alembic/       # DB 마이그레이션
├── docs/          # 설계 문서
├── scripts/       # dev / test / lint 스크립트
└── tests/         # pytest
```

자세한 설명은 [docs/02-directory-structure.md](docs/02-directory-structure.md)를 참고하세요.

## 문서

| 문서 | 설명 |
|------|------|
| [00-project-overview.md](docs/00-project-overview.md) | 프로젝트 개요 |
| [01-architecture.md](docs/01-architecture.md) | 아키텍처 |
| [05-ui-design-system.md](docs/05-ui-design-system.md) | UI 시스템 개요 |
| [13-clips-design-language.md](docs/13-clips-design-language.md) | **CDL 단일 기준** |
| [14-theme-system.md](docs/14-theme-system.md) | Dual Theme (Eclipse/Dawn) |
| [15-information-pages.md](docs/15-information-pages.md) | 소식·쿠폰 Mock 정보 페이지 |
| [design-philosophy.md](docs/design-philosophy.md) | CLIPS Design Philosophy |
| [06-seo-strategy.md](docs/06-seo-strategy.md) | SEO 전략 |
| [12-development-roadmap.md](docs/12-development-roadmap.md) | 로드맵 |
| [backup-restore.md](docs/backup-restore.md) | **운영 백업·복구** |

전체 목록은 `docs/` 디렉터리를 참고하세요.

## 운영 백업 (요약)

운영 서버에서는 `scripts/backup.sh`로 `clips.db` · `uploads/` · `.env`를  
`/backup/clips/YYYY-MM-DD_HHMMSS.tar.gz`에 보관한 뒤, rclone으로 Google Drive
(`gdrive:CLIPS-Backup`)에 **copy** 업로드하고, 로컬·원격 모두 30일 지난 `*.tar.gz`를 정리합니다.

```bash
# 운영 수동 백업 (로컬 + Google Drive)
sudo /var/www/clips/scripts/backup.sh

# 운영 복구 (로컬 아카이브 기준; restore.sh 변경 없음)
sudo /var/www/clips/scripts/restore.sh /backup/clips/2026-07-30_040001.tar.gz
```

### Google Drive 자동 업로드

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `RCLONE_ENABLED` | `true` | `false`면 업로드 건너뜀 |
| `RCLONE_REMOTE` | `gdrive` | rclone remote 이름 |
| `RCLONE_DESTINATION` | `CLIPS-Backup` | Drive 폴더 |
| `RCLONE_DRY_RUN` | `false` | `true`면 rclone에 `--dry-run` |

**주의:** rclone 설정이 들어 있는 계정과 cron/수동 실행 계정이 **같아야** 합니다.  
root crontab이면 root의 `~/.config/rclone/rclone.conf`를 사용합니다.

```bash
# 업로드만 끄고 로컬 백업만
sudo RCLONE_ENABLED=false /var/www/clips/scripts/backup.sh

# 실제 전송 없이 rclone dry-run
sudo RCLONE_DRY_RUN=true /var/www/clips/scripts/backup.sh

# 원격 확인
sudo rclone lsf gdrive:CLIPS-Backup
```

### 운영 cron 예시 (매일 04:00, root)

```cron
0 4 * * * /var/www/clips/scripts/backup.sh >>/var/log/clips-backup.log 2>&1
```

### 로컬 백업 테스트

프로젝트 루트에서 (`.local-backups/`는 gitignore됨).  
로컬에 rclone remote가 없으면 업로드를 끕니다:

```bash
APP_ROOT="$PWD" \
BACKUP_DIR="$PWD/.local-backups" \
LOG_FILE="$PWD/.local-backups/backup.log" \
RETENTION_DAYS=30 \
RCLONE_ENABLED=false \
./scripts/backup.sh
```

### 로컬 복구 테스트 (주의)

복구는 `APP_ROOT`의 `clips.db` / `.env` / `uploads`를 **덮어씁니다.**  
**실제 프로젝트 디렉터리에서 복구하지 마세요.** 반드시 별도 임시 디렉터리에서 검증하세요.

```bash
# 1) 위에서 만든 아카이브 경로 확인
ls -la .local-backups/*.tar.gz

# 2) 임시 대상에만 복구
RESTORE_ROOT="$(mktemp -d /tmp/clips-restore-XXXXXX)"
mkdir -p "$RESTORE_ROOT"
# 대상이 비어 있어도 APP_ROOT 디렉터리는 존재해야 함
APP_ROOT="$RESTORE_ROOT" \
BACKUP_SKIP_SERVICE_CONTROL=true \
LOG_FILE="$PWD/.local-backups/restore.log" \
./scripts/restore.sh "$PWD/.local-backups/백업파일명.tar.gz"

# 3) 확인 후 임시 디렉터리 삭제
ls -la "$RESTORE_ROOT"
rm -rf "$RESTORE_ROOT"
```

cron·rclone 상세는 [docs/backup-restore.md](docs/backup-restore.md)를 참고하세요.

## Git 초기화

원격 저장소는 직접 연결하지 않았습니다. 로컬에서 초기 커밋 예시:

```bash
git init
git add .
git commit -m "chore: initialize CLIPS project"
```

(`create_project`로 이미 Git이 초기화되어 있을 수 있습니다.)

## 라이선스 및 고지

- 소스 코드: [MIT License](LICENSE)
- **CLIPS는 비공식 팬 정보 사이트**이며, 공식 퍼블리셔·운영사와 무관합니다.
