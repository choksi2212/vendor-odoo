#!/usr/bin/env python3
"""
Arial Sense — Unified Dev Launcher
────────────────────────────────────
Run from the project root:

    python app.py

Starts both servers:
  * Backend  (FastAPI + Uvicorn)  -> http://localhost:8000
  * Frontend (Python http.server) -> http://localhost:5500

Press Ctrl+C to stop everything cleanly.
"""

import os
import re
import signal
import subprocess
import sys
import threading
import time
import webbrowser

# ── Force UTF-8 output on Windows ────────────────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        os.system("chcp 65001 >nul 2>&1")
    except Exception:
        pass
    os.system("")  # activate ANSI VT100

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT          = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR   = os.path.join(ROOT, "backend")
FRONTEND_DIR  = os.path.join(ROOT, "frontend")
BACKEND_PORT  = 8000
FRONTEND_PORT = 5500

# ── ANSI colours ──────────────────────────────────────────────────────────────

R      = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"

# ── Venv discovery ────────────────────────────────────────────────────────────

def _find_venv_python() -> str:
    """
    Search for a Python executable in known venv locations.
    Checks root-level venvs first, then backend/.venv as fallback.
    """
    candidates = []

    # Any directory at the root that looks like a venv
    for name in os.listdir(ROOT):
        candidate_dir = os.path.join(ROOT, name)
        if not os.path.isdir(candidate_dir):
            continue
        py = os.path.join(candidate_dir, "Scripts", "python.exe") if sys.platform == "win32" \
             else os.path.join(candidate_dir, "bin", "python")
        if os.path.exists(py):
            candidates.append((name, py))

    # backend/.venv as fallback
    fallback = os.path.join(BACKEND_DIR, ".venv",
                            "Scripts" if sys.platform == "win32" else "bin",
                            "python.exe" if sys.platform == "win32" else "python")
    if os.path.exists(fallback):
        candidates.append((".venv (backend)", fallback))

    if not candidates:
        _print(f"\n  {RED}{BOLD}Error:{R} No virtual environment found.")
        _print(f"\n  Create one and install dependencies:")
        _print(f"    python -m venv arial")
        if sys.platform == "win32":
            _print(f"    arial\\Scripts\\pip install -r backend\\requirements.txt")
        else:
            _print(f"    arial/bin/pip install -r backend/requirements.txt")
        _print()
        sys.exit(1)

    # Prefer the one named "arial" if present, otherwise take the first
    for name, py in candidates:
        if "arial" in name.lower():
            return py
    return candidates[0][1]

# ── .env reader ───────────────────────────────────────────────────────────────

def _read_env() -> dict:
    """Parse backend/.env into a dict (no external deps needed)."""
    env = {}
    env_path = os.path.join(BACKEND_DIR, ".env")
    if not os.path.exists(env_path):
        return env
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^([A-Z_]+)\s*=\s*(.*)$', line)
            if m:
                env[m.group(1)] = m.group(2).strip()
    return env

# ── Pre-flight DB migration ───────────────────────────────────────────────────

def _run_db_migration(python_exe: str) -> None:
    """
    Run an inline psycopg2 migration to ensure the DB schema is up to date
    BEFORE uvicorn starts. This prevents 'column does not exist' errors on
    servers that were created before new columns were added to the models.
    """
    env = _read_env()
    db_url = env.get("DATABASE_URL", "")
    if not db_url:
        _print(f"  {YELLOW}WARNING:{R} DATABASE_URL not found in backend/.env — skipping migration check.")
        return

    # Convert SQLAlchemy URL to psycopg2 DSN
    dsn = db_url.replace("postgresql+psycopg2://", "postgresql://")

    migration_script = (
        "import sys\n"
        "try:\n"
        "    import psycopg2\n"
        "except ImportError:\n"
        "    print('SKIP: psycopg2 not available'); sys.exit(0)\n"
        "dsn = sys.argv[1]\n"
        "try:\n"
        "    conn = psycopg2.connect(dsn)\n"
        "    conn.autocommit = True\n"
        "    cur = conn.cursor()\n"
        "    cur.execute('SELECT column_name FROM information_schema.columns "
        "WHERE table_name=\\'users\\' AND column_name=\\'is_2fa_enabled\\'')\n"
        "    if cur.fetchone() is None:\n"
        "        cur.execute('ALTER TABLE users ADD COLUMN is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE')\n"
        "        print('MIGRATION: Added users.is_2fa_enabled')\n"
        "    else:\n"
        "        print('OK: users.is_2fa_enabled already present')\n"
        "    cur.execute(\"SELECT to_regclass('public.otp_codes')\")\n"
        "    if cur.fetchone()[0] is None:\n"
        "        cur.execute('CREATE TABLE otp_codes (id UUID PRIMARY KEY DEFAULT gen_random_uuid(),"
        " user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
        " otp_hash VARCHAR(64) NOT NULL, expires_at TIMESTAMPTZ NOT NULL,"
        " attempt_count INTEGER NOT NULL DEFAULT 0,"
        " created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())')\n"
        "        cur.execute('CREATE INDEX ix_otp_codes_user_id ON otp_codes (user_id)')\n"
        "        print('MIGRATION: Created otp_codes table')\n"
        "    else:\n"
        "        print('OK: otp_codes table already present')\n"
        "    cur.close(); conn.close()\n"
        "except Exception as e:\n"
        "    print(f'MIGRATION WARNING: {e}')\n"
    )

    _print(f"  {DIM}Verifying database schema ...{R}")
    try:
        result = subprocess.run(
            [python_exe, "-c", migration_script, dsn],
            capture_output=True,
            text=True,
            timeout=15,
        )
        for line in (result.stdout + result.stderr).splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("MIGRATION:"):
                _print(f"  {YELLOW}{BOLD}{line}{R}")
            elif line.startswith("OK:"):
                _print(f"  {GREEN}{line}{R}")
            else:
                _print(f"  {DIM}{line}{R}")
    except Exception as e:
        _print(f"  {YELLOW}Migration check skipped: {e}{R}")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _print(*args, **kwargs) -> None:
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe = " ".join(str(a) for a in args).encode("ascii", errors="replace").decode("ascii")
        print(safe, **kwargs)


def _stream_output(stream, label: str, color: str) -> None:
    try:
        for raw in stream:
            line = raw.rstrip()
            if line:
                _print(f"  {color}{BOLD}{label}{R}  {line}")
    except Exception:
        pass

# ── Process launchers ─────────────────────────────────────────────────────────

def _start_backend(python_exe: str) -> subprocess.Popen:
    proc = subprocess.Popen(
        [
            python_exe, "-m", "uvicorn", "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", str(BACKEND_PORT),
        ],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    threading.Thread(
        target=_stream_output,
        args=(proc.stdout, "[BACKEND] ", CYAN),
        daemon=True,
    ).start()
    return proc


def _start_frontend() -> subprocess.Popen:
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "http.server", str(FRONTEND_PORT),
            "--directory", FRONTEND_DIR,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    threading.Thread(
        target=_stream_output,
        args=(proc.stdout, "[FRONTEND]", GREEN),
        daemon=True,
    ).start()
    return proc

# ── Banner ────────────────────────────────────────────────────────────────────

def _print_banner(venv_name: str) -> None:
    bar = "-" * 54
    _print()
    _print(f"  {CYAN}{BOLD}{bar}{R}")
    _print(f"  {CYAN}{BOLD}    Arial Sense  --  Dev Launcher{R}")
    _print(f"  {CYAN}{BOLD}{bar}{R}")
    _print()
    _print(f"  {DIM}venv:{R}  {venv_name}")
    _print()
    _print(f"  {CYAN}>{R}  Backend   {BOLD}http://localhost:{BACKEND_PORT}{R}")
    _print(f"  {CYAN}>{R}  API Docs  {BOLD}http://localhost:{BACKEND_PORT}/docs{R}")
    _print(f"  {GREEN}>{R}  Frontend  {BOLD}http://localhost:{FRONTEND_PORT}{R}")
    _print()
    _print(f"  {DIM}Press Ctrl+C to stop all servers.{R}")
    _print(f"  {CYAN}{BOLD}{bar}{R}")
    _print()

# ── Main ──────────────────────────────────────────────────────────────────────

def _free_port(port: int) -> None:
    """Kill any process already listening on the given port."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        in_use = s.connect_ex(("127.0.0.1", port)) == 0
        s.close()
        if not in_use:
            return
        # Port is occupied — find and kill via netstat
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) != os.getpid():
                    subprocess.run(["taskkill", "/F", "/PID", pid],
                                   capture_output=True)
                    _print(f"  {YELLOW}Freed port {port} (killed PID {pid}){R}")
        time.sleep(1)
    except Exception:
        pass


def main() -> None:
    python_exe = _find_venv_python()
    venv_name  = os.path.basename(os.path.dirname(os.path.dirname(python_exe)))

    _print_banner(venv_name)

    # Free ports before starting — kills any stale leftover processes
    _print(f"  {DIM}Checking ports ...{R}")
    _free_port(BACKEND_PORT)
    _free_port(FRONTEND_PORT)

    # Run DB migration BEFORE uvicorn starts — guarantees schema is up to date
    _run_db_migration(python_exe)
    _print()

    backend  = _start_backend(python_exe)
    time.sleep(2)
    frontend = _start_frontend()
    time.sleep(1)

    _print(f"\n  {GREEN}{BOLD}Both servers are running.{R}")
    _print(f"  {DIM}Opening browser -> http://localhost:{FRONTEND_PORT}{R}\n")

    try:
        webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
    except Exception:
        pass

    processes = [("Backend", backend), ("Frontend", frontend)]

    def _shutdown(*_) -> None:
        _print(f"\n  {YELLOW}{BOLD}Shutting down ...{R}")
        for name, proc in processes:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                except Exception:
                    pass
        _print(f"  {GREEN}{BOLD}All servers stopped.{R}\n")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        for name, proc in processes:
            if proc.poll() is not None:
                _print(f"\n  {RED}{BOLD}{name} exited unexpectedly (code {proc.returncode}).{R}")
                _shutdown()
        time.sleep(1)


if __name__ == "__main__":
    main()
