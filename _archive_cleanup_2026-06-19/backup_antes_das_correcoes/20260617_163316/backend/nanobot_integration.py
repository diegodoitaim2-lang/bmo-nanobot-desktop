"""
nanobot_integration.py — Integracao total do BMO com o NanobotRuntime.

Usa o AgentLoop real do Nanobot como unico motor de processamento,
com skills, memorias e ferramentas completas.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any


def _log(event: str, **fields: Any) -> None:
    try:
        sys.stderr.write(json.dumps({"event": event, **fields}, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


# ============================================================
# Estado do NanobotRuntime
# ============================================================

_runtime = None
_runtime_lock = threading.Lock()
_runtime_initialized = False
_runtime_error = ""
_runtime_started = False


def is_runtime_ready() -> bool:
    global _runtime_initialized, _runtime_started
    return _runtime_initialized and _runtime_started


def runtime_status() -> dict[str, Any]:
    global _runtime_initialized, _runtime_started, _runtime_error
    with _runtime_lock:
        return {
            "ready": _runtime_initialized and _runtime_started,
            "started": _runtime_started,
            "error": _runtime_error,
            "tools": list(_runtime.tool_names) if _runtime is not None and hasattr(_runtime, 'tool_names') and _runtime_initialized else [],
        }


def initialize_runtime() -> bool:
    """Tenta inicializar o NanobotRuntime. Retorna True se funcionou."""
    global _runtime, _runtime_initialized, _runtime_started, _runtime_error
    
    with _runtime_lock:
        if _runtime_initialized and _runtime_started:
            return True
        
        try:
            from backend import nanobot_runtime as nr
            
            # Descobrir paths como o bmo_backend faz
            root = _find_root()
            config_path = root / "config" / "nanobot_config.json"
            workspace = Path(os.environ.get("BMO_HOME", str(Path.home() / ".bmo"))) / "workspace"
            app_data = Path(os.environ.get("BMO_HOME", str(Path.home() / ".bmo")))
            
            # Pegar env vars do sistema (API keys)
            env = {}
            secrets_paths = [
                root / "config" / "secrets.env",
                app_data / "config" / "secrets.env",
            ]
            for sp in secrets_paths:
                if sp.exists():
                    try:
                        for line in sp.read_text(encoding="utf-8").splitlines():
                            line = line.strip()
                            if "=" in line and not line.startswith("#"):
                                k, v = line.split("=", 1)
                                env[k.strip()] = v.strip()
                    except Exception:
                        pass
            
            # Também pegar do ambiente real
            for key in ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]:
                val = os.environ.get(key) or env.get(key)
                if val:
                    os.environ[key] = val
                    env[key] = val
            
            _log("nanobot_integration_initializing", config=str(config_path))
            
            # Inicializar
            nr.NanobotRuntime.reset()  # Garantir estado limpo
            _runtime = nr.NanobotRuntime.initialize(
                root=root,
                config_path=config_path,
                workspace=workspace,
                app_data=app_data,
                env=env,
            )
            
            if _runtime.is_ready:
                _runtime_initialized = True
                _runtime_started = True
                _runtime_error = ""
                tools = _runtime.tool_names
                _log("nanobot_integration_ok", tools_count=len(tools))
                return True
            else:
                _runtime_error = _runtime.error
                _runtime_initialized = False
                _runtime_started = False
                _log("nanobot_integration_not_ready", error=_runtime_error)
                return False
                
        except Exception as e:
            _runtime_error = str(e)
            _runtime_initialized = False
            _runtime_started = False
            _log("nanobot_integration_failed", error=str(e))
            return False


def _find_root() -> Path:
    """Encontra a raiz do projeto (mesma lógica do bmo_backend.app_root)."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        resource_dir = exe_dir.parent if exe_dir.name.lower() == "bmo_backend" else exe_dir
        if (resource_dir / "config").exists() or (resource_dir / "piper").exists() or (resource_dir / "wakeword.onnx").exists():
            return resource_dir
        return exe_dir
    # Em dev, sobe um nível de backend/
    return Path(__file__).resolve().parents[1]


# ============================================================
# Função principal de chat — usa Nanobot se disponível
# ============================================================

def chat(message: str, session_id: str | None = None, language: str = "pt-BR") -> str | None:
    """Tenta responder com NanobotRuntime. Retorna None se falhar (fallback para motor antigo)."""
    global _runtime, _runtime_initialized, _runtime_started
    
    if not _runtime_initialized or not _runtime_started:
        # Tenta inicializar na primeira chamada
        ok = initialize_runtime()
        if not ok:
            _log("nanobot_integration_skipped", reason="init_failed", error=_runtime_error)
            return None
    
    try:
        sk = f"bmo_desktop:{session_id or 'local'}"
        reply = _runtime.chat(message, session_key=sk)
        if reply:
            return reply
        _log("nanobot_integration_empty_reply")
        return None
    except Exception as e:
        _log("nanobot_integration_chat_failed", error=str(e))
        return None


# ============================================================
# Ferramentas — expõe tools do Nanobot
# ============================================================

def tool_definitions() -> list[dict[str, Any]]:
    """Retorna definições de tools do NanobotRuntime."""
    if not _runtime_initialized or not _runtime_started or _runtime is None:
        # Se não iniciou, tenta
        ok = initialize_runtime()
        if not ok:
            return []
    try:
        return _runtime.definitions()
    except Exception:
        return []


def execute_tool(name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Executa tool no NanobotRuntime. Retorna None se falhar."""
    if not _runtime_initialized or not _runtime_started or _runtime is None:
        return None
    try:
        return _runtime.execute_tool(name, params or {})
    except Exception:
        return None


def tool_names() -> list[str]:
    """Lista nomes das tools disponíveis."""
    if not _runtime_initialized or not _runtime_started or _runtime is None:
        return []
    try:
        return _runtime.tool_names
    except Exception:
        return []
