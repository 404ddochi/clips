"""Tests for Discord notify + monitor wrapper scripts (PATH-mocked; no live Discord)."""

from __future__ import annotations

import os
import re
import stat
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTIFY = ROOT / "scripts" / "notify_discord.sh"
RUN_CHECK = ROOT / "scripts" / "run_monitor_check.sh"
RUN_HOST = ROOT / "scripts" / "run_host_monitor.sh"
RUN_BACKUP = ROOT / "scripts" / "run_backup_monitor.sh"

FAKE_WEBHOOK = "https://discord.example.invalid/api/webhooks/123/TESTTOKEN"


def _chmod_x(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_exe(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    _chmod_x(path)


def _run(
    script: Path,
    args: list[str] | None = None,
    *,
    env: dict[str, str],
    path_prepend: list[Path] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **env}
    # Avoid leaking a real webhook from the developer shell into tests.
    merged.setdefault("DISCORD_WEBHOOK_URL", "")
    if path_prepend:
        merged["PATH"] = os.pathsep.join([*(str(p) for p in path_prepend), merged.get("PATH", "")])
    cmd = ["bash", str(script), *(args or [])]
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=merged,
        text=True,
        capture_output=True,
        check=False,
    )


def _install_flock(bin_dir: Path) -> None:
    _write_exe(
        bin_dir / "flock",
        """#!/usr/bin/env bash
set -euo pipefail
# Accept: flock -n FD  (lock already opened by caller)
exit 0
""",
    )


def _install_curl(
    bin_dir: Path,
    *,
    http_code: str = "204",
    log_path: Path,
    fail_request: bool = False,
) -> None:
    _write_exe(
        bin_dir / "curl",
        f"""#!/usr/bin/env bash
set -euo pipefail
log="{log_path}"
out=""
write_out=""
data=""
url=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) out="$2"; shift 2 ;;
    --write-out) write_out="$2"; shift 2 ;;
    --data) data="$2"; shift 2 ;;
    --header|--request|--connect-timeout|--max-time)
      shift
      if [[ $# -gt 0 && "$1" != --* ]]; then
        shift
      fi
      ;;
    --silent|--show-error) shift ;;
    --) shift; url="${{1:-}}"; shift || true; break ;;
    http*|HTTP*) url="$1"; shift ;;
    *) shift ;;
  esac
done
printf 'url=%s\\n' "$url" >>"$log"
printf 'data=%s\\n' "$data" >>"$log"
if [[ "{int(fail_request)}" == "1" ]]; then
  printf '000'
  exit 7
fi
if [[ -n "$out" ]]; then
  printf '' >"$out"
fi
if [[ "$write_out" == "%{{http_code}}" ]]; then
  printf '%s' "{http_code}"
fi
""",
    )


@pytest.mark.skipif(not NOTIFY.is_file(), reason="notify_discord.sh missing")
def test_notify_missing_webhook(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_curl(bin_dir, log_path=tmp_path / "curl.log")
    result = _run(
        NOTIFY,
        ["ERROR", "title", "msg"],
        env={"DISCORD_WEBHOOK_URL": ""},
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "missing_discord_webhook_url" in result.stderr


@pytest.mark.skipif(not NOTIFY.is_file(), reason="notify_discord.sh missing")
def test_notify_2xx_success(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    log = tmp_path / "curl.log"
    _install_curl(bin_dir, http_code="204", log_path=log)
    result = _run(
        NOTIFY,
        ["ERROR", "CLIPS health check failed", "health endpoint returned HTTP 503"],
        env={
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
            "HOST_LABEL": "production",
            "DISCORD_USERNAME": "CLIPS Monitor",
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "OK discord_notified" in result.stdout
    payload = log.read_text(encoding="utf-8")
    assert FAKE_WEBHOOK in payload
    assert "[ERROR] CLIPS health check failed" in payload
    assert "Environment: production" in payload
    assert "health endpoint returned HTTP 503" in payload


@pytest.mark.skipif(not NOTIFY.is_file(), reason="notify_discord.sh missing")
def test_notify_non_2xx_fails(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_curl(bin_dir, http_code="500", log_path=tmp_path / "curl.log")
    result = _run(
        NOTIFY,
        ["ERROR", "title", "msg"],
        env={"DISCORD_WEBHOOK_URL": FAKE_WEBHOOK},
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "discord_http_status" in result.stderr
    assert "500" in result.stderr


@pytest.mark.skipif(not NOTIFY.is_file(), reason="notify_discord.sh missing")
def test_notify_json_escaping(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    log = tmp_path / "curl.log"
    _install_curl(bin_dir, log_path=log)
    message = 'line1\nquote "here" and \\ backslash'
    result = _run(
        NOTIFY,
        ["WARN", 'Title "x"', message],
        env={"DISCORD_WEBHOOK_URL": FAKE_WEBHOOK},
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    data_line = next(
        line
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.startswith("data=")
    )
    raw = data_line[len("data=") :]
    assert '"content":' in raw
    assert '\\"here\\"' in raw or '\\"x\\"' in raw
    assert "\\n" in raw
    assert "\\\\" in raw
    # Payload must be parseable-ish: balanced braces
    assert raw.startswith("{") and raw.endswith("}")


@pytest.mark.skipif(not NOTIFY.is_file(), reason="notify_discord.sh missing")
def test_notify_does_not_print_webhook_url(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_curl(bin_dir, log_path=tmp_path / "curl.log")
    result = _run(
        NOTIFY,
        ["INFO", "title", "msg"],
        env={"DISCORD_WEBHOOK_URL": FAKE_WEBHOOK},
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0
    assert FAKE_WEBHOOK not in result.stdout
    assert FAKE_WEBHOOK not in result.stderr
    assert "TESTTOKEN" not in result.stdout
    assert "TESTTOKEN" not in result.stderr


def _fake_check(path: Path, *, rc: int, output: str = "check-output\n") -> None:
    _write_exe(
        path,
        f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s' '{output}'
exit {rc}
""",
    )


def _fake_notify(path: Path, log: Path, *, fail: bool = False) -> None:
    fail_flag = "1" if fail else "0"
    _write_exe(
        path,
        f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\t%s\\t%s\\n' "$1" "$2" "$3" >>"{log}"
if [[ "{fail_flag}" == "1" ]]; then
  echo "FAIL fake_notify" >&2
  exit 1
fi
echo "OK fake_notify level=$1"
exit 0
""",
    )


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_first_success_no_alert(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    state_dir = tmp_path / "state"
    check = tmp_path / "ok.sh"
    notify = tmp_path / "notify.sh"
    notify_log = tmp_path / "notify.log"
    _fake_check(check, rc=0, output="OK all-good\n")
    _fake_notify(notify, notify_log)

    result = _run(
        RUN_CHECK,
        ["host", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
            "ALERT_COOLDOWN_SECONDS": "3600",
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "OK all-good" in result.stdout
    assert not notify_log.exists() or notify_log.read_text(encoding="utf-8") == ""
    assert (state_dir / "host.state").read_text(encoding="utf-8").startswith("STATUS=OK")


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_first_failure_alerts_once(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    state_dir = tmp_path / "state"
    check = tmp_path / "fail.sh"
    notify = tmp_path / "notify.sh"
    notify_log = tmp_path / "notify.log"
    _fake_check(check, rc=1, output="FAIL boom\n")
    _fake_notify(notify, notify_log)

    result = _run(
        RUN_CHECK,
        ["host", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    lines = notify_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("ERROR\tCLIPS host check failed\t")
    assert "FAIL boom" in lines[0]
    assert "STATUS=FAILED" in (state_dir / "host.state").read_text(encoding="utf-8")


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_repeat_failure_respects_cooldown(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    now = int(time.time())
    (state_dir / "host.state").write_text(
        f"STATUS=FAILED\nLAST_ALERT_EPOCH={now}\nLAST_CHANGE_EPOCH={now}\n",
        encoding="utf-8",
    )
    check = tmp_path / "fail.sh"
    notify = tmp_path / "notify.sh"
    notify_log = tmp_path / "notify.log"
    _fake_check(check, rc=1, output="FAIL again\n")
    _fake_notify(notify, notify_log)

    result = _run(
        RUN_CHECK,
        ["host", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
            "ALERT_COOLDOWN_SECONDS": "3600",
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert not notify_log.exists() or notify_log.read_text(encoding="utf-8") == ""


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_repeat_failure_alerts_after_cooldown(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    old = int(time.time()) - 4000
    (state_dir / "host.state").write_text(
        f"STATUS=FAILED\nLAST_ALERT_EPOCH={old}\nLAST_CHANGE_EPOCH={old}\n",
        encoding="utf-8",
    )
    check = tmp_path / "fail.sh"
    notify = tmp_path / "notify.sh"
    notify_log = tmp_path / "notify.log"
    _fake_check(check, rc=1, output="FAIL still\n")
    _fake_notify(notify, notify_log)

    result = _run(
        RUN_CHECK,
        ["host", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
            "ALERT_COOLDOWN_SECONDS": "3600",
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    lines = notify_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("ERROR\t")


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_recovery_alert_once(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    now = int(time.time())
    (state_dir / "backup.state").write_text(
        f"STATUS=FAILED\nLAST_ALERT_EPOCH={now}\nLAST_CHANGE_EPOCH={now}\n",
        encoding="utf-8",
    )
    check = tmp_path / "ok.sh"
    notify = tmp_path / "notify.sh"
    notify_log = tmp_path / "notify.log"
    _fake_check(check, rc=0, output="OK backup=fresh\n")
    _fake_notify(notify, notify_log)

    result = _run(
        RUN_CHECK,
        ["backup", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    lines = notify_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("RECOVERY\tCLIPS backup check recovered\t")
    assert "STATUS=OK" in (state_dir / "backup.state").read_text(encoding="utf-8")

    notify_log.write_text("", encoding="utf-8")
    result2 = _run(
        RUN_CHECK,
        ["backup", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
        },
        path_prepend=[bin_dir],
    )
    assert result2.returncode == 0
    assert notify_log.read_text(encoding="utf-8") == ""


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_rejects_invalid_check_name(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    check = tmp_path / "ok.sh"
    _fake_check(check, rc=0)
    result = _run(
        RUN_CHECK,
        ["../evil", str(check)],
        env={"MONITOR_STATE_DIR": str(tmp_path / "state")},
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "invalid_check_name" in result.stderr


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_keeps_failure_when_discord_fails(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    state_dir = tmp_path / "state"
    check = tmp_path / "fail.sh"
    notify = tmp_path / "notify.sh"
    notify_log = tmp_path / "notify.log"
    _fake_check(check, rc=1, output="FAIL x\n")
    _fake_notify(notify, notify_log, fail=True)

    result = _run(
        RUN_CHECK,
        ["host", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 1
    assert "STATUS=FAILED" in (state_dir / "host.state").read_text(encoding="utf-8")


@pytest.mark.skipif(not RUN_CHECK.is_file(), reason="run_monitor_check.sh missing")
def test_monitor_keeps_success_when_recovery_discord_fails(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _install_flock(bin_dir)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    now = int(time.time())
    (state_dir / "host.state").write_text(
        f"STATUS=FAILED\nLAST_ALERT_EPOCH={now}\nLAST_CHANGE_EPOCH={now}\n",
        encoding="utf-8",
    )
    check = tmp_path / "ok.sh"
    notify = tmp_path / "notify.sh"
    _fake_check(check, rc=0, output="OK\n")
    _fake_notify(notify, tmp_path / "notify.log", fail=True)

    result = _run(
        RUN_CHECK,
        ["host", str(check)],
        env={
            "MONITOR_STATE_DIR": str(state_dir),
            "NOTIFY_DISCORD_SCRIPT": str(notify),
            "DISCORD_WEBHOOK_URL": FAKE_WEBHOOK,
        },
        path_prepend=[bin_dir],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "STATUS=OK" in (state_dir / "host.state").read_text(encoding="utf-8")


def _install_stub_project(proj: Path, record: Path) -> None:
    scripts = proj / "scripts"
    scripts.mkdir(parents=True)
    _write_exe(
        scripts / "run_monitor_check.sh",
        f"""#!/usr/bin/env bash
set -euo pipefail
printf 'name=%s\\n' "$1" >>"{record}"
printf 'min_size=%s\\n' "${{MIN_SIZE_BYTES-}}" >>"{record}"
shift
printf 'cmd=%s\\n' "$*" >>"{record}"
exit 0
""",
    )
    _write_exe(scripts / "check_host.sh", "#!/usr/bin/env bash\nexit 0\n")
    _write_exe(scripts / "check_backup_freshness.sh", "#!/usr/bin/env bash\nexit 0\n")


@pytest.mark.skipif(not RUN_HOST.is_file(), reason="run_host_monitor.sh missing")
def test_host_monitor_missing_env(tmp_path: Path) -> None:
    result = _run(
        RUN_HOST,
        env={
            "CLIPS_MONITOR_ENV": str(tmp_path / "missing.env"),
            "PROJECT_DIR": str(tmp_path / "proj"),
        },
    )
    assert result.returncode == 1
    assert "missing_env" in result.stderr


@pytest.mark.skipif(not RUN_HOST.is_file(), reason="run_host_monitor.sh missing")
def test_host_monitor_passes_env(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    record = tmp_path / "record.log"
    _install_stub_project(proj, record)
    env_file = tmp_path / "clips-monitor.env"
    env_file.write_text(
        "DISCORD_WEBHOOK_URL=https://discord.example.invalid/api/webhooks/1/x\n"
        "HOST_LABEL=staging\n",
        encoding="utf-8",
    )
    result = _run(
        RUN_HOST,
        env={
            "CLIPS_MONITOR_ENV": str(env_file),
            "PROJECT_DIR": str(proj),
        },
    )
    assert result.returncode == 0, result.stderr + result.stdout
    text = record.read_text(encoding="utf-8")
    assert "name=host" in text
    assert str(proj / "scripts" / "check_host.sh") in text


@pytest.mark.skipif(not RUN_BACKUP.is_file(), reason="run_backup_monitor.sh missing")
def test_backup_monitor_default_min_size(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    record = tmp_path / "record.log"
    _install_stub_project(proj, record)
    env_file = tmp_path / "clips-monitor.env"
    env_file.write_text(
        "DISCORD_WEBHOOK_URL=https://discord.example.invalid/hook\n",
        encoding="utf-8",
    )
    result = _run(
        RUN_BACKUP,
        env={
            "CLIPS_MONITOR_ENV": str(env_file),
            "PROJECT_DIR": str(proj),
        },
    )
    assert result.returncode == 0, result.stderr + result.stdout
    text = record.read_text(encoding="utf-8")
    assert "name=backup" in text
    assert re.search(r"^min_size=500$", text, re.M)
    assert str(proj / "scripts" / "check_backup_freshness.sh") in text


@pytest.mark.skipif(not RUN_BACKUP.is_file(), reason="run_backup_monitor.sh missing")
def test_backup_monitor_env_overrides_min_size(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    record = tmp_path / "record.log"
    _install_stub_project(proj, record)
    env_file = tmp_path / "clips-monitor.env"
    env_file.write_text(
        "DISCORD_WEBHOOK_URL=https://discord.example.invalid/hook\nMIN_SIZE_BYTES=900\n",
        encoding="utf-8",
    )
    result = _run(
        RUN_BACKUP,
        env={
            "CLIPS_MONITOR_ENV": str(env_file),
            "PROJECT_DIR": str(proj),
        },
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert re.search(r"^min_size=900$", record.read_text(encoding="utf-8"), re.M)


@pytest.mark.skipif(not RUN_BACKUP.is_file(), reason="run_backup_monitor.sh missing")
def test_backup_monitor_missing_env(tmp_path: Path) -> None:
    result = _run(
        RUN_BACKUP,
        env={
            "CLIPS_MONITOR_ENV": str(tmp_path / "nope.env"),
            "PROJECT_DIR": str(tmp_path / "proj"),
        },
    )
    assert result.returncode == 1
    assert "missing_env" in result.stderr
