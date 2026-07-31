"""Tests for ops monitoring shell scripts (PATH-mocked; no live host deps)."""

from __future__ import annotations

import gzip
import os
import stat
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKUP_CHECK = ROOT / "scripts" / "check_backup_freshness.sh"
HOST_CHECK = ROOT / "scripts" / "check_host.sh"

GNU_STAT_PY = """#!/usr/bin/env python3
import os
import sys

args = sys.argv[1:]
fmt = None
path = None
i = 0
while i < len(args):
    if args[i] == "-c" and i + 1 < len(args):
        fmt = args[i + 1]
        i += 2
        continue
    path = args[i]
    i += 1
if not path or not fmt:
    sys.exit(1)
st = os.stat(path)
if fmt == "%Y":
    print(int(st.st_mtime))
elif fmt == "%s":
    print(st.st_size)
else:
    sys.exit(2)
"""


def _chmod_x(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_exe(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    _chmod_x(path)


def _run(
    script: Path,
    *,
    env: dict[str, str],
    path_prepend: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **env}
    if path_prepend:
        merged["PATH"] = os.pathsep.join([*(str(p) for p in path_prepend), merged.get("PATH", "")])
    return subprocess.run(
        ["bash", str(script)],
        cwd=ROOT,
        env=merged,
        text=True,
        capture_output=True,
        check=False,
    )


def _install_gnu_stat(bin_dir: Path) -> None:
    _write_exe(bin_dir / "stat", GNU_STAT_PY)


def _make_gzip_archive(path: Path, *, min_file_bytes: int = 2048) -> None:
    """Write a valid .gz whose on-disk size is at least ``min_file_bytes``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload_size = max(min_file_bytes, 4096)
    while True:
        data = gzip.compress(os.urandom(payload_size), compresslevel=1)
        if len(data) >= min_file_bytes:
            path.write_bytes(data)
            return
        payload_size *= 2


@pytest.mark.skipif(not BACKUP_CHECK.is_file(), reason="check_backup_freshness.sh missing")
def test_backup_freshness_ok(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    archive = backup_dir / "2026-07-31_040000.tar.gz"
    _make_gzip_archive(archive, min_file_bytes=4096)
    log_file = tmp_path / "clips-backup.log"
    log_file.write_text("Backup completed successfully\n", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    _install_gnu_stat(bin_dir)

    result = _run(
        BACKUP_CHECK,
        env={
            "BACKUP_DIR": str(backup_dir),
            "MAX_AGE_HOURS": "26",
            "MIN_SIZE_BYTES": "1024",
            "BACKUP_LOG_FILE": str(log_file),
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stdout.startswith("OK backup=")
    assert str(archive) in result.stdout
    assert "size_bytes=" in result.stdout


@pytest.mark.skipif(not BACKUP_CHECK.is_file(), reason="check_backup_freshness.sh missing")
def test_backup_freshness_no_archives(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    bin_dir = tmp_path / "bin"
    _install_gnu_stat(bin_dir)

    result = _run(
        BACKUP_CHECK,
        env={
            "BACKUP_DIR": str(backup_dir),
            "BACKUP_LOG_FILE": str(tmp_path / "missing.log"),
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "no_tar_gz" in result.stderr


@pytest.mark.skipif(not BACKUP_CHECK.is_file(), reason="check_backup_freshness.sh missing")
def test_backup_freshness_too_old(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    archive = backup_dir / "old.tar.gz"
    _make_gzip_archive(archive, min_file_bytes=4096)
    old = time.time() - (40 * 3600)
    os.utime(archive, (old, old))
    bin_dir = tmp_path / "bin"
    _install_gnu_stat(bin_dir)

    result = _run(
        BACKUP_CHECK,
        env={
            "BACKUP_DIR": str(backup_dir),
            "MAX_AGE_HOURS": "26",
            "MIN_SIZE_BYTES": "1024",
            "BACKUP_LOG_FILE": str(tmp_path / "missing.log"),
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "backup_too_old" in result.stderr


@pytest.mark.skipif(not BACKUP_CHECK.is_file(), reason="check_backup_freshness.sh missing")
def test_backup_freshness_too_small(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    archive = backup_dir / "tiny.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(gzip.compress(b"tiny"))
    assert archive.stat().st_size < 1024
    bin_dir = tmp_path / "bin"
    _install_gnu_stat(bin_dir)

    result = _run(
        BACKUP_CHECK,
        env={
            "BACKUP_DIR": str(backup_dir),
            "MAX_AGE_HOURS": "26",
            "MIN_SIZE_BYTES": "1024",
            "BACKUP_LOG_FILE": str(tmp_path / "missing.log"),
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "backup_too_small" in result.stderr


@pytest.mark.skipif(not BACKUP_CHECK.is_file(), reason="check_backup_freshness.sh missing")
def test_backup_freshness_gzip_corrupt(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    archive = backup_dir / "bad.tar.gz"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(b"not-a-gzip-payload" * 100)
    bin_dir = tmp_path / "bin"
    _install_gnu_stat(bin_dir)

    result = _run(
        BACKUP_CHECK,
        env={
            "BACKUP_DIR": str(backup_dir),
            "MAX_AGE_HOURS": "26",
            "MIN_SIZE_BYTES": "1024",
            "BACKUP_LOG_FILE": str(tmp_path / "missing.log"),
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "backup_gzip_corrupt" in result.stderr


@pytest.mark.skipif(not BACKUP_CHECK.is_file(), reason="check_backup_freshness.sh missing")
def test_backup_freshness_missing_log_is_warn_only(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    archive = backup_dir / "ok.tar.gz"
    _make_gzip_archive(archive, min_file_bytes=4096)
    bin_dir = tmp_path / "bin"
    _install_gnu_stat(bin_dir)

    result = _run(
        BACKUP_CHECK,
        env={
            "BACKUP_DIR": str(backup_dir),
            "BACKUP_LOG_FILE": str(tmp_path / "no-such.log"),
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "backup_log_missing" in result.stderr
    assert result.stdout.startswith("OK backup=")


def _install_host_mocks(
    bin_dir: Path,
    *,
    service_state: str = "active",
    http_code: str = "200",
    health_body: str = '{"status":"ok","service":"CLIPS"}',
    disk_pct: int = 40,
    inode_pct: int = 30,
    curl_fail: bool = False,
) -> None:
    _write_exe(
        bin_dir / "systemctl",
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "is-active" ]]; then
  echo "{service_state}"
  exit 0
fi
echo "unexpected systemctl: $*" >&2
exit 2
""",
    )
    health_literal = health_body.replace("'", "'\\''")
    _write_exe(
        bin_dir / "curl",
        f"""#!/usr/bin/env bash
set -euo pipefail
out=""
write_out=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) out="$2"; shift 2 ;;
    --write-out) write_out="$2"; shift 2 ;;
    --silent|--show-error)
      shift
      ;;
    --connect-timeout|--max-time)
      shift
      if [[ $# -gt 0 && "$1" =~ ^[0-9]+$ ]]; then
        shift
      fi
      ;;
    *) shift ;;
  esac
done
if [[ "{int(curl_fail)}" == "1" ]]; then
  echo "000"
  exit 7
fi
if [[ -n "$out" ]]; then
  printf '%s' '{health_literal}' >"$out"
fi
if [[ "$write_out" == "%{{http_code}}" ]]; then
  printf '%s' "{http_code}"
fi
""",
    )
    _write_exe(
        bin_dir / "df",
        f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "-Pi" ]]; then
  printf 'Filesystem Inodes IUsed IFree IUse%% Mounted on\\n'
  printf '/dev/fake 1000 300 700 %s%% /\\n' "{inode_pct}"
  exit 0
fi
if [[ "${{1:-}}" == "-P" ]]; then
  printf 'Filesystem 1024-blocks Used Available Capacity Mounted on\\n'
  printf '/dev/fake 1000 400 600 %s%% /\\n' "{disk_pct}"
  exit 0
fi
echo "unexpected df: $*" >&2
exit 2
""",
    )


@pytest.mark.skipif(not HOST_CHECK.is_file(), reason="check_host.sh missing")
def test_host_check_ok(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_host_mocks(bin_dir)
    result = _run(HOST_CHECK, env={"DISK_PATH": "/"}, path_prepend=[bin_dir])
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stdout.startswith("OK service=clips")
    assert "health=ok" in result.stdout


@pytest.mark.skipif(not HOST_CHECK.is_file(), reason="check_host.sh missing")
def test_host_check_health_fail(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    degraded = '{"status":"degraded","service":"CLIPS"}'
    _install_host_mocks(bin_dir, http_code="503", health_body=degraded)
    result = _run(HOST_CHECK, env={}, path_prepend=[bin_dir])
    assert result.returncode == 1
    assert "health_http_status" in result.stderr


@pytest.mark.skipif(not HOST_CHECK.is_file(), reason="check_host.sh missing")
def test_host_check_health_status_not_ok(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    degraded = '{"status":"degraded","service":"CLIPS"}'
    _install_host_mocks(bin_dir, http_code="200", health_body=degraded)
    result = _run(HOST_CHECK, env={}, path_prepend=[bin_dir])
    assert result.returncode == 1
    assert "health_status_not_ok" in result.stderr


@pytest.mark.skipif(not HOST_CHECK.is_file(), reason="check_host.sh missing")
def test_host_check_disk_critical(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_host_mocks(bin_dir, disk_pct=95)
    result = _run(HOST_CHECK, env={}, path_prepend=[bin_dir])
    assert result.returncode == 1
    assert "disk_critical" in result.stderr


@pytest.mark.skipif(not HOST_CHECK.is_file(), reason="check_host.sh missing")
def test_host_check_disk_warn_exit_zero(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_host_mocks(bin_dir, disk_pct=85, inode_pct=20)
    result = _run(HOST_CHECK, env={}, path_prepend=[bin_dir])
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stdout.startswith("WARN ")
    assert "disk_warn" in result.stdout
