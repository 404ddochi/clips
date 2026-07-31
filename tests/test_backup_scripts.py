"""Smoke tests for scripts/backup.sh and scripts/restore.sh (local mode)."""

from __future__ import annotations

import os
import sqlite3
import stat
import subprocess
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKUP_SH = ROOT / "scripts" / "backup.sh"
RESTORE_SH = ROOT / "scripts" / "restore.sh"


def _run(
    cmd: list[str],
    *,
    env: dict[str, str],
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **env}
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=merged,
        check=check,
        text=True,
        capture_output=True,
    )


def _backup_env(app: Path, backup_dir: Path, **extra: str) -> dict[str, str]:
    env = {
        "APP_ROOT": str(app),
        "BACKUP_DIR": str(backup_dir),
        "LOG_FILE": str(backup_dir / "backup.log"),
        "RETENTION_DAYS": "30",
        # Default RCLONE_ENABLED=true would require a real remote; disable in unit tests.
        "RCLONE_ENABLED": "false",
    }
    env.update(extra)
    return env


def _make_app_root(tmp_path: Path, *, with_uploads: bool = True) -> Path:
    app = tmp_path / "app"
    app.mkdir()
    db = app / "clips.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY);")
    conn.execute("INSERT INTO t DEFAULT VALUES;")
    conn.commit()
    conn.close()
    (app / ".env").write_text("SECRET_KEY=test-secret\nENVIRONMENT=development\n", encoding="utf-8")
    if with_uploads:
        uploads = app / "uploads"
        uploads.mkdir()
        (uploads / "sample.txt").write_text("hello", encoding="utf-8")
    return app


def _install_fake_rclone(bin_dir: Path, *, fail_copy: bool = False) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_path = bin_dir / "rclone-calls.log"
    script = bin_dir / "rclone"
    fail_flag = "1" if fail_copy else "0"
    script.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
echo "$*" >>"{log_path}"
case "${{1:-}}" in
  listremotes)
    echo "gdrive:"
    ;;
  copy)
    if [[ "{fail_flag}" == "1" ]]; then
      echo "fake rclone copy failed" >&2
      exit 17
    fi
    ;;
  delete)
    ;;
  *)
    echo "unexpected rclone args: $*" >&2
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return log_path


@pytest.mark.skipif(not BACKUP_SH.is_file(), reason="backup.sh missing")
def test_backup_script_local_paths(tmp_path: Path) -> None:
    app = _make_app_root(tmp_path)
    backup_dir = tmp_path / "backups"

    result = _run(["bash", str(BACKUP_SH)], env=_backup_env(app, backup_dir))
    assert result.returncode == 0, result.stderr + result.stdout
    archives = list(backup_dir.glob("*.tar.gz"))
    assert len(archives) == 1
    assert (backup_dir / "backup.log").is_file()
    with tarfile.open(archives[0], "r:gz") as tf:
        names = tf.getnames()
    assert "clips-backup/clips.db" in names
    assert "clips-backup/.env" in names
    assert any(n.startswith("clips-backup/uploads/") for n in names)
    assert "skipping Google Drive upload" in result.stdout


@pytest.mark.skipif(not BACKUP_SH.is_file(), reason="backup.sh missing")
def test_backup_continues_without_uploads(tmp_path: Path) -> None:
    app = _make_app_root(tmp_path, with_uploads=False)
    backup_dir = tmp_path / "backups"
    result = _run(["bash", str(BACKUP_SH)], env=_backup_env(app, backup_dir))
    assert result.returncode == 0, result.stderr + result.stdout
    assert "uploads/ missing" in result.stdout or "uploads/ missing" in result.stderr
    assert list(backup_dir.glob("*.tar.gz"))


@pytest.mark.skipif(
    not (BACKUP_SH.is_file() and RESTORE_SH.is_file()),
    reason="backup/restore scripts missing",
)
def test_restore_skip_service_control(tmp_path: Path) -> None:
    app = _make_app_root(tmp_path)
    backup_dir = tmp_path / "backups"
    _run(["bash", str(BACKUP_SH)], env=_backup_env(app, backup_dir))
    archive = next(backup_dir.glob("*.tar.gz"))

    target = tmp_path / "restore-target"
    target.mkdir()
    (target / "clips.db").write_bytes(b"old")
    (target / ".env").write_text("OLD=1\n", encoding="utf-8")
    (target / "uploads").mkdir()
    (target / "uploads" / "old.txt").write_text("old", encoding="utf-8")

    result = _run(
        ["bash", str(RESTORE_SH), str(archive)],
        env={
            "APP_ROOT": str(target),
            "BACKUP_SKIP_SERVICE_CONTROL": "true",
            "LOG_FILE": str(backup_dir / "restore.log"),
        },
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "skipping systemctl" in result.stdout.lower() or "건너뜀" in result.stdout
    assert (target / ".env").read_text(encoding="utf-8").startswith("SECRET_KEY=")
    conn = sqlite3.connect(target / "clips.db")
    assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
    conn.close()
    assert (target / "uploads" / "sample.txt").read_text(encoding="utf-8") == "hello"


@pytest.mark.skipif(not BACKUP_SH.is_file(), reason="backup.sh missing")
def test_backup_fails_when_app_root_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no-such-app"
    backup_dir = tmp_path / "backups"
    result = _run(
        ["bash", str(BACKUP_SH)],
        env=_backup_env(missing, backup_dir),
        check=False,
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "APP_ROOT does not exist" in combined


@pytest.mark.skipif(not BACKUP_SH.is_file(), reason="backup.sh missing")
def test_rclone_copy_and_delete_with_dry_run(tmp_path: Path) -> None:
    app = _make_app_root(tmp_path)
    backup_dir = tmp_path / "backups"
    bin_dir = tmp_path / "bin"
    call_log = _install_fake_rclone(bin_dir)

    result = _run(
        ["bash", str(BACKUP_SH)],
        env=_backup_env(
            app,
            backup_dir,
            RCLONE_ENABLED="true",
            RCLONE_REMOTE="gdrive",
            RCLONE_DESTINATION="CLIPS-Backup",
            RCLONE_DRY_RUN="true",
            PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        ),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "rclone upload success" in result.stdout
    assert list(backup_dir.glob("*.tar.gz"))
    calls = call_log.read_text(encoding="utf-8")
    assert "copy " in calls
    assert "--dry-run" in calls
    assert "delete " in calls
    assert "sync " not in calls
    assert "move " not in calls
    assert "purge " not in calls
    assert "gdrive:CLIPS-Backup" in calls


@pytest.mark.skipif(not BACKUP_SH.is_file(), reason="backup.sh missing")
def test_rclone_failure_keeps_local_backup(tmp_path: Path) -> None:
    app = _make_app_root(tmp_path)
    backup_dir = tmp_path / "backups"
    bin_dir = tmp_path / "bin"
    _install_fake_rclone(bin_dir, fail_copy=True)

    result = _run(
        ["bash", str(BACKUP_SH)],
        env=_backup_env(
            app,
            backup_dir,
            RCLONE_ENABLED="true",
            PATH=f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        ),
        check=False,
    )
    assert result.returncode != 0
    archives = list(backup_dir.glob("*.tar.gz"))
    assert len(archives) == 1
    combined = result.stdout + result.stderr
    assert "rclone copy failed" in combined
    assert "Local backup retained" in combined
