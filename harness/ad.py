"""Wrapper do agent-desktop: executa o binario e devolve o envelope JSON tipado."""
import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Envelope:
    argv: tuple
    returncode: int | None
    ok: bool
    version: str | None = None
    command: str | None = None
    data: dict | list | None = None
    error_code: str | None = None
    error_message: str | None = None
    disposition: dict | None = None  # {"delivery": ..., "retry": ...}
    duration_ms: int = 0


def retry_safe(env: Envelope) -> bool:
    """Verdadeiro so se a disposicao permite repetir.

    Fonte: guia embutido (`agent-desktop skills get desktop`, secao "Delivery and
    retry"): "Retry ... only when `disposition.retry` is `safe`. Only
    `not_delivered` is safe." Exigimos os dois: retry == "safe" e
    delivery == "not_delivered". Erros do harness (sem disposicao) nunca sao seguros.
    """
    d = env.disposition or {}
    return not env.ok and d.get("retry") == "safe" and d.get("delivery") == "not_delivered"


def run_ad(argv, *, binary="agent-desktop", env=None, timeout=30.0,
           steps_path=None, scenario=None, rep=None, step=None) -> Envelope:
    """Executa `binary *argv` (sem shell). Nunca levanta por falha do comando."""
    full = (binary, *argv)
    t0 = time.monotonic()
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=timeout, env=env)
        env_out = _parse(full, p.returncode, p.stdout, p.stderr)
    except subprocess.TimeoutExpired:
        env_out = _err(full, None, "HARNESS_TIMEOUT", f"timeout de {timeout}s")
    except OSError as e:
        env_out = _err(full, None, "HARNESS_SPAWN_FAILED", str(e))
    ms = round((time.monotonic() - t0) * 1000)
    env_out = Envelope(**{**env_out.__dict__, "duration_ms": ms})
    if steps_path:
        row = {"ts": datetime.now(timezone.utc).isoformat(), "scenario": scenario, "rep": rep,
               "step": step, "argv": list(full), "ok": env_out.ok,
               "error_code": env_out.error_code, "duration_ms": ms}
        with open(steps_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return env_out


def _err(argv, rc, code, msg):
    return Envelope(argv=tuple(argv), returncode=rc, ok=False, error_code=code, error_message=msg)


def _parse(argv, rc, stdout, stderr):
    try:
        j = json.loads(stdout)
        if not isinstance(j, dict) or not isinstance(j.get("ok"), bool):
            raise ValueError("envelope sem 'ok' booleano")
        err = j.get("error") or {}
        if not j["ok"] and not isinstance(err, dict):
            raise ValueError("'error' invalido")
    except ValueError as e:  # JSONDecodeError herda de ValueError
        return _err(argv, rc, "HARNESS_BAD_ENVELOPE", f"{e}; stdout={stdout[:200]!r} stderr={stderr[:200]!r}")
    data = j.get("data")
    return Envelope(
        argv=tuple(argv), returncode=rc, ok=j["ok"], version=j.get("version"),
        command=j.get("command"), data=data if isinstance(data, (dict, list)) else None,
        error_code=err.get("code"), error_message=err.get("message"),
        disposition=err.get("disposition") if isinstance(err.get("disposition"), dict) else None,
    )


def load_display_env(path=None) -> dict:
    """Le KEY=VALUE de $XDG_RUNTIME_DIR/cadcli-display.env (gerado por scripts/display-up.sh)."""
    p = Path(path) if path else Path(os.environ["XDG_RUNTIME_DIR"]) / "cadcli-display.env"
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def build_env(display_env: dict, *, base=None, allow_real_session=False) -> dict:
    """Ambiente para o binario. Recusa DISPLAY != :2 sem allow_real_session=True."""
    if display_env.get("DISPLAY") != ":2" and not allow_real_session:
        raise ValueError(
            f"DISPLAY={display_env.get('DISPLAY')!r} nao e o display isolado ':2'; "
            "use allow_real_session=True so com autorizacao do Igor")
    return {**(os.environ if base is None else base), **display_env}
