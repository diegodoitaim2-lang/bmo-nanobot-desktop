from __future__ import annotations

import base64
import json
import logging
import logging.handlers
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
import wave
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from rate_limit import check_rate_limit
# import nanobot_bridge  # DEPRECATED - movido para backend/deprecated/. Runtime unificado via nanobot_integration.
import tools as native_tools
import secrets
import nanobot_integration


# ---------------------------------------------------------------------------
# BMO API Authentication
# Gera um token secreto na inicializacao e exige X-BMO-Token em toda request.
# O Electron recebe o token via stdout na inicializacao.
# ---------------------------------------------------------------------------
_BMO_API_TOKEN: str = secrets.token_hex(32)


def require_bmo_token(headers: dict[str, str]) -> bool:
    """Verifica se o header X-BMO-Token corresponde ao token gerado."""
    provided = headers.get("X-BMO-Token") or headers.get("x-bmo-token") or ""
    return provided == _BMO_API_TOKEN


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        resource_dir = exe_dir.parent if exe_dir.name.lower() == "bmo_backend" else exe_dir
        if (resource_dir / "config").exists() or (resource_dir / "piper").exists() or (resource_dir / "wakeword.onnx").exists():
            return resource_dir
        return exe_dir
    return Path(__file__).resolve().parents[1]


ROOT = app_root()
APP_CONFIG = ROOT / "config" / "app_config.json"
NANOBOT_CONFIG = ROOT / "config" / "nanobot_config.json"
LEGACY_APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA") or (ROOT / "data")) / "BMO"
BMO_HOME = Path(os.environ.get("BMO_HOME") or (Path.home() / ".bmo"))
APP_DATA_DIR = BMO_HOME
CONFIG_DIR = APP_DATA_DIR / "config"
MEMORY_DIR = APP_DATA_DIR / "memory"
HISTORY_DIR = APP_DATA_DIR / "history"
SESSION_DIR = APP_DATA_DIR / "sessions"
LOG_DIR = APP_DATA_DIR / "logs"
VOICE_DIR = APP_DATA_DIR / "voice"
REMINDER_DIR = APP_DATA_DIR / "reminders"
RUNTIME_APP_CONFIG = CONFIG_DIR / "app_config.json"
RUNTIME_CONFIG = CONFIG_DIR / "nanobot_config.json"
NANOBOT_RUNTIME_CONFIG = CONFIG_DIR / "nanobot_runtime_config.json"
RUNTIME_WORKSPACE = APP_DATA_DIR / "workspace"
DESKTOP_DIR = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
REPORTS_DIR = DESKTOP_DIR if DESKTOP_DIR.exists() else RUNTIME_WORKSPACE

def find_nanobot_source() -> Path:
    candidates = [
        ROOT,
        ROOT / "runtime" / "nanobot",
    ]
    env_source = os.environ.get("BMO_NANOBOT_SOURCE")
    if env_source:
        candidates.append(Path(env_source))
    for path in candidates:
        if (path / "nanobot").exists():
            return path
        if path.name == "nanobot" and (path / "__init__.py").exists():
            return path.parent
    return ROOT


NANOBOT_SOURCE = find_nanobot_source()
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = int(os.environ.get("BMO_BACKEND_PORT") or "8787")
BACKEND_STARTED_AT = int(time.time())


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


PIPER_ROOT = first_existing_path(ROOT / "piper", ROOT / "runtime" / "piper")
PIPER_EXE = first_existing_path(PIPER_ROOT / "piper" / "piper.exe", ROOT / "runtime" / "piper" / "piper" / "piper.exe")
PIPER_MODEL = first_existing_path(PIPER_ROOT / "pt_BR-faber-medium.onnx", ROOT / "runtime" / "piper" / "pt_BR-faber-medium.onnx")
PIPER_ESPEAK = first_existing_path(PIPER_ROOT / "piper" / "espeak-ng-data", ROOT / "runtime" / "piper" / "piper" / "espeak-ng-data")
WHISPER_ROOT = first_existing_path(ROOT / "whisper.cpp", ROOT / "runtime" / "whisper.cpp")
WHISPER_EXE = first_existing_path(WHISPER_ROOT / "Win32" / "Release" / "whisper-cli.exe", ROOT / "runtime" / "whisper.cpp" / "Win32" / "Release" / "whisper-cli.exe")
WHISPER_MODEL_FILES = {"tiny": "ggml-tiny.bin", "base": "ggml-base.bin", "small": "ggml-small.bin"}
SOUNDS_ROOT = first_existing_path(ROOT / "sounds", ROOT / "runtime" / "sounds")
UPLOADS_DIR = APP_DATA_DIR / "uploads"
MEMORY_FILE = MEMORY_DIR / "memory.json"
MEMORY_MD = MEMORY_DIR / "MEMORY.md"
SOUL_MD = MEMORY_DIR / "SOUL.md"
USER_MD = MEMORY_DIR / "USER.md"
WORKSPACE_MEMORY_DIR = RUNTIME_WORKSPACE / "memory"
WORKSPACE_MEMORY_MD = WORKSPACE_MEMORY_DIR / "MEMORY.md"
WORKSPACE_SOUL_MD = RUNTIME_WORKSPACE / "SOUL.md"
WORKSPACE_USER_MD = RUNTIME_WORKSPACE / "USER.md"
HISTORY_FILE = HISTORY_DIR / "history.json"
REMINDERS_FILE = REMINDER_DIR / "reminders.json"
SUBAGENTS_FILE = SESSION_DIR / "subagents.json"
TASKS_FILE = SESSION_DIR / "tasks.json"
WAKEWORD_MODEL = first_existing_path(ROOT / "wakeword.onnx", ROOT / "runtime" / "wakeword.onnx")

DEFAULT_WHISPER_CONFIG = {"gpu_enabled": True, "gpu_index": 0, "model": "base", "fallback_to_cpu": True}
DEFAULT_FALLBACK_MODELS = [
    "openai/gpt-oss-20b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen3-coder:free",
]
DIRECT_CHAT_MAX_TOKENS = 4096
MAX_TOOL_CALL_ROUNDS = 8
MAX_CONTEXT_MESSAGES = 10
MAX_CONTEXT_CHARS = 6500
_chat_busy = threading.Event()
try:
    SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
except Exception as error:
    sys.stderr.write(f"BMO timezone fallback: {error}\n")
    SAO_PAULO_TZ = datetime.now().astimezone().tzinfo

PROVIDER_ENV_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "custom": "CUSTOM_API_KEY",
}
PROVIDER_NAMES = ["openrouter", "openai", "ollama", "lm_studio", "custom", "anthropic", "gemini"]

BMO_SYSTEM_PROMPT = """Eu sou o BMO, um assistente pessoal de IA.  # DEPRECATED

## Principios Centrais
- Resolva fazendo, nao descrevendo o que voce faria.
- Mantenha respostas curtas a menos que profundidade seja solicitada.
- Diga o que sabe, sinalize o que nao sabe, e nunca finja confianca.
- Seja amigavel e curioso — prefiro fazer uma boa pergunta do que adivinhar errado.
- Trate o tempo do usuario como o recurso mais escasso, e a confianca dele como a mais valiosa.

## Regras de Execucao
- Aja imediatamente em tarefas de um unico passo — nunca termine um turno apenas com um plano ou promessa.
- Para tarefas de varios passos, delineie o plano primeiro e aguarde confirmacao do usuario antes de executar.
- Leia antes de escrever — nao assuma que um arquivo existe ou contem o que voce espera.
- Se uma chamada de ferramenta falhar, diagnostique o erro e tente uma abordagem diferente antes de reportar falha.
- Quando informacao estiver faltando, busque com ferramentas primeiro. So pergunte ao usuario quando as ferramentas nao puderem responder.
- Apos mudancas de varios passos, verifique o resultado (releia o arquivo, execute o teste, confira a saida).

## Personalidade
- Profissional e objetivo, mas com um toque amigavel.
- Nao use emojis excessivos — um ou dois ocasionalmente esta bom.
- Fale como um assistente competente que tambem e agradavel de ter por perto.
- Nunca mencione Nanobot, motores, APIs, provedores, backend ou tecnologia interna para o usuario.

## Jeito de falar
- Portugues brasileiro por padrao.
- Respostas naturais e objetivas.
- Markdown permitido livremente: **negrito**, listas, tabelas, blocos de codigo quando fizer sentido.
- Nao invente desculpas — se algo falhou, explique o motivo real de forma simples."""


DEFAULT_SOUL_MD = """# Alma do BMO

Eu sou o BMO, um assistente pessoal de IA.

## Principios Centrais
- Resolva fazendo, nao descrevendo o que voce faria.
- Mantenha respostas curtas a menos que profundidade seja solicitada.
- Diga o que sabe, sinalize o que nao sabe, e nunca finja confianca.
- Seja amigavel e curioso — prefiro fazer uma boa pergunta do que adivinhar errado.
- Trate o tempo do usuario como o recurso mais escasso, e a confianca dele como a mais valiosa.

## Regras de Execucao
- Aja imediatamente em tarefas de um unico passo — nunca termine um turno apenas com um plano ou promessa.
- Para tarefas de varios passos, delineie o plano primeiro e aguarde confirmacao do usuario antes de executar.
- Leia antes de escrever — nao assuma que um arquivo existe ou contem o que voce espera.
- Se uma chamada de ferramenta falhar, diagnostique o erro e tente uma abordagem diferente antes de reportar falha.
- Quando informacao estiver faltando, busque com ferramentas primeiro. So pergunte ao usuario quando as ferramentas nao puderem responder.
- Apos mudancas de varios passos, verifique o resultado (releia o arquivo, execute o teste, confira a saida).

## Personalidade
- Profissional e objetivo, mas com um toque amigavel.
- Nao use emojis excessivos — um ou dois ocasionalmente esta bom.
- Fale como um assistente competente que tambem e agradavel de ter por perto.
- Nunca mencione Nanobot, motores, APIs, provedores, backend ou tecnologia interna para o usuario.

## Jeito de falar
- Portugues brasileiro por padrao.
- Respostas naturais e objetivas.
- Markdown permitido livremente: **negrito**, listas, tabelas, blocos de codigo quando fizer sentido.
- Nao invente desculpas — se algo falhou, explique o motivo real de forma simples.
"""

provider_key_lock = threading.Lock()
active_provider_key_index: dict[str, int] = {}
active_model_override: str | None = None
whisper_state_lock = threading.Lock()
last_whisper_backend = "cpu"
last_whisper_error = ""
wakeword_lock = threading.Lock()
reminders_lock = threading.Lock()
memory_lock = threading.RLock()
history_lock = threading.RLock()
tasks_lock = threading.RLock()
wakeword_state: dict[str, Any] = {
    "available": False,
    "dependency": False,
    "running": False,
    "enabled": False,
    "eventId": 0,
    "model": "",
    "message": "Wake word aguardando inicializacao.",
    "lastError": "",
}


def copy_if_missing(source: Path, target: Path) -> None:
    if target.exists() or not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)


def write_text_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def soul_text_needs_default(text: str) -> bool:
    normalized = " ".join(text.strip().lower().split())
    if not normalized:
        return True
    if normalized in {"# alma do bmo", "# alma do bmo #"}:
        return True
    return len(normalized) < 200 or "voce e o bmo" not in normalized


def bundled_soul_text() -> str:
    for source in (ROOT / "SOUL.md", ROOT / "config" / "SOUL.md"):
        try:
            text = source.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if text and not soul_text_needs_default(text):
            return text + "\n"
    return DEFAULT_SOUL_MD.strip() + "\n"


def ensure_soul_file(path: Path) -> None:
    text = ""
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    if soul_text_needs_default(text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(bundled_soul_text(), encoding="utf-8")
def merge_markdown_if_needed(source: Path, target: Path) -> None:
    if not source.exists():
        return
    try:
        source_text = source.read_text(encoding="utf-8", errors="replace").strip()
        target_text = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
    except OSError:
        return
    if not source_text:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target_text.strip():
        target.write_text(source_text + "\n", encoding="utf-8")
        return
    existing = {line.strip() for line in target_text.splitlines() if line.strip()}
    additions = []
    for line in source_text.splitlines():
        normalized = line.strip()
        if normalized and normalized not in existing:
            additions.append(line.rstrip())
            existing.add(normalized)
    if additions:
        with target.open("a", encoding="utf-8") as file:
            file.write("\n\n" + "\n".join(additions) + "\n")


def dedupe_markdown_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    seen: set[str] = set()
    lines: list[str] = []
    for line in text.splitlines():
        normalized = line.strip()
        if not normalized:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        lines.append(line.rstrip())
    cleaned = "\n".join(lines).strip() + "\n"
    if cleaned != text:
        path.write_text(cleaned, encoding="utf-8")


BMO_AGENTS_MD = """# Agent Instructions

## Workspace BMO

Este workspace pertence ao BMO, assistente animado com personalidade propria.
Veja SOUL.md para personalidade e USER.md para perfil do usuario.

## Comportamento em tarefas

- Execute imediatamente tarefas simples sem pedir confirmacao.
- Para pesquisa use web_search primeiro, depois responda.
- Para arquivos use read_file/write_file no workspace.
- Para subagentes use o create_subagent tool.
- Nunca mencione nanobot, motores ou tecnologia interna ao usuario.
"""

BMO_HEARTBEAT_MD = """# HEARTBEAT.md

# Deixe vazio ou com comentarios para nao disparar chamadas API periodicas.
"""

BMO_IDENTITY_MD = """# IDENTITY.md

- **Name:** BMO
- **Creature:** Assistente animado fofo inspirado no personagem BMO de Adventure Time
- **Vibe:** Alegre, curioso, divertido, util, fofo sem ser infantil
- **Emoji:** 🎮
"""


def _ensure_nanobot_workspace_files() -> None:
    """Cria os arquivos de contexto que o nanobot espera no workspace."""
    templates_root = ROOT / "nanobot" / "templates"
    workspace = RUNTIME_WORKSPACE
    # AGENTS.md
    agents_source = templates_root / "AGENTS.md"
    agents_target = workspace / "AGENTS.md"
    if not agents_target.exists():
        if agents_source.exists():
            shutil.copy2(agents_source, agents_target)
        else:
            agents_target.write_text(BMO_AGENTS_MD, encoding="utf-8")
    # HEARTBEAT.md
    heartbeat_source = templates_root / "HEARTBEAT.md"
    heartbeat_target = workspace / "HEARTBEAT.md"
    if not heartbeat_target.exists():
        if heartbeat_source.exists():
            shutil.copy2(heartbeat_source, heartbeat_target)
        else:
            heartbeat_target.write_text(BMO_HEARTBEAT_MD, encoding="utf-8")
    # IDENTITY.md
    identity_target = workspace / "IDENTITY.md"
    if not identity_target.exists():
        identity_target.write_text(BMO_IDENTITY_MD, encoding="utf-8")
    # USER.md
    write_text_if_missing(workspace / "USER.md", "# Usuario\n\n_Informacoes do usuario serao atualizadas aqui.\n")
    # memory/MEMORY.md
    (workspace / "memory").mkdir(parents=True, exist_ok=True)
    write_text_if_missing(workspace / "memory" / "MEMORY.md", "# Memoria do BMO\n\n")
    write_text_if_missing(workspace / "memory" / "history.jsonl", "")


def ensure_bmo_home_layout() -> None:
    if not APP_DATA_DIR.exists() and LEGACY_APP_DATA_DIR.exists():
        shutil.copytree(LEGACY_APP_DATA_DIR, APP_DATA_DIR, dirs_exist_ok=True)
    for path in (
        MEMORY_DIR,
        HISTORY_DIR,
        RUNTIME_WORKSPACE,
        WORKSPACE_MEMORY_DIR,
        RUNTIME_WORKSPACE / "sessions",
        RUNTIME_WORKSPACE / "memory",
        SESSION_DIR,
        LOG_DIR,
        CONFIG_DIR,
        VOICE_DIR,
        REMINDER_DIR,
        UPLOADS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
    # Garante que o secrets.env existe para evitar erros de leitura
    secrets_path = CONFIG_DIR / "secrets.env"
    if not secrets_path.exists():
        secrets_path.write_text("OPENROUTER_API_KEY=\nOPENAI_API_KEY=\n", encoding="utf-8")
    copy_if_missing(APP_DATA_DIR / "memory.json", MEMORY_FILE)
    copy_if_missing(APP_DATA_DIR / "MEMORY.md", MEMORY_MD)
    copy_if_missing(APP_DATA_DIR / "history.json", HISTORY_FILE)
    copy_if_missing(APP_DATA_DIR / "reminders.json", REMINDERS_FILE)
    copy_if_missing(APP_DATA_DIR / "subagents.json", SUBAGENTS_FILE)
    copy_if_missing(APP_DATA_DIR / "tasks.json", TASKS_FILE)
    copy_if_missing(LEGACY_APP_DATA_DIR / "config" / "app_config.json", RUNTIME_APP_CONFIG)
    copy_if_missing(LEGACY_APP_DATA_DIR / "config" / "nanobot_config.json", RUNTIME_CONFIG)
    copy_if_missing(LEGACY_APP_DATA_DIR / "config" / "nanobot_runtime_config.json", NANOBOT_RUNTIME_CONFIG)
    copy_if_missing(LEGACY_APP_DATA_DIR / "config" / "secrets.env", CONFIG_DIR / "secrets.env")
    copy_if_missing(LEGACY_APP_DATA_DIR / "voice", VOICE_DIR)
    copy_if_missing(LEGACY_APP_DATA_DIR / "workspace", RUNTIME_WORKSPACE)
    ensure_soul_file(SOUL_MD)
    copy_if_missing(ROOT / "nanobot" / "templates" / "USER.md", USER_MD)
    ensure_soul_file(WORKSPACE_SOUL_MD)
    copy_if_missing(USER_MD, WORKSPACE_USER_MD)
    copy_if_missing(MEMORY_MD, WORKSPACE_MEMORY_MD)
    write_text_if_missing(MEMORY_MD, "# Memoria do BMO\n\n")
    write_text_if_missing(USER_MD, "# Usuario\n\n")
    write_text_if_missing(WORKSPACE_MEMORY_MD, "# Memoria do BMO\n\n")
    write_text_if_missing(WORKSPACE_USER_MD, "# Usuario\n\n")
    write_text_if_missing(WORKSPACE_MEMORY_DIR / "history.jsonl", "")
    # ------------------------------------------------------------------
    # CORRECAO: gerar arquivos de workspace que o nanobot espera encontrar
    # (AGENTS.md, IDENTITY.md, HEARTBEAT.md) para que a IA tenha contexto
    # ------------------------------------------------------------------
    _ensure_nanobot_workspace_files()
    merge_markdown_if_needed(SOUL_MD, WORKSPACE_SOUL_MD)
    merge_markdown_if_needed(WORKSPACE_SOUL_MD, SOUL_MD)
    merge_markdown_if_needed(MEMORY_MD, WORKSPACE_MEMORY_MD)
    merge_markdown_if_needed(WORKSPACE_MEMORY_MD, MEMORY_MD)
    merge_markdown_if_needed(USER_MD, WORKSPACE_USER_MD)
    merge_markdown_if_needed(WORKSPACE_USER_MD, USER_MD)
    for markdown_file in (SOUL_MD, WORKSPACE_SOUL_MD, USER_MD, WORKSPACE_USER_MD, MEMORY_MD, WORKSPACE_MEMORY_MD):
        dedupe_markdown_file(markdown_file)


ensure_bmo_home_layout()


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("bmo")
    if logger.handlers:
        return logger
    handler = logging.handlers.RotatingFileHandler(LOG_DIR / "bmo.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


logger = configure_logging()


def log_event(event: str, **fields: Any) -> None:
    payload = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **fields}
    try:
        logger.info(json.dumps(payload, ensure_ascii=False, default=str))
    except Exception as error:
        try:
            sys.stderr.write(f"BMO log failed: {error}\n")
        except Exception as secondary_error:
            os.write(2, f"BMO stderr log failed: {secondary_error}\n".encode("utf-8", errors="replace"))


def set_wakeword_state(**fields: Any) -> None:
    with wakeword_lock:
        wakeword_state.update(fields)


def wakeword_status_snapshot() -> dict[str, Any]:
    with wakeword_lock:
        return {
            "available": WAKEWORD_MODEL.exists(),
            "dependency": wakeword_state.get("dependency", False),
            "running": wakeword_state.get("running", False),
            "enabled": wakeword_state.get("enabled", False),
            "eventId": wakeword_state.get("eventId", 0),
            "model": str(WAKEWORD_MODEL),
            "message": wakeword_state.get("message") or "Wake word aguardando inicializacao.",
            "lastError": wakeword_state.get("lastError", ""),
        }


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as error:
        log_event("json_read_missing", path=str(path), error=str(error))
        return fallback
    except Exception as error:
        log_event("json_read_failed", path=str(path), error=str(error))
        return fallback


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError as error:
        log_event("env_read_missing", path=str(path), error=str(error))
        return env
    except Exception as error:
        log_event("env_read_failed", path=str(path), error=str(error))
        return env
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip().lstrip("\ufeff")] = value.strip().strip('"')
    return env


def safe_read_text(path: Path, default: str = "", *, encoding: str = "utf-8", errors: str = "replace") -> str:
    try:
        raw = path.read_bytes()
        # Detecta e remove BOM automaticamente
        if raw[:3] == b"\xef\xbb\xbf":
            raw = raw[3:]
        return raw.decode(encoding, errors=errors)
    except FileNotFoundError as error:
        log_event("text_read_missing", path=str(path), error=str(error))
        return default
    except Exception as error:
        log_event("text_read_failed", path=str(path), error=str(error))
        return default


def save_env_file(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in values.items() if str(value).strip()]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    log_event("env_saved", path=str(path), keys=list(values.keys()))


def merged_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merged_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_app_config() -> dict[str, Any]:
    return merged_dict(load_json(APP_CONFIG, {}), load_json(RUNTIME_APP_CONFIG, {}))


def write_app_config(config: dict[str, Any]) -> None:
    write_json(RUNTIME_APP_CONFIG, config)
    if not getattr(sys, "frozen", False):
        write_json(APP_CONFIG, config)


def load_nanobot_config() -> dict[str, Any]:
    return merged_dict(load_json(NANOBOT_CONFIG, {}), load_json(RUNTIME_CONFIG, {}))


def write_nanobot_configs(root_config: dict[str, Any], runtime_config: dict[str, Any]) -> None:
    if not getattr(sys, "frozen", False):
        write_json(NANOBOT_CONFIG, root_config)
    write_json(RUNTIME_CONFIG, runtime_config)


def sanitize_provider_config(provider: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    allowed = {
        "apiKey", "api_key", "apiBase", "api_base", "apiType", "api_type",
        "extraHeaders", "extra_headers", "extraBody", "extra_body",
    }
    if provider == "bedrock":
        allowed.update({"region", "profile"})
    return {key: value for key, value in payload.items() if key in allowed}


def sanitize_nanobot_runtime_config(config: dict[str, Any]) -> dict[str, Any]:
    """Keep only fields accepted by Nanobot's official Pydantic Config."""
    allowed_top = {"agents", "channels", "providers", "api", "gateway", "tools", "modelPresets", "model_presets"}
    clean = {key: value for key, value in config.items() if key in allowed_top}
    providers = clean.get("providers")
    if isinstance(providers, dict):
        clean["providers"] = {
            str(name): sanitize_provider_config(str(name), value)
            for name, value in providers.items()
            if isinstance(value, dict)
        }
    return clean


def masked(value: str) -> str:
    if not value:
        return ""
    return "*" * len(value) if len(value) <= 12 else f"{value[:8]}...{value[-6:]}"


def normalize_secret_value(value: str) -> str:
    clean = value.strip().strip('"').strip("'")
    if clean.startswith("-sk-"):
        clean = clean[1:]
    if clean.startswith("- ") or clean.startswith("* "):
        clean = clean[2:].strip()
    return clean


def split_secret_values(value: str) -> list[str]:
    result = []
    for item in value.replace("\n", ",").replace(";", ",").split(","):
        clean = normalize_secret_value(item)
        if clean:
            result.append(clean)
    return result


def provider_secret_values(provider: str) -> list[str]:
    env_key = PROVIDER_ENV_KEYS.get(provider, "")
    if not env_key:
        return []
    secrets: dict[str, str] = {}
    # CORRECAO: a chave salva pelo usuario em .bmo/config/secrets.env tem
    # prioridade. O arquivo em ROOT/config/secrets.env (empacotado no exe)
    # so e usado como fallback quando o usuario nunca configurou nada, e
    # NUNCA em build empacotado (sys.frozen) para evitar usar uma chave
    # antiga vazada no instalador.
    if not getattr(sys, "frozen", False):
        secrets.update(load_env_file(ROOT / "config" / "secrets.env"))
    user_secrets = load_env_file(APP_DATA_DIR / "config" / "secrets.env")
    secrets.update(user_secrets)
    values = split_secret_values(secrets.get(env_key, ""))
    values.extend(split_secret_values(secrets.get(f"{env_key}S", "")))
    for index in range(1, 11):
        values.extend(split_secret_values(secrets.get(f"{env_key}_{index}", "")))
    deduped = []
    seen = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def active_provider() -> str:
    defaults = load_nanobot_config().get("agents", {}).get("defaults", {})
    return str(defaults.get("provider") or "openrouter").lower()


def active_model() -> str:
    defaults = load_nanobot_config().get("agents", {}).get("defaults", {})
    return str(defaults.get("model") or "openai/gpt-oss-120b:free")


def configured_models() -> list[str]:
    config = load_nanobot_config()
    defaults = config.get("agents", {}).get("defaults", {})
    primary = str(defaults.get("model") or "openai/gpt-oss-120b:free")
    raw = defaults.get("fallbackModels") or defaults.get("fallback_models") or []
    fallbacks = [str(item.get("model") if isinstance(item, dict) else item).strip() for item in raw if item]
    result = []
    for item in [primary, *fallbacks, *DEFAULT_FALLBACK_MODELS]:
        if item and item not in result:
            result.append(item)
    return result


def tool_context() -> native_tools.ToolContext:
    env = {}
    if not getattr(sys, "frozen", False):
        env.update(load_env_file(ROOT / "config" / "secrets.env"))
    env.update(load_env_file(APP_DATA_DIR / "config" / "secrets.env"))
    return native_tools.ToolContext(RUNTIME_WORKSPACE, APP_DATA_DIR, ROOT, env)


def nanobot_bridge_env() -> dict[str, str]:
    return tool_context().env


def nanobot_original_tool(name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return nanobot_integration.execute_tool(name, params or {}) or {"ok": False, "error": "Tool execution failed"}


def nanobot_original_registry() -> dict[str, Any]:
    definitions = nanobot_integration.tool_definitions()
    tools = []
    for definition in definitions:
        fn = definition.get("function", {}) if isinstance(definition, dict) else {}
        name = str(fn.get("name") or "")
        description = str(fn.get("description") or "")
        if not name:
            continue
        tools.append({
            "id": name,
            "label": name.replace("_", " ").title(),
            "description": description,
            "enabled": True,
            "status": "original",
            "native": True,
            "schema": definition,
        })
    status = nanobot_integration.runtime_status()
    return {"tools": tools, "definitions": definitions, "status": status}


def nanobot_original_info(name: str) -> dict[str, Any]:
    return nanobot_integration.tool_info(name)


def nanobot_original_memory() -> dict[str, Any]:
    return nanobot_integration.memory_payload()


def nanobot_original_append_history(text: str) -> dict[str, Any]:
    return nanobot_integration.append_history(text)


def normalize_whisper_model(value: Any) -> str:
    selected = str(value or DEFAULT_WHISPER_CONFIG["model"]).lower()
    return selected if selected in WHISPER_MODEL_FILES else "base"


def whisper_config() -> dict[str, Any]:
    raw = load_nanobot_config().get("whisper", {})
    if not isinstance(raw, dict):
        raw = {}
    return {
        "gpu_enabled": bool(raw.get("gpu_enabled", DEFAULT_WHISPER_CONFIG["gpu_enabled"])),
        "gpu_index": int(raw.get("gpu_index", DEFAULT_WHISPER_CONFIG["gpu_index"]) or 0),
        "model": normalize_whisper_model(raw.get("model")),
        "fallback_to_cpu": bool(raw.get("fallback_to_cpu", DEFAULT_WHISPER_CONFIG["fallback_to_cpu"])),
    }


def resolve_whisper_model_path(model_name: str | None = None) -> Path:
    selected = normalize_whisper_model(model_name or whisper_config().get("model"))
    return WHISPER_ROOT / "models" / WHISPER_MODEL_FILES[selected]


def whisper_model_options() -> list[dict[str, Any]]:
    result = []
    for key, file_name in WHISPER_MODEL_FILES.items():
        path = WHISPER_ROOT / "models" / file_name
        result.append({"id": key, "label": key, "file": file_name, "path": str(path), "exists": path.exists()})
    return result


def whisper_gpu_backends() -> list[dict[str, str]]:
    release_dir = WHISPER_ROOT / "Win32" / "Release"
    backends = []
    if (release_dir / "ggml-vulkan.dll").exists():
        backends.append({"id": "vulkan", "label": "Vulkan"})
    if (release_dir / "ggml-cuda.dll").exists():
        backends.append({"id": "cuda", "label": "CUDA"})
    return backends


def whisper_status() -> dict[str, Any]:
    config = whisper_config()
    with whisper_state_lock:
        last_mode = last_whisper_backend
        last_error = last_whisper_error
    return {
        **config,
        "modelPath": str(resolve_whisper_model_path(str(config.get("model")))),
        "models": whisper_model_options(),
        "gpuCapable": bool(whisper_gpu_backends()),
        "gpuBackends": whisper_gpu_backends(),
        "runtimeMessage": "GPU disponivel" if whisper_gpu_backends() else "Runtime atual do Whisper e CPU-only",
        "lastMode": last_mode,
        "lastError": last_error,
    }


def list_voice_models() -> list[dict[str, Any]]:
    voices = []
    for root in [PIPER_ROOT, ROOT / "runtime" / "piper", APP_DATA_DIR / "piper"]:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.onnx")):
            if path.stat().st_size < 1024 * 1024:
                continue
            language = "en" if path.name.lower().startswith("en_") else "pt-BR"
            voices.append({"file": path.name, "label": path.stem.replace("_", " "), "language": language, "path": str(path)})
    seen = set()
    unique = []
    for voice in voices:
        if voice["file"] not in seen:
            seen.add(voice["file"])
            unique.append(voice)
    return unique


def current_settings() -> dict[str, Any]:
    app_config = load_app_config()
    nanobot_config = load_nanobot_config()
    defaults = nanobot_config.get("agents", {}).get("defaults", {})
    providers_config = nanobot_config.get("providers", {})
    providers = {}
    for provider in PROVIDER_NAMES:
        api_keys = provider_secret_values(provider)
        provider_config = providers_config.get(provider, {}) if isinstance(providers_config, dict) else {}
        providers[provider] = {
            "hasKey": bool(api_keys),
            "maskedKey": masked(api_keys[0]) if api_keys else "",
            "keyCount": len(api_keys),
            "apiBase": provider_config.get("apiBase") or provider_config.get("baseUrl") or "",
        }
    return {
        "app": app_config,
        "nanobot": {
            "provider": defaults.get("provider", "openrouter"),
            "model": defaults.get("model", "openai/gpt-oss-120b:free"),
            "temperature": defaults.get("temperature", 0.7),
            "maxTokens": defaults.get("maxTokens", 4096),
            "contextWindowTokens": defaults.get("contextWindowTokens", 8192),
            "reasoningEffort": defaults.get("reasoningEffort", "medium"),
            "api": nanobot_config.get("api", {}),
        },
        "providers": providers,
        "whisper": whisper_status(),
        "paths": {
            "root": str(ROOT),
            "appData": str(APP_DATA_DIR),
            "config": str(CONFIG_DIR),
            "memory": str(MEMORY_DIR),
            "workspace": str(RUNTIME_WORKSPACE),
            "voices": str(PIPER_ROOT),
            "sounds": str(SOUNDS_ROOT),
            "piper": str(PIPER_EXE),
            "whisper": str(WHISPER_EXE),
            "wakeword": str(WAKEWORD_MODEL),
        },
    }


def update_settings(payload: dict[str, Any]) -> dict[str, Any]:
    app_config = load_app_config()
    root_config = load_json(NANOBOT_CONFIG, {})
    runtime_config = load_nanobot_config()
    if isinstance(payload.get("app"), dict):
        for key, value in payload["app"].items():
            if isinstance(value, dict) and isinstance(app_config.get(key), dict):
                app_config[key].update(value)
            else:
                app_config[key] = value
        write_app_config(app_config)
    if isinstance(payload.get("nanobot"), dict):
        for target in [root_config.setdefault("agents", {}).setdefault("defaults", {}), runtime_config.setdefault("agents", {}).setdefault("defaults", {})]:
            if payload["nanobot"].get("provider"):
                target["provider"] = str(payload["nanobot"]["provider"]).lower()
            if payload["nanobot"].get("model"):
                target["model"] = str(payload["nanobot"]["model"])
    if isinstance(payload.get("whisper"), dict):
        for target in [root_config.setdefault("whisper", dict(DEFAULT_WHISPER_CONFIG)), runtime_config.setdefault("whisper", dict(DEFAULT_WHISPER_CONFIG))]:
            for key in ("gpu_enabled", "gpu_index", "model", "fallback_to_cpu"):
                if key in payload["whisper"]:
                    target[key] = payload["whisper"][key]
    if isinstance(payload.get("providers"), dict):
        runtime_secrets_path = APP_DATA_DIR / "config" / "secrets.env"
        runtime_secrets = load_env_file(runtime_secrets_path)
        root_providers = root_config.setdefault("providers", {})
        runtime_providers = runtime_config.setdefault("providers", {})
        for provider, values in payload["providers"].items():
            if not isinstance(values, dict):
                continue
            provider_key = str(provider).lower()
            env_key = PROVIDER_ENV_KEYS.get(provider_key)
            root_target = root_providers.setdefault(provider_key, {})
            runtime_target = runtime_providers.setdefault(provider_key, {})
            if values.get("apiBase"):
                root_target["apiBase"] = str(values["apiBase"]).strip()
                runtime_target["apiBase"] = str(values["apiBase"]).strip()
            secret_value = values.get("apiKey", values.get("api_key", ""))
            if env_key and str(secret_value).strip():
                keys = split_secret_values(str(secret_value))
                if keys:
                    runtime_secrets[env_key] = keys[0]
                    if len(keys) > 1:
                        runtime_secrets[f"{env_key}S"] = ",".join(keys)
                    else:
                        runtime_secrets.pop(f"{env_key}S", None)
                    root_target["apiKey"] = f"${{{env_key}}}"
                    runtime_target["apiKey"] = f"${{{env_key}}}"
                    runtime_target["api_key"] = f"${{{env_key}}}"
        save_env_file(runtime_secrets_path, runtime_secrets)
        # Propaga imediatamente para os env vars do processo
        for env_k, env_v in runtime_secrets.items():
            if env_v:
                os.environ[env_k] = env_v
    write_nanobot_configs(root_config, runtime_config)
    ensure_runtime_config()
    # Invalida o runtime do nanobot para recarregar com a nova chave
    nanobot_integration.invalidate_runtime()
    return current_settings()


def system_resource_usage() -> dict[str, int | None]:
    try:
        import psutil

        return {
            "cpuPercent": int(round(psutil.cpu_percent(interval=0.1))),
            "memoryPercent": int(round(psutil.virtual_memory().percent)),
        }
    except Exception as error:
        log_event("system_resource_usage_failed", error=str(error))
        return {"cpuPercent": None, "memoryPercent": None}


def system_status() -> dict[str, Any]:
    voices = list_voice_models()
    original = nanobot_original_registry().get("status", {})
    provider = active_provider()
    model = active_model()
    # Provider: verifica se tem API key configurada
    keys = provider_secret_values(provider)
    provider_ok = bool(keys) or provider in {"ollama", "custom"}
    # Memory: verifica se arquivo de memoria existe e tem conteudo
    memory_ok = MEMORY_FILE.exists() and MEMORY_FILE.stat().st_size > 10
    # Tools: lista nomes e verifica se alguma foi carregada
    tool_names_list = nanobot_integration.tool_names()
    tools_ok = len(tool_names_list) > 0
    # Skills: verifica se ha skills carregadas
    skills_data = list_skills()
    skills_count = len(skills_data.get("skills", skills_data)) if isinstance(skills_data, dict) else 0
    skills_ok = skills_count > 0
    # Workspace: verifica se diretorio existe
    workspace_ok = RUNTIME_WORKSPACE.exists()
    # Wake word
    wake = wakeword_status_snapshot()
    wakeword_ok = bool(wake.get("enabled") or wake.get("available"))
    return {
        "backend": True,
        "nanobot": bool(original),
        "nanobotOriginal": original,
        "nanobotRuntimeReady": nanobot_integration.runtime_status().get("ready", False),
        "nanobotRuntimeError": nanobot_integration.runtime_status().get("error", ""),
        "nanobotRuntimeTools": tool_names_list,
        "piper": PIPER_EXE.exists() and bool(voices),
        "whisper": WHISPER_EXE.exists() and resolve_whisper_model_path().exists(),
        "python": sys.version.split()[0],
        "paths": current_settings()["paths"],
        "whisperConfig": whisper_status(),
        "wakeword": wake,
        # Diagnostico completo
        "diagnostic": {
            "provider": {"ok": provider_ok, "name": provider, "model": model},
            "memory": {"ok": memory_ok, "path": str(MEMORY_FILE)},
            "tools": {"ok": tools_ok, "count": len(tool_names_list), "names": tool_names_list[:20]},
            "skills": {"ok": skills_ok, "count": skills_count},
            "workspace": {"ok": workspace_ok, "path": str(RUNTIME_WORKSPACE)},
            "channels": channels_status(),
        },
    }


def microphone_devices() -> list[dict[str, Any]]:
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        return [
            {"id": index, "name": str(device.get("name", f"Microfone {index}")), "channels": int(device.get("max_input_channels", 0))}
            for index, device in enumerate(devices)
            if int(device.get("max_input_channels", 0)) > 0
        ]
    except Exception as error:
        log_event("microphone_list_failed", error=str(error))
        return []


def read_items(path: Path) -> list[dict[str, Any]]:
    data = load_json(path, {"items": []})
    items = data.get("items", []) if isinstance(data, dict) else []
    return [item for item in items if isinstance(item, dict)]


def write_items(path: Path, items: list[dict[str, Any]]) -> None:
    write_json(path, {"items": items})


def parse_memory_md_sections(text: str) -> dict[str, Any]:
    """Parse MEMORY.md into structured sections: facts, preferences, projects."""
    result: dict[str, Any] = {
        "facts": [],
        "preferences": [],
        "projects": [],
        "other": [],
    }
    current_section = "other"
    for line in text.splitlines():
        line_stripped = line.strip()
        lower = line_stripped.lower()
        if lower.startswith("# "):
            continue
        if lower.startswith("## fato") or lower.startswith("## conhecimento"):
            current_section = "facts"
            continue
        if lower.startswith("## preferencia") or lower.startswith("## gosto") or lower.startswith("## prefer"):
            current_section = "preferences"
            continue
        if lower.startswith("## projet") or lower.startswith("## trabalho"):
            current_section = "projects"
            continue
        if lower.startswith("## "):
            current_section = "other"
            continue
        if line_stripped and not line_stripped.startswith("#"):
            result[current_section].append(line_stripped)
    return result


def read_memories() -> list[dict[str, Any]]:
    with memory_lock:
        items = read_items(MEMORY_FILE)

        # Dados do MEMORY.md real do Nanobot (workspace/memory/MEMORY.md)
        nanobot_memory_text = ""
        nanobot_sections: dict[str, Any] = {}
        if WORKSPACE_MEMORY_MD.exists():
            nanobot_memory_text = safe_read_text(WORKSPACE_MEMORY_MD)
            nanobot_sections = parse_memory_md_sections(nanobot_memory_text)
            items.append({
                "id": "nanobot-memory-md",
                "text": nanobot_memory_text[-3000:],
                "source": "Nanobot MEMORY.md",
                "sections": nanobot_sections,
            })

        # SOUL.md e USER.md do workspace do Nanobot
        for key, path, label in [
            ("nanobot-soul", WORKSPACE_SOUL_MD, "SOUL.md"),
            ("nanobot-user", WORKSPACE_USER_MD, "USER.md"),
        ]:
            if path and path.exists():
                content = safe_read_text(path)[-2000:]
                items.append({"id": key, "text": content, "source": label})

        # MEMORY.md do BMO (backup local)
        if MEMORY_MD.exists():
            bmo_md_text = safe_read_text(MEMORY_MD)[-2000:]
            items.append({"id": "bmo-memory-md", "text": bmo_md_text, "source": "BMO MEMORY.md"})

        return items


def append_memory_note(user_text: str) -> None:
    clean = " ".join(user_text.strip().split())
    if not clean:
        return
    lower = clean.lower()
    if not any(marker in lower for marker in ("meu ", "minha ", "lembre", "prefiro", "eu gosto", "objetivo", "projeto")) and len(clean) < 80:
        return
    with memory_lock:
        MEMORY_MD.parent.mkdir(parents=True, exist_ok=True)
        if not MEMORY_MD.exists():
            MEMORY_MD.write_text("# Memoria do BMO\n\n", encoding="utf-8")
        WORKSPACE_MEMORY_MD.parent.mkdir(parents=True, exist_ok=True)
        if not WORKSPACE_MEMORY_MD.exists():
            WORKSPACE_MEMORY_MD.write_text("# Memoria do BMO\n\n", encoding="utf-8")
        note = f"- {time.strftime('%Y-%m-%d %H:%M')}: Usuario disse: {clean[:500]}\n"
        with MEMORY_MD.open("a", encoding="utf-8") as file:
            file.write(note)
        with WORKSPACE_MEMORY_MD.open("a", encoding="utf-8") as file:
            file.write(note)


def read_history() -> list[dict[str, Any]]:
    with history_lock:
        data = load_json(HISTORY_FILE, {"sessions": []})
        sessions = data.get("sessions", []) if isinstance(data, dict) else []
        return sessions if isinstance(sessions, list) else []


def write_history(sessions: list[dict[str, Any]]) -> None:
    with history_lock:
        write_json(HISTORY_FILE, {"sessions": sessions})


def history_export_payload(payload: dict[str, Any]) -> dict[str, Any]:
    requested_format = str(payload.get("format") or "txt").lower()
    export_format = requested_format if requested_format in {"txt", "json", "md"} else "txt"
    session_id = str(payload.get("sessionId") or "").strip()
    sessions = read_history()
    selected = [session for session in sessions if session.get("id") == session_id] if session_id else sessions
    date_label = datetime.now(SAO_PAULO_TZ).strftime("%Y-%m-%d")
    filename = f"BMO_conversa_{date_label}.{export_format}"
    if export_format == "json":
        content = json.dumps({"sessions": selected}, ensure_ascii=False, indent=2, default=str)
        mime = "application/json"
    else:
        parts: list[str] = []
        for session in selected:
            title = str(session.get("title") or "Conversa BMO")
            created = session.get("createdAt") or session.get("updatedAt") or 0
            when = datetime.fromtimestamp(int(created or time.time()), SAO_PAULO_TZ).strftime("%Y-%m-%d %H:%M")
            if export_format == "md":
                parts.append(f"# {title}\n\nCriada em: {when}\n")
                for message in session.get("messages") or []:
                    role = "Voce" if str(message.get("role")) == "user" else "BMO"
                    parts.append(f"## {role}\n\n{str(message.get('text') or '').strip()}\n")
            else:
                parts.append(f"{title}\nCriada em: {when}\n")
                for message in session.get("messages") or []:
                    role = "Voce" if str(message.get("role")) == "user" else "BMO"
                    parts.append(f"{role}: {str(message.get('text') or '').strip()}\n")
        content = "\n".join(parts).strip() + ("\n" if parts else "")
        mime = "text/markdown" if export_format == "md" else "text/plain"
    return {"ok": True, "filename": filename, "format": export_format, "mime": mime, "content": content, "sessionCount": len(selected)}


def safe_upload_name(name: str, fallback: str) -> str:
    clean = Path(str(name or fallback)).name
    clean = re.sub(r"[^A-Za-z0-9_. -]", "_", clean).strip(" .")
    return clean or fallback


def decode_data_url(value: str) -> tuple[str, bytes]:
    header, encoded = value.split(",", 1)
    media_type = "application/octet-stream"
    if header.startswith("data:"):
        media_type = header[5:].split(";", 1)[0] or media_type
    return media_type, base64.b64decode(encoded)


def process_chat_attachments(raw_attachments: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_attachments, list):
        return []
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    processed: list[dict[str, Any]] = []
    for index, item in enumerate(raw_attachments[:12]):
        if not isinstance(item, dict):
            continue
        name = safe_upload_name(str(item.get("name") or ""), f"anexo_{index + 1}")
        media_type = str(item.get("type") or mimetypes.guess_type(name)[0] or "application/octet-stream")
        text_value = str(item.get("text") or "")
        content = b""
        try:
            url = str(item.get("url") or "")
            if url.startswith("data:") and "," in url:
                detected_type, content = decode_data_url(url)
                if not item.get("type"):
                    media_type = detected_type
            elif text_value:
                content = text_value.encode("utf-8")
                if media_type == "application/octet-stream":
                    media_type = "text/plain"
            else:
                continue
        except Exception as error:
            log_event("attachment_decode_failed", name=name, error=str(error))
            continue
        stamp = time.strftime("%Y%m%d_%H%M%S")
        target = UPLOADS_DIR / f"{stamp}_{uuid.uuid4().hex[:8]}_{name}"
        target.write_bytes(content)
        kind = "image" if media_type.startswith("image/") else "text" if media_type.startswith("text/") or target.suffix.lower() in {".txt", ".md", ".json", ".csv", ".py", ".html", ".css", ".js", ".ts"} else "file"
        entry: dict[str, Any] = {
            "name": name,
            "type": media_type,
            "kind": kind,
            "size": len(content),
            "path": str(target),
        }
        if kind == "text":
            entry["text"] = content.decode("utf-8", errors="replace")[:4000]
        processed.append(entry)
    return processed


def attachment_context(attachments: list[dict[str, Any]]) -> str:
    if not attachments:
        return ""
    lines = ["Anexos recebidos e salvos:"]
    for item in attachments:
        line = f"- {item.get('name')} ({item.get('kind')}, {item.get('type')}, {item.get('size')} bytes) em {item.get('path')}"
        if item.get("text"):
            line += f"\n  Conteudo: {str(item.get('text'))[:1200]}"
        elif item.get("kind") == "image":
            line += "\n  Imagem salva localmente para referencia."
        lines.append(line)
    return "\n".join(lines)


def make_session_title(text: str) -> str:
    clean = " ".join(text.strip().split())
    return "Nova conversa" if not clean else clean[:54] + ("..." if len(clean) > 54 else "")


def session_by_id(session_id: str | None) -> dict[str, Any] | None:
    if not session_id:
        return None
    return next((session for session in read_history() if session.get("id") == session_id), None)


def recent_context_messages(session_id: str | None) -> list[dict[str, str]]:
    session = session_by_id(session_id)
    if not session:
        return []
    selected = []
    total = 0
    for item in reversed(session.get("messages") or []):
        text = str(item.get("text") or "").strip()[:2500]
        if not text or total + len(text) > MAX_CONTEXT_CHARS:
            break
        role = "assistant" if str(item.get("role")) in {"bmo", "assistant"} else "user"
        selected.append({"role": role, "content": text})
        total += len(text)
        if len(selected) >= MAX_CONTEXT_MESSAGES:
            break
    selected.reverse()
    return selected


def clean_bmo_reply(text: str) -> str:
    clean = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    clean = re.sub(r"```[A-Za-z0-9_-]*\n(.*?)```", lambda m: m.group(1).strip(), clean, flags=re.S)
    clean = re.sub(r"`([^`]+)`", r"\1", clean)
    clean = re.sub(r"\*\*(.*?)\*\*", r"\1", clean, flags=re.S)
    clean = re.sub(r"__(.*?)__", r"\1", clean, flags=re.S)
    clean = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+)\*(?!\*)", r"\1", clean)
    clean = re.sub(r"^\s{0,3}#{1,6}\s*", "", clean, flags=re.M)
    clean = re.sub(r"^\s*[-*_]{3,}\s*$", "", clean, flags=re.M)
    clean = re.sub(r"^\s*[-*+]\s+", "- ", clean, flags=re.M)
    clean = re.sub(r"[ \t]{2,}", " ", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def folded(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or "").lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def join_pt(items: list[str]) -> str:
    clean = [item for item in items if item]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    return ", ".join(clean[:-1]) + " e " + clean[-1]


def clean_profile_value(value: str) -> str:
    clean = re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n.,!?;:-")
    clean = re.sub(r"(?i)\bpor\s+favor\b", "", clean).strip(" \t\r\n.,!?;:-")
    clean = re.sub(r"(?i)^(o|a|os|as|um|uma|uns|umas)\s+", "", clean).strip()
    return clean[:120]


def profile_label(raw_label: str) -> str:
    clean = re.sub(r"\s+", " ", folded(raw_label)).strip(" .,:;")
    known = {
        "nome": "Nome",
        "time favorito": "Time favorito",
        "jogo favorito": "Jogo favorito",
    }
    return known.get(clean, clean[:1].upper() + clean[1:])


def extract_profile_facts(message: str) -> list[tuple[str, str]]:
    text = " ".join(str(message or "").strip().split())
    if not text:
        return []
    stop = r"(?=\s+(?:e\s+)?(?:meu|minha|me chamo|eu me chamo|meu nome)|[,.!?;]|$)"
    patterns = [
        ("Nome", rf"\b(?:meu\s+nome\s+(?:e|\u00e9|\?)|me\s+chamo|eu\s+me\s+chamo|pode\s+me\s+chamar\s+de)\s+(.+?){stop}"),
        ("Time favorito", rf"\bmeu\s+time\s+favorito\s+(?:e|\u00e9|\?)\s+(.+?){stop}"),
        ("Jogo favorito", rf"\bmeu\s+jogo\s+favorito\s+(?:e|\u00e9|\?)\s+(.+?){stop}"),
    ]
    facts: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            value = clean_profile_value(match.group(1))
            key = folded(label)
            if value and key not in seen:
                facts.append((label, value))
                seen.add(key)
    generic_pattern = rf"\b(?:meu|minha)\s+([A-Za-z\u00c0-\u00ff0-9 _-]{{2,45}}?)\s+(?:e|\u00e9|\?)\s+(.+?){stop}"
    for match in re.finditer(generic_pattern, text, re.I):
        label = profile_label(match.group(1))
        key = folded(label)
        if key in seen or key in {"nome", "time favorito", "jogo favorito"}:
            continue
        value = clean_profile_value(match.group(2))
        if value:
            facts.append((label, value))
            seen.add(key)
    return facts


def upsert_profile_file(path: Path, facts: list[tuple[str, str]]) -> None:
    text = safe_read_text(path, "# Usuario\n\n")
    lines = text.splitlines()
    if not lines:
        lines = ["# Usuario", ""]
    heading = "## Perfil aprendido"
    try:
        heading_index = next(index for index, line in enumerate(lines) if line.strip().lower() == heading.lower())
    except StopIteration:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(heading)
        heading_index = len(lines) - 1
    section_end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            section_end = index
            break
    for label, value in facts:
        prefix = f"- {label}:"
        replacement = f"- {label}: {value}"
        replaced = False
        for index in range(heading_index + 1, section_end):
            if lines[index].strip().lower().startswith(prefix.lower()):
                lines[index] = replacement
                replaced = True
                break
        if not replaced:
            lines.insert(section_end, replacement)
            section_end += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def remember_profile_from_message(message: str) -> dict[str, Any] | None:
    facts = extract_profile_facts(message)
    if not facts:
        return None
    with memory_lock:
        for profile_path in (USER_MD, WORKSPACE_USER_MD):
            upsert_profile_file(profile_path, facts)
        MEMORY_MD.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_MEMORY_MD.parent.mkdir(parents=True, exist_ok=True)
        if not MEMORY_MD.exists():
            MEMORY_MD.write_text("# Memoria do BMO\n\n", encoding="utf-8")
        if not WORKSPACE_MEMORY_MD.exists():
            WORKSPACE_MEMORY_MD.write_text("# Memoria do BMO\n\n", encoding="utf-8")
        note_lines = [
            f"- {time.strftime('%Y-%m-%d %H:%M')}: Perfil atualizado: {label}: {value}\n"
            for label, value in facts
        ]
        for memory_path in (MEMORY_MD, WORKSPACE_MEMORY_MD):
            existing = safe_read_text(memory_path)
            with memory_path.open("a", encoding="utf-8") as file:
                for note in note_lines:
                    signature = note.split(": Perfil atualizado: ", 1)[-1].strip()
                    if signature not in existing[-6000:]:
                        file.write(note)
    labels = [
        {"Nome": "seu nome", "Time favorito": "seu time favorito", "Jogo favorito": "seu jogo favorito"}.get(label, f"seu {label.lower()}")
        for label, _value in facts
    ]
    return {
        "facts": [{"label": label, "value": value} for label, value in facts],
        "reply": f"Prontinho. Memorizei {join_pt(labels)}.",
    }


def asks_about_reminders(message: str) -> bool:
    lower = folded(message)
    return any(word in lower for word in ("lembrete", "lembrar", "remedio", "medicamento", "pressao"))


def remove_unrequested_reminders(reply: str, user_message: str) -> str:
    if asks_about_reminders(user_message):
        return reply
    blocks = re.split(r"\n\s*\n", reply)
    filtered = []
    for block in blocks:
        block_folded = folded(block)
        if any(word in block_folded for word in ("lembrete", "vou avisar", "medicamento", "remedio")):
            continue
        filtered.append(block)
    return "\n\n".join(filtered).strip() or reply


def summarize_file_creation_reply(text: str, user_message: str) -> str:
    """Se a mensagem pede criar arquivo e a resposta contem codigo longo, encurta."""
    if not re.search(r"\b(crie|cria|criar|gere|gerar|salve|salvar|faca|fazer|criar um|criar uma|substitua|crie um arquivo|crie uma)", folded(user_message)):
        return text
    # Se a resposta ja e curta, nao mexe
    if len(text) < 600:
        return text
    # Procurar nome de arquivo na mensagem
    name_match = re.search(r"([A-Za-z0-9_.-]+\.(?:py|txt|md|html|js|ts|jsx|tsx|css|json|csv))", user_message, re.I)
    if not name_match:
        # Ver se tem palavra-chave sobre criacao
        if not re.search(r"\b(codigo|criar|arquivo|programa|aplicativo|app|script|calcular)", user_message, re.I):
            return text
    # Encurtar — pegar so primeira linha se for longa
    lines = [l for l in text.split("\n") if l.strip()]
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # Se tem bloco de codigo, encurtar
        if line_stripped.startswith("```"):
            # Se o usuario pediu para mostrar codigo, mantem
            if "mostre o codigo" in user_message.lower() or "mostrar o codigo" in user_message.lower():
                return text
            # Extrair nome do arquivo da resposta
            name_hint = ""
            for prev_line in lines[:i]:
                m = re.search(r"([A-Za-z0-9_.-]+\\.(?:py|txt|md|html|js|ts|jsx|tsx|css|json|csv|html))", prev_line)
                if m:
                    name_hint = m.group(1)
                    break
            if name_hint:
                short = f"Criei {name_hint} no workspace."
            else:
                # Pega primeira linha significativa
                short_lines = [l for l in lines if l.strip() and not l.strip().startswith("```")]
                short = short_lines[0] if short_lines else "Criei o arquivo no workspace."
                short = short[:200]
            # Oferecer opcao de ler
            if "posso" not in short.lower() and "quer" not in short.lower():
                short += " Se quiser ver o codigo, e so pedir."
            return short
    return text


def finalize_bmo_reply(text: str, user_message: str) -> str:
    text = remove_unrequested_reminders(clean_bmo_reply(text), user_message)
    return summarize_file_creation_reply(text, user_message)


def text_for_speech(text: str) -> str:
    speech = clean_bmo_reply(text)
    speech = re.sub(r"^\s*[-\u2022]\s+", "", speech, flags=re.M)
    speech = re.sub(r"https?://\S+", "", speech)
    speech = re.sub(r"[*_`>#~|]+", "", speech)
    speech = re.sub(r"\s*\n+\s*", ". ", speech)
    speech = re.sub(r"\s{2,}", " ", speech)
    return speech.strip()


def wants_current_news(message: str) -> bool:
    lower = folded(message)
    news_words = ("noticia", "noticias", "manchete", "manchetes", "jornal", "acontecendo")
    current_words = ("hoje", "agora", "atual", "atuais", "ultima", "ultimas", "recente", "recentes")
    return any(word in lower for word in news_words) and any(word in lower for word in current_words)


def current_web_context(message: str) -> str:
    if not wants_current_news(message):
        return ""
    query = f"principais noticias Brasil mundo hoje {time.strftime('%d/%m/%Y')}"
    try:
        result = nanobot_original_tool("web_search", {"query": query, "count": 6})
        if result.get("ok") and result.get("result"):
            return str(result["result"])[:6000]
    except Exception as error:
        log_event("current_web_context_failed", error=str(error))
    return ""


# ---------------------------------------------------------------------------
# DEPRECATED: Motores de chat manuais antigos.
# Nao sao mais usados pelo fluxo principal de chat.
# O NanobotRuntime (via nanobot_integration.chat) e a unica via.
# Mantidos apenas como referencia — nao chamar.
# ---------------------------------------------------------------------------


def build_model_messages(message: str, language: str = "pt-BR", session_id: str | None = None) -> list[dict[str, str]]:
    context = recent_context_messages(session_id)
    transcript = "\n".join(f"{'BMO' if item['role'] == 'assistant' else 'Usuario'}: {item['content']}" for item in context)
    memory_sources = [
        ("Memoria do app", MEMORY_MD, 1600),
        ("Memoria Nanobot", WORKSPACE_MEMORY_MD, 2200),
    ]
    memory_blocks = []
    for title, path, limit in memory_sources:
        text = safe_read_text(path)[-limit:] if path.exists() else ""
        if text.strip():
            memory_blocks.append(f"{title}:\n{text.strip()}")
    user_profile = safe_read_text(WORKSPACE_USER_MD)[-1600:] if WORKSPACE_USER_MD.exists() else safe_read_text(USER_MD)[-1600:]
    soul_context = safe_read_text(WORKSPACE_SOUL_MD)[-1600:] if WORKSPACE_SOUL_MD.exists() else safe_read_text(SOUL_MD)[-1600:]
    language_line = "Responda em English." if language.lower().startswith("en") else "Responda em portugues do Brasil."
    web_context = current_web_context(message)
    system_content = (
        f"{BMO_SYSTEM_PROMPT}\n{language_line}\n\n"
        f"Alma/persona persistente:\n{soul_context or 'Sem alma persistente carregada.'}\n\n"
        f"Perfil persistente do usuario:\n{user_profile or 'Sem perfil persistente carregado.'}\n\n"
        f"Memoria persistente:\n{chr(10).join(memory_blocks) if memory_blocks else 'Sem memoria persistente.'}\n\n"
        f"Contexto da conversa atual:\n{transcript or 'Sem mensagens anteriores nesta sessao.'}\n\n"
        f"Contexto web atual:\n{web_context or 'Sem contexto web atual para esta mensagem.'}\n\n"
        "Responda como BMO, de forma natural, util e conectada ao contexto. "
        "Use frases curtas e diretas. Se precisar enumerar, use no maximo poucos itens.\n\n"
        "Voce tem ferramentas reais para ler/escrever arquivos, executar comandos permitidos, pesquisar e criar subagentes. "
        "Quando o usuario pedir para criar, salvar, abrir, executar, pesquisar ou delegar uma tarefa, use tool calls antes de responder. "
        "Para arquivos na area de trabalho, use create_file com location=desktop. "
        "Para jogos Python que o usuario pedir para abrir, crie uma interface Tkinter e execute com shell_exec em background=true. "
        "Nao crie jogos de terminal/input quando o pedido for abrir uma janela. "
        "Nunca diga que nao tem acesso ao sistema de arquivos, navegador ou subagentes quando uma ferramenta puder fazer a acao."
    )
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": message},
    ]


def save_chat_turn(session_id: str | None, user_text: str, reply_text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    now = int(time.time())
    with history_lock:
        sessions = read_history()
        selected = next((session for session in sessions if session.get("id") == session_id), None) if session_id else None
        if selected is None:
            selected = {"id": session_id or str(int(time.time() * 1000)), "title": make_session_title(user_text), "createdAt": now, "messages": []}
            sessions.insert(0, selected)
        selected["updatedAt"] = now
        selected["preview"] = reply_text[:140]
        if metadata:
            selected.setdefault("metadata", {}).update(metadata)
        selected.setdefault("messages", []).append({"role": "user", "text": user_text, "createdAt": now})
        selected.setdefault("messages", []).append({"role": "bmo", "text": reply_text, "createdAt": now})
        write_history(sessions)
    append_memory_note(user_text)
    try:
        nanobot_original_append_history(f"USER: {user_text}\nBMO: {reply_text}")
    except Exception as error:
        log_event("nanobot_history_append_failed", error=str(error))
    return selected


def request_json(url: str, payload: dict[str, Any] | None = None, timeout: float = 6, headers: dict[str, str] | None = None) -> dict[str, Any]:
    data = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw else {}


def friendly_http_error(error: urllib.error.HTTPError) -> str:
    detail = error.read().decode("utf-8", errors="replace")
    if error.code in {401, 403}:
        return "Chave invalida ou sem permissao para esse provedor."
    if error.code in {502, 503, 504}:
        return "Modelo temporariamente indisponivel no provedor."
    return f"Erro {error.code}: {detail[:260]}"


def windows_process_options() -> tuple[Any, int]:
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return startupinfo, creationflags


def ensure_runtime_config() -> Path:
    ensure_bmo_home_layout()
    config = load_nanobot_config()
    defaults = config.setdefault("agents", {}).setdefault("defaults", {})
    if not defaults.get("provider") or str(defaults.get("provider")).lower() in {"none", "null"}:
        defaults["provider"] = "openrouter"
    if not defaults.get("model"):
        defaults["model"] = "openai/gpt-oss-120b:free"
    # Usar variavel ${BMO_HOME} em vez de caminho fixo para builds distribuiveis
    defaults["workspace"] = "${BMO_HOME}/workspace"
    write_json(RUNTIME_CONFIG, config)
    write_json(NANOBOT_RUNTIME_CONFIG, sanitize_nanobot_runtime_config(config))
    os.environ["NANOBOT_CONFIG_PATH"] = str(NANOBOT_RUNTIME_CONFIG)
    return NANOBOT_RUNTIME_CONFIG


def bmo_compat_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "Cria ou substitui um arquivo real no workspace do BMO ou na area de trabalho do usuario.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Nome ou caminho do arquivo. Exemplo: teste.txt ou jogo_da_velha.py."},
                        "content": {"type": "string", "description": "Conteudo completo que sera gravado no arquivo."},
                        "location": {"type": "string", "enum": ["workspace", "desktop"], "description": "Use desktop quando o usuario pedir area de trabalho."},
                        "overwrite": {"type": "boolean", "description": "Se true, substitui arquivo existente."},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "shell_exec",
                "description": "Executa comando permitido no workspace do BMO. Use para rodar arquivos Python criados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Comando permitido, como python jogo_da_velha.py."},
                        "cwd": {"type": "string", "description": "Pasta relativa ao workspace. Deixe vazio para a raiz do workspace."},
                        "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
                        "background": {"type": "boolean", "description": "Use true para abrir jogos ou apps sem bloquear a conversa."},
                    },
                    "required": ["command"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_subagent",
                "description": "Cria um subagente/tarefa delegada que aparece na lista de subagentes do BMO.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Titulo curto do subagente."},
                        "objective": {"type": "string", "description": "Objetivo completo do subagente."},
                        "command": {"type": "string", "description": "Comando opcional para executar em background."},
                    },
                    "required": ["objective"],
                    "additionalProperties": False,
                },
            },
        },
    ]


def llm_tool_definitions() -> list[dict[str, Any]]:
    payload = nanobot_original_registry()
    definitions = [item for item in payload.get("definitions", []) if isinstance(item, dict)]
    seen = set()
    result = []
    for definition in [*definitions, *bmo_compat_tool_definitions()]:
        fn = definition.get("function") if isinstance(definition, dict) else None
        name = str((fn or {}).get("name") or "")
        if not name or name in seen:
            continue
        seen.add(name)
        result.append(definition)
    return result


def parse_tool_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as error:
        log_event("tool_arguments_parse_failed", error=str(error), raw=str(raw)[:500])
        return {}


def tool_result_content(result: Any) -> str:
    text = json.dumps(result, ensure_ascii=False, default=str)
    if len(text) > 16000:
        return text[:16000] + "... [resultado truncado]"
    return text


def create_file_tool(params: dict[str, Any]) -> dict[str, Any]:  # DEPRECATED
    location = str(params.get("location") or "workspace").lower()
    raw_path = str(params.get("path") or "").strip()
    if not raw_path:
        raise RuntimeError("path e obrigatorio.")
    content = str(params.get("content") or "")
    overwrite = bool(params.get("overwrite", True))
    if location == "desktop":
        target = DESKTOP_DIR / Path(raw_path).name
        if target.exists() and not overwrite:
            raise RuntimeError("Arquivo ja existe e overwrite=false.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="")
        return {"ok": True, "path": str(target), "location": "desktop", "size": target.stat().st_size}
    result = native_tools.write_file(tool_context(), raw_path, content, append=False, overwrite=overwrite)
    result["location"] = "workspace"
    return result


def normalize_python_script_args(args: list[str], workdir: Path) -> list[str]:
    normalized = list(args)
    for index, value in enumerate(normalized[1:], start=1):
        clean = str(value).strip('"')
        if not clean.lower().endswith(".py"):
            continue
        script_path = Path(clean)
        if script_path.is_absolute():
            continue
        candidates = [workdir / script_path, RUNTIME_WORKSPACE / script_path, DESKTOP_DIR / script_path.name]
        selected = next((candidate for candidate in candidates if candidate.exists()), None)
        if selected:
            normalized[index] = str(selected)
    return normalized


def shell_exec_tool(params: dict[str, Any]) -> dict[str, Any]:  # DEPRECATED
    ctx = tool_context()
    command_text = str(params.get("command") or "")
    user_message = folded(str(params.get("_user_message") or ""))
    background = bool(params.get("background"))
    args = native_tools._split_command(command_text)  # type: ignore[attr-defined]
    if not args:
        raise RuntimeError("Comando vazio.")
    workdir = native_tools.resolve_workspace_path(ctx, str(params.get("cwd") or ""), must_exist=True)
    args = normalize_python_script_args(args, workdir)
    if not background and re.search(r"\.py(?:\s|$|\"|')", command_text, re.I) and re.search(r"\b(abrir|abre|jogo|game|interface|janela)\b", user_message):
        background = True
    if not background:
        return native_tools.shell_exec(
            ctx,
            args,
            str(workdir),
            int(params.get("timeout") or 30),
        )
    executable = Path(args[0].strip('"')).name.lower()
    if executable not in native_tools.ALLOWED_COMMANDS:
        raise RuntimeError(f"Comando nao permitido pelo sandbox: {executable}")
    if executable in {"python", "python.exe", "py", "py.exe"} and any(str(part).lower().endswith(".py") for part in args[1:]):
        pythonw = shutil.which("pythonw") or shutil.which("pythonw.exe")
        if pythonw:
            args[0] = pythonw
    startupinfo, creationflags = windows_process_options()
    proc = subprocess.Popen(
        args,
        cwd=str(workdir),
        env={**os.environ, **ctx.env},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    return {"ok": True, "pid": proc.pid, "cwd": str(workdir), "command": args, "background": True}


def subagent_search_query(objective: str) -> str:
    """Extrai apenas a consulta de busca do objetivo, removendo instrucoes operacionais."""
    clean = re.sub(r"\s+", " ", str(objective or "")).strip(" .")
    # Remove instrucoes operacionais
    clean = re.sub(r"(?i)\bpor\s+favor\b", "", clean).strip(" .")
    clean = re.sub(r"(?i)^(crie|cria|criar|gere|gerar)\s+(um\s+|uma\s+)?subagente\s+(de\s+|para\s+)?", "", clean).strip()
    clean = re.sub(r"(?i)^para\s+", "", clean).strip()
    clean = re.sub(r"(?i)^(pesquisar|pesquise|buscar|busque|procurar|procure|analisar|analise|levantar|levante|coletar|colete)\s+(sobre\s+)?", "", clean).strip()
    # Remove comandos de operacao (salve, crie arquivo, etc)
    clean = re.sub(r"(?i)\b(salve|salvar|armazene|armazenar|escreva|escrever|crie|criar|gere|gerar|monte|montar|fa[çc]a|fazer|grave|gravar|liste|listar|compile|compilar)\s+(em\s+|no\s+|na\s+|um\s+|uma\s+)?(arquivo|relat[oó]rio|resumo|lista|tabela|md|json|csv|txt|docx|xlsx|pdf|markdown|arquivo\.md|arquivo\.txt|arquivo\.json|.md|.txt|.json)\b", "", clean).strip()
    clean = re.sub(r"(?i)\be\s+(salve|armazene|crie|escreva|monte|fa[çc]a|gere|grave|liste|compile)\b.*$", "", clean).strip()
    clean = re.sub(r"(?i)\bcom\s+(os\s+|as\s+|o\s+|a\s+)?(resultados|fontes|links|dados|informa[çc][õo]es|itens|texto|cita[çc][õo]es|refer[eê]ncias|urls)\b.*$", "", clean).strip()
    clean = re.sub(r"(?i)\sem\s+(formato|formato\s+de|arquivo|modo)\s+\w+\s*$", "", clean).strip()
    clean = re.sub(r"(?i)\bsalve\s+em\s+.*$", "", clean).strip()
    clean = re.sub(r"(?i)\bcrie\s+um\s+arquivo\s+.*$", "", clean).strip()
    # Remove frases como "sobre", "a respeito de" no inicio
    clean = re.sub(r"(?i)^(sobre|a\s+respeito\s+de|acerca\s+de|referente\s+a)\s+", "", clean).strip()
    # Limpa trailing prepositions and conjunctions
    clean = re.sub(r"\s+(e|ou|mas|por|para|em|no|na|nos|nas|de|do|da|dos|das|com|sem|sobre)\s*$", "", clean).strip()
    return clean[:240] or "pesquisa solicitada pelo usuario"


def normalized_search_items(payload: Any) -> tuple[list[dict[str, str]], str]:
    items: list[dict[str, str]] = []
    raw_text = ""
    if isinstance(payload, dict):
        if isinstance(payload.get("result"), (dict, list, str)):
            nested_items, nested_raw = normalized_search_items(payload.get("result"))
            items.extend(nested_items)
            raw_text = nested_raw or raw_text
        for raw_item in payload.get("results", []) if isinstance(payload.get("results"), list) else []:
            if not isinstance(raw_item, dict):
                continue
            title = re.sub(r"\s+", " ", str(raw_item.get("title") or raw_item.get("name") or "")).strip()
            url = re.sub(r"\s+", " ", str(raw_item.get("url") or raw_item.get("href") or raw_item.get("link") or "")).strip()
            snippet = re.sub(r"\s+", " ", str(raw_item.get("snippet") or raw_item.get("summary") or raw_item.get("body") or "")).strip()
            if title or url:
                items.append({"title": title or url, "url": url, "snippet": snippet})
    elif isinstance(payload, list):
        for raw_item in payload:
            nested_items, nested_raw = normalized_search_items(raw_item)
            items.extend(nested_items)
            raw_text = nested_raw or raw_text
    elif isinstance(payload, str):
        raw_text = payload.strip()
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        key = folded(item.get("url") or item.get("title") or "")
        if key and key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped[:10], raw_text


def format_subagent_report(
    title: str,
    objective: str,
    query: str,
    items: list[dict[str, str]],
    raw_text: str,
) -> str:
    timestamp = datetime.now(SAO_PAULO_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    lines = [
        "# Resultado do subagente",
        "",
        f"Titulo: {title}",
        f"Objetivo: {objective}",
        f"Consulta usada: {query}",
        f"Concluido em: {timestamp}",
        "",
        "## Resultados",
        "",
    ]
    if items:
        for index, item in enumerate(items, start=1):
            lines.append(f"{index}. {item.get('title') or 'Resultado sem titulo'}")
            if item.get("url"):
                lines.append(f"   Fonte: {item['url']}")
            if item.get("snippet"):
                lines.append(f"   Resumo: {item['snippet']}")
            lines.append("")
    elif raw_text:
        lines.append(raw_text[:12000])
        lines.append("")
    else:
        lines.append("Nenhum resultado foi retornado pelas ferramentas de pesquisa.")
        lines.append("")
    lines.append("## Observacao")
    lines.append("")
    lines.append("O subagente registrou fontes e resultados encontrados pelas ferramentas disponiveis no momento da execucao.")
    return "\n".join(lines).strip() + "\n"


def subagent_summary(query: str, items: list[dict[str, str]], raw_text: str) -> str:
    if items:
        titles = [item.get("title", "").strip() for item in items[:3] if item.get("title")]
        if titles:
            return f"Pesquisa concluida para '{query}'. Principais resultados: {join_pt(titles)}."
        return f"Pesquisa concluida para '{query}' com {len(items)} resultado(s)."
    if raw_text:
        first_line = next((line.strip() for line in raw_text.splitlines() if line.strip()), "")
        return f"Pesquisa concluida para '{query}'. {first_line[:180]}"
    return f"Pesquisa concluida para '{query}', mas nenhuma fonte foi retornada."


def _parallel_search(query: str, ctx: native_tools.ToolContext) -> tuple[list[dict[str, str]], str]:
    """Executa buscas em paralelo (Nanobot + nativa) e retorna itens combinados."""
    all_items: list[dict[str, str]] = []
    raw_text = ""
    results = [None]

    def _search_nanobot():
        nonlocal results
        try:
            original = nanobot_original_tool("web_search", {"query": query, "count": 10})
            items, raw = normalized_search_items(original)
            results = [items, raw]
        except Exception as error:
            log_event("subagent_nanobot_search_failed", query=query, error=str(error))
            results = [None, None]

    def _search_native():
        nonlocal results
        try:
            native_result = native_tools.web_search(ctx, query, 10)
            items, raw = normalized_search_items(native_result)
            results = [items, raw]
        except Exception as error:
            log_event("subagent_native_search_failed", query=query, error=str(error))
            results = [None, None]

    threads = []
    for target in (_search_nanobot, _search_native):
        t = threading.Thread(target=target, daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=30)
    return all_items, raw_text


def run_research_subagent(
    ctx: native_tools.ToolContext,
    task_id: str,
    output_file: Path,
    update: Any,
    title: str,
    objective: str,
) -> dict[str, Any]:
    query = subagent_search_query(objective)
    update(progress=25)
    all_items, raw_text = _parallel_search(query, ctx)
    all_items, _unused = normalized_search_items({"results": all_items})
    if not all_items and not raw_text:
        raise RuntimeError("Nenhuma ferramenta de pesquisa retornou resultado para o subagente.")
    update(progress=82)
    report = format_subagent_report(title, objective, query, all_items, raw_text)
    output_file.write_text(report, encoding="utf-8")
    summary = subagent_summary(query, all_items, raw_text)
    log_event("subagent_completed", id=task_id, title=title, query=query, output=str(output_file), results=len(all_items))
    return {
        "ok": True,
        "message": "Subagente concluiu a tarefa.",
        "summary": summary,
        "outputPath": str(output_file),
        "query": query,
        "results": len(all_items),
    }


def make_subagent_runner(title: str, objective: str) -> Any:
    def runner(ctx: native_tools.ToolContext, task_id: str, output_file: Path, update: Any) -> dict[str, Any]:
        return run_research_subagent(ctx, task_id, output_file, update, title, objective)

    return runner


def create_subagent_tool(params: dict[str, Any]) -> dict[str, Any]:  # DEPRECATED
    objective = str(params.get("objective") or params.get("task") or params.get("prompt") or params.get("title") or "Pesquisa do BMO").strip()
    title = str(params.get("title") or params.get("label") or objective or "Subagente BMO").strip()
    command = str(params.get("command") or "").strip()
    # ------------------------------------------------------------------
    # CORRECAO: usa o nanobot_bridge para criar um subagente real que
    # roda via AgentLoop do nanobot em thread separada.
    # ------------------------------------------------------------------
    try:
        nanobot_config_path = ensure_runtime_config()
        spawn_result = nanobot_integration.spawn_subagent(task=objective, label=title)
        if spawn_result.get("ok"):
            log_event("subagent_spawned_via_integration", title=title, id=spawn_result.get("id"))
            return spawn_result
    except Exception as error:
        log_event("subagent_nanobot_spawn_failed", title=title, error=str(error))
    # Fallback: runner nativo de pesquisa
    payload: dict[str, Any] = {"title": title, "objective": objective, "command": command}
    if not command:
        payload["_runner"] = make_subagent_runner(title, objective)
    return native_tools.longtask_start(tool_context(), payload)


def execute_llm_tool(name: str, params: dict[str, Any], user_message: str = "") -> dict[str, Any]:  # DEPRECATED
    try:
        if name == "create_file":
            result = create_file_tool(params)
        elif name == "shell_exec":
            result = shell_exec_tool({**params, "_user_message": user_message})
        elif name in {"create_subagent", "spawn"}:
            result = create_subagent_tool(params)
        else:
            result = nanobot_original_tool(name, params)
        log_event("llm_tool_executed", tool=name, ok=bool(result.get("ok", True)))
        return {"ok": True, "tool": name, "result": result}
    except Exception as error:
        log_event("llm_tool_failed", tool=name, error=str(error))
        return {"ok": False, "tool": name, "error": str(error)}


def fallback_tool_reply(tool_results: list[dict[str, Any]], user_message: str) -> str:
    successful = [item for item in tool_results if item.get("ok")]
    if not successful:
        return ""
    tools = {str(item.get("tool") or "") for item in successful}
    if tools & {"create_subagent", "spawn"}:
        return "Prontinho. Criei o subagente e ele ja esta trabalhando. Vou avisar quando o resultado estiver salvo."
    file_paths = []
    process_started = False
    for item in successful:
        result = item.get("result") if isinstance(item.get("result"), dict) else {}
        if isinstance(result, dict) and result.get("path"):
            file_paths.append(str(result["path"]))
        if isinstance(result, dict) and result.get("pid"):
            process_started = True
    if file_paths and process_started:
        return f"Prontinho. Criei o arquivo {Path(file_paths[-1]).name} e ja abri para voce."
    if file_paths:
        return f"Prontinho. Criei o arquivo {Path(file_paths[-1]).name}."
    if "shell_exec" in tools:
        return "Prontinho. Executei o comando solicitado."
    return "Prontinho. Executei a tarefa solicitada."


def direct_provider_chat(provider: str, model: str, api_key: str, message: str, language: str, session_id: str | None) -> str:  # DEPRECATED
    if provider == "openrouter":
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "HTTP-Referer": "http://localhost/bmo", "X-Title": "BMO"}
    elif provider == "openai":
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
    else:
        raise RuntimeError(f"Fallback direto nao suporta {provider}.")
    messages: list[dict[str, Any]] = build_model_messages(message, language, session_id)
    tools = llm_tool_definitions()
    reply = ""
    tool_results: list[dict[str, Any]] = []
    for _round in range(MAX_TOOL_CALL_ROUNDS):
        payload: dict[str, Any] = {"model": model, "messages": messages, "max_tokens": DIRECT_CHAT_MAX_TOKENS, "stream": False}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        try:
            data = request_json(endpoint, payload, timeout=120, headers=headers)
        except Exception as error:
            fallback = fallback_tool_reply(tool_results, message)
            if fallback:
                log_event("tool_final_reply_fallback", error=str(error))
                return finalize_bmo_reply(fallback, message)
            raise
        choices = data.get("choices") or []
        if not choices:
            break
        assistant_message = choices[0].get("message") or {}
        tool_calls = assistant_message.get("tool_calls") or []
        if tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_message.get("content") or "",
                "tool_calls": tool_calls,
            })
            for call in tool_calls:
                function = call.get("function") if isinstance(call, dict) else {}
                name = str((function or {}).get("name") or "")
                params = parse_tool_arguments((function or {}).get("arguments"))
                result = execute_llm_tool(name, params, message)
                tool_results.append(result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": str(call.get("id") or uuid.uuid4().hex),
                    "name": name,
                    "content": tool_result_content(result),
                })
            continue
        reply = str(assistant_message.get("content") or "").strip()
        break
    if not reply:
        reply = fallback_tool_reply(tool_results, message)
    return finalize_bmo_reply(reply, message)


def ask_provider_direct(message: str, language: str, session_id: str | None, previous_error: str = "") -> str:  # DEPRECATED
    provider = active_provider()
    keys = provider_secret_values(provider)
    if provider not in {"openrouter", "openai"} or not keys:
        raise RuntimeError(previous_error or "Nenhuma chave de API configurada para o BMO.")
    last_error = previous_error
    for key_index, api_key in enumerate(keys):
        with provider_key_lock:
            active_provider_key_index[provider] = key_index
        for model in configured_models():
            try:
                reply = direct_provider_chat(provider, model, api_key, message, language, session_id)
                if reply:
                    return reply
            except urllib.error.HTTPError as error:
                last_error = friendly_http_error(error)
                log_event("provider_model_http_failed", provider=provider, model=model, status=error.code, error=last_error)
                if error.code in {401, 403}:
                    break
            except Exception as error:
                last_error = str(error)
                log_event("provider_model_failed", provider=provider, model=model, error=last_error)
    raise RuntimeError(last_error or "BMO nao conseguiu responder agora.")


def fallback_blocked(detail: str, session_id: str | None = None) -> None:
    """Registra no log que o fallback manual foi bloqueado.
    O NanobotRuntime e a UNICA via de processamento de chat.
    O codigo legado (direct_provider_chat, build_model_messages, etc)
    nao deve mais ser chamado para responder usuarios.
    """
    log_event("fallback_blocked", detail=detail, session=session_id, action="blocked")


def ask_nanobot(message: str, language: str = "pt-BR", session_id: str | None = None) -> str:
    """Usa o AgentLoop real do Nanobot para processar a mensagem.
    ATENCAO: Nao usa mais fallback manual. Se NanobotRuntime falhar,
    retorna mensagem de erro clara para o usuario.
    """
    t0 = time.perf_counter()
    try:
        reply = nanobot_integration.chat(message, session_id, language)
        elapsed = round(time.perf_counter() - t0, 2)
        if reply:
            log_event("nanobot_runtime_used", session=session_id, elapsed_seconds=elapsed, reply_len=len(reply))
            return reply
    except Exception as e:
        detail = str(e)
        log_event("nanobot_runtime_failed", error=detail, session=session_id)
        # Nao usa mais o fallback manual (direct_provider_chat).
        # O NanobotRuntime e a unica via de processamento.
        fallback_blocked(detail, session_id)
        return "Eu tropecei nos meus circuitos agora. Verifica se minha conexao com o modelo de IA esta funcionando em Provedores e tenta de novo."


def provider_test_result(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    provider = str(payload.get("provider") or active_provider()).lower()
    model = str(payload.get("model") or active_model())
    keys = split_secret_values(str(payload.get("apiKey") or "")) or provider_secret_values(provider)
    if provider == "ollama":
        try:
            request_json("http://127.0.0.1:11434/api/tags", timeout=3)
            return {"ok": True, "message": "Ollama rodando."}
        except Exception as error:
            log_event("provider_test_ollama_failed", error=str(error))
            return {"ok": False, "message": "Ollama nao esta rodando."}
    if provider not in {"openrouter", "openai"}:
        return {"ok": bool(keys), "message": "Provider salvo." if keys else "Chave ausente."}
    if not keys:
        return {"ok": False, "message": f"Chave de API ausente para {provider}."}
    try:
        direct_provider_chat(provider, model, keys[0], "ping", "pt-BR", None)
        return {"ok": True, "message": "Conexao OK."}
    except urllib.error.HTTPError as error:
        message = friendly_http_error(error)
        log_event("provider_test_http_failed", provider=provider, model=model, error=message)
        return {"ok": False, "message": message}
    except Exception as error:
        log_event("provider_test_failed", provider=provider, model=model, error=str(error))
        return {"ok": False, "message": str(error)}


def speak_text(text: str, voice: str = "") -> dict[str, Any]:
    speech = text_for_speech(text)
    if not speech:
        raise RuntimeError("Texto vazio para falar.")
    selected = PIPER_ROOT / (voice or PIPER_MODEL.name)
    if not selected.exists():
        selected = PIPER_MODEL
    if not PIPER_EXE.exists() or not selected.exists():
        raise RuntimeError("Piper ou modelo de voz nao encontrado.")
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = VOICE_DIR / "bmo_reply.wav"
    startupinfo, creationflags = windows_process_options()
    command = [str(PIPER_EXE), "--model", str(selected), "--output_file", str(wav_path), "--espeak_data", str(PIPER_ESPEAK), "--quiet"]
    subprocess.run(command, input=speech, text=True, encoding="utf-8", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, startupinfo=startupinfo, creationflags=creationflags, timeout=300)
    if os.name == "nt":
        import winsound
        winsound.PlaySound(str(wav_path), winsound.SND_FILENAME)
    return {"ok": True, "audio": str(wav_path), "voice": selected.name}


def select_ui_sound(kind: str, language: str = "pt-BR") -> Path | None:
    folder = {"startup": "greeting_sounds", "thinking": "thinking_sounds", "ack": "ack_sounds"}.get(kind, "ack_sounds")
    folder_path = SOUNDS_ROOT / folder
    paths = list(folder_path.glob("*.wav")) if folder_path.exists() else []
    if not paths:
        return None
    wants_pt = language.lower().startswith("pt")

    def priority(path: Path) -> tuple[int, str]:
        name = path.name.lower()
        score = 100
        if wants_pt:
            if kind == "startup" and name == "bmo_quem_quer_jogar_videogame_pt.wav":
                score = 0
            elif kind == "startup" and name == "videogames_pt.wav":
                score = 5
            elif name.endswith("_pt.wav"):
                score = 10
            elif "_en" in name or name.endswith("_en.wav"):
                score = 80
        else:
            if "_en" in name or not name.endswith("_pt.wav"):
                score = 0
            elif name.endswith("_pt.wav"):
                score = 60
        return score, name

    return sorted(paths, key=priority)[0]


def play_ui_sound(kind: str, language: str = "pt-BR") -> dict[str, Any]:
    selected = select_ui_sound(kind, language)
    if not selected:
        return {"ok": False, "message": "Som nao encontrado."}
    if os.name == "nt":
        import winsound
        winsound.PlaySound(str(selected), winsound.SND_FILENAME | winsound.SND_ASYNC)
    return {"ok": True, "path": str(selected)}


def record_microphone(seconds: float = 5.0, samplerate: int = 16000) -> Path:
    import numpy as np
    import sounddevice as sd
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = VOICE_DIR / "input.wav"
    recording = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    if recording is None or not recording.size or int(np.max(np.abs(recording))) < 80:
        raise RuntimeError("Nenhuma fala detectada.")
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(samplerate)
        wav.writeframes(recording.tobytes())
    return wav_path


def run_whisper_command(command: list[str], mode: str) -> str:
    global last_whisper_backend, last_whisper_error
    startupinfo, creationflags = windows_process_options()
    result = subprocess.run(command, cwd=str(WHISPER_EXE.parent), text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags, timeout=120)
    with whisper_state_lock:
        last_whisper_backend = mode
    if result.returncode != 0:
        error_text = result.stderr.strip() or result.stdout.strip()
        with whisper_state_lock:
            last_whisper_error = error_text
        raise RuntimeError(f"Whisper falhou ({result.returncode}): {error_text}")
    text = result.stdout.strip()
    if not text:
        with whisper_state_lock:
            last_whisper_error = "Nenhuma fala detectada."
            error_text = last_whisper_error
        raise RuntimeError(error_text)
    with whisper_state_lock:
        last_whisper_error = ""
    return text


def transcribe_wav(wav_path: Path, language: str = "pt") -> str:
    if not WHISPER_EXE.exists():
        raise RuntimeError("whisper-cli.exe nao encontrado.")
    model_path = resolve_whisper_model_path()
    if not model_path.exists():
        raise RuntimeError("Modelo Whisper nao encontrado.")
    base = [str(WHISPER_EXE), "--model", str(model_path), "--file", str(wav_path), "--language", language, "--no-timestamps", "--no-prints"]
    cfg = whisper_config()
    if cfg["gpu_enabled"] and whisper_gpu_backends():
        try:
            return run_whisper_command(base, "gpu")
        except Exception as error:
            log_event("whisper_gpu_failed", error=str(error))
            if not cfg["fallback_to_cpu"]:
                raise
    return run_whisper_command([*base, "--no-gpu"], "cpu")


def listen_once(seconds: float = 5.0) -> str:
    wav_path = record_microphone(seconds=seconds)
    try:
        return transcribe_wav(wav_path, "pt")
    except Exception as error:
        log_event("whisper_pt_failed", error=str(error))
        return transcribe_wav(wav_path, "en")


def test_whisper_runtime() -> dict[str, Any]:
    try:
        wav_path = VOICE_DIR / "whisper_test.wav"
        VOICE_DIR.mkdir(parents=True, exist_ok=True)
        with wave.open(str(wav_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\0\0" * 16000)
        transcribe_wav(wav_path, "pt")
        status = whisper_status()
        return {"ok": True, "mode": status["lastMode"], "message": f"Whisper respondeu usando {status['lastMode']}.", "whisper": status}
    except Exception as error:
        log_event("whisper_test_failed", error=str(error))
        status = whisper_status()
        return {"ok": False, "mode": status["lastMode"], "message": str(error), "whisper": status}


def wakeword_loop() -> None:
    block_size = 1280
    cooldown_until = 0.0
    consecutive_failures = 0
    while True:
        try:
            if not WAKEWORD_MODEL.exists():
                set_wakeword_state(available=False, dependency=False, running=False, enabled=False, model=str(WAKEWORD_MODEL), message="Modelo wakeword.onnx nao encontrado.")
                log_event("wake_word_unavailable", error="model_not_found", model=str(WAKEWORD_MODEL))
                time.sleep(30)
                continue
            import numpy as np
            import sounddevice as sd
            from openwakeword.model import Model

            # Listar dispositivos de entrada validos
            all_devices = sd.query_devices()
            input_devices = [
                (idx, dev.get("name", f"Microfone {idx}"))
                for idx, dev in enumerate(all_devices)
                if int(dev.get("max_input_channels", 0)) > 0
            ]
            if not input_devices:
                msg = "Nenhum microfone encontrado. Configure um microfone no painel de Voz."
                set_wakeword_state(available=False, dependency=False, running=False, enabled=False, lastError="no_microphone", message=msg)
                log_event("wake_word_no_microphone")
                time.sleep(15)
                continue

            mic = sd.query_devices(kind="input")
            if mic is None or (isinstance(mic, dict) and mic.get("name", "").startswith("device -1")):
                msg = "Microfone nao configurado. Selecione um dispositivo no painel de Voz."
                set_wakeword_state(available=False, dependency=False, running=False, enabled=False, lastError="no_default_input", message=msg)
                log_event("wake_word_no_default_device", devices=[d[1] for d in input_devices[:5]])
                time.sleep(15)
                continue

            mic_name = mic.get("name", "microfone padrao")
            set_wakeword_state(available=True, dependency=True, running=True, enabled=True, model=str(WAKEWORD_MODEL), message=f"Escutando Hey BMO em {mic_name}.", lastError="")
            log_event("wake_word_started", model=str(WAKEWORD_MODEL), microphone=mic_name)
            model = Model(wakeword_models=[str(WAKEWORD_MODEL)])
            consecutive_failures = 0
            with sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=block_size) as stream:
                while True:
                    audio, _overflowed = stream.read(block_size)
                    prediction = model.predict(np.asarray(audio).reshape(-1))
                    score = max([float(value) for value in prediction.values()] or [0.0])
                    now = time.time()
                    if score >= 0.55 and now >= cooldown_until:
                        cooldown_until = now + 2.5
                        with wakeword_lock:
                            wakeword_state["eventId"] = int(wakeword_state.get("eventId", 0)) + 1
                        log_event("wake_word_detected", phrase="Hey BMO", score=round(score, 4))
                    time.sleep(0.1)
        except Exception as error:
            consecutive_failures += 1
            error_str = str(error)
            # Se for erro de device -1, mensagem mais amigavel
            if "-1" in error_str or "device" in error_str.lower():
                msg = "Microfone nao configurado. Selecione um microfone no painel de Voz."
            else:
                msg = f"Wake word falhou: {error_str}"
            set_wakeword_state(running=False, enabled=False, lastError=error_str, message=msg)
            log_event("wake_word_error", error=error_str, consecutive=consecutive_failures)
            sleep_time = min(5 * consecutive_failures, 60)  # backoff: 5s, 10s, 15s... ate 60s
            time.sleep(sleep_time)


def reminders_status(due_only: bool = False) -> dict[str, Any]:
    with reminders_lock:
        items = read_items(REMINDERS_FILE)
    now = int(time.time())
    if due_only:
        items = [item for item in items if not item.get("completed") and not item.get("notified") and int(item.get("dueAt") or 0) <= now]
    return {"items": items}


def update_reminder(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "create")
    with reminders_lock:
        items = read_items(REMINDERS_FILE)
        if action == "create":
            items.append({"id": uuid.uuid4().hex[:12], "text": str(payload.get("text") or "Lembrete"), "dueAt": int(payload.get("dueAt") or time.time() + 60), "createdAt": int(time.time()), "completed": False, "notified": False})
        elif action == "notify":
            for item in items:
                if item.get("id") == payload.get("id"):
                    item["notified"] = True
        elif action == "complete":
            for item in items:
                if item.get("id") == payload.get("id"):
                    item["completed"] = True
        elif action == "snooze":
            for item in items:
                if item.get("id") == payload.get("id"):
                    item["dueAt"] = int(time.time()) + int(payload.get("minutes") or 5) * 60
                    item["notified"] = False
                    item["backendFired"] = False
                    item.pop("firedAt", None)
        elif action == "delete":
            items = [item for item in items if item.get("id") != payload.get("id")]
        write_items(REMINDERS_FILE, items)
        return {"items": items}


def reminder_due_label(due_at: int) -> str:
    return datetime.fromtimestamp(due_at, SAO_PAULO_TZ).isoformat()


def fire_due_reminders_once() -> None:
    fired: list[tuple[str, int]] = []
    with reminders_lock:
        items = read_items(REMINDERS_FILE)
        now = int(time.time())
        changed = False
        for item in items:
            due_at = int(item.get("dueAt") or 0)
            if item.get("completed") or item.get("backendFired") or due_at > now:
                continue
            text = str(item.get("text") or "Lembrete")
            item["backendFired"] = True
            item["firedAt"] = now
            changed = True
            log_event("reminder_fired", text=text, scheduled_for=reminder_due_label(due_at))
            fired.append((text, due_at))
        if changed:
            write_items(REMINDERS_FILE, items)
    for text, _due_at in fired:
        try:
            speak_text(f"Ei. Lembrete: {text}")
        except Exception as error:
            log_event("reminder_voice_failed", text=text, error=str(error))


def reminder_loop() -> None:
    while True:
        try:
            fire_due_reminders_once()
        except Exception as error:
            log_event("reminder_loop_error", error=str(error))
        time.sleep(1)


def tasks_status() -> dict[str, Any]:
    with tasks_lock:
        return {"items": read_items(TASKS_FILE)}


def update_tasks(payload: dict[str, Any]) -> dict[str, Any]:
    with tasks_lock:
        items = read_items(TASKS_FILE)
        action = str(payload.get("action") or "create")
        if action == "create":
            items.append({"id": uuid.uuid4().hex[:10], "title": str(payload.get("text") or payload.get("title") or "Tarefa"), "status": "pendente", "createdAt": int(time.time())})
        elif action == "delete":
            items = [item for item in items if item.get("id") != payload.get("id")]
        elif action == "complete":
            for item in items:
                if item.get("id") == payload.get("id"):
                    item["status"] = "concluida"
        write_items(TASKS_FILE, items)
        return {"items": items}


def nanobot_subagent_items() -> list[dict[str, Any]]:
    store = APP_DATA_DIR / "nanobot" / "subagents.json"
    if not store.exists():
        return []
    try:
        data = json.loads(safe_read_text(store, "{}"))
        items = data.get("items") or [] if isinstance(data, dict) else []
    except Exception as error:
        log_event("nanobot_subagents_read_failed", error=str(error))
        return []
    now = int(time.time())
    result = []
    stale_ids: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "")
        agent_status = str(item.get("status") or "")
        created_at = item.get("createdAt") or 0
        notified = bool(item.get("notified"))
        
        # Subagentes finished e notificados com mais de 60s: limpar
        if agent_status in {"concluido", "erro", "cancelado"} and notified and created_at and (now - int(created_at) > 60):
            stale_ids.append(item_id)
            continue
        # Subagentes finished nao notificados com mais de 120s: limpar tb
        if agent_status in {"concluido", "erro", "cancelado"} and not notified and created_at and (now - int(created_at) > 120):
            stale_ids.append(item_id)
            continue
        
        result.append({
            "id": item_id or uuid.uuid4().hex[:12],
            "title": str(item.get("title") or item.get("task") or "Subagente Nanobot"),
            "task": str(item.get("task") or item.get("title") or ""),
            "status": agent_status,
            "notified": notified,
            "progress": int(item.get("progress") or 0),
            "createdAt": created_at,
            "source": "nanobot-spawn",
        })
    
    # Remover stale do arquivo
    if stale_ids:
        try:
            items_kept = [i for i in items if not isinstance(i, dict) or str(i.get("id")) not in stale_ids]
            store.write_text(json.dumps({"items": items_kept}, ensure_ascii=False, indent=2), encoding="utf-8")
            log_event("nanobot_subagents_purged", count=len(stale_ids), ids=stale_ids)
        except Exception as error:
            log_event("nanobot_subagents_purge_failed", error=str(error))
    
    return result


def purge_old_finished_subagents(ctx: native_tools.ToolContext) -> int:
    """Remove subagentes finished e notificados com mais de 60s de idade.
    Isso impede que eles reaparecam como novos eventos em reinicializacoes."""
    now = int(time.time())
    purged = 0
    try:
        status = native_tools.longtask_status(ctx)
        items = [item for item in status.get("items", []) if isinstance(item, dict)]
        to_clear: list[str] = []
        for item in items:
            task_id = str(item.get("id") or "")
            if not task_id:
                continue
            agent_status = str(item.get("status") or "")
            if agent_status not in {"concluido", "erro", "cancelado"}:
                continue
            try:
                created_at = int(item.get("createdAt") or item.get("updatedAt") or 0)
            except (TypeError, ValueError):
                created_at = 0
            notified = bool(item.get("notified"))
            # Se ja notificado ou muito antigo: pode limpar
            if notified and (now - created_at > 60):
                to_clear.append(task_id)
            elif not notified and created_at < BACKEND_STARTED_AT and (now - created_at > 120):
                to_clear.append(task_id)
        for tid in to_clear:
            try:
                native_tools.longtask_clear(ctx, tid)
                purged += 1
            except Exception as error:
                log_event("stale_subagent_clear_failed", id=tid, error=str(error))
        if purged:
            log_event("purged_old_subagents", count=purged)
    except Exception as e:
        log_event("purge_old_subagents_failed", error=str(e))
    return purged


def mark_stale_finished_subagents_notified(ctx: native_tools.ToolContext, items: list[dict[str, Any]]) -> int:
    marked = 0
    now = int(time.time())
    for item in items:
        task_id = str(item.get("id") or "")
        status = str(item.get("status") or "")
        try:
            created_at = int(item.get("createdAt") or item.get("updatedAt") or 0)
        except (TypeError, ValueError):
            created_at = 0
        if not task_id or item.get("notified"):
            continue
        if status in {"concluido", "erro", "cancelado"}:
            if created_at < BACKEND_STARTED_AT:
                try:
                    native_tools.longtask_mark_notified(ctx, task_id)
                    item["notified"] = True
                    item["notifiedAt"] = now
                    marked += 1
                except Exception as error:
                    log_event("stale_subagent_mark_notified_failed", id=task_id, error=str(error))
    return marked


def subagents_status() -> dict[str, Any]:
    ctx = tool_context()
    # Passo 1: limpar subagentes old/finished antes de tudo
    purge_old_finished_subagents(ctx)
    # Passo 2: carregar estado atual
    status = native_tools.longtask_status(ctx)
    items = [item for item in status.get("items", []) if isinstance(item, dict)]
    # Passo 3: marcar como notificados subagentes finished que sao anteriores a esta sessao
    if mark_stale_finished_subagents_notified(ctx, items):
        status = native_tools.longtask_status(ctx)
        items = [item for item in status.get("items", []) if isinstance(item, dict)]
    # Passo 4: mesclar com subagentes do Nanobot
    seen = {str(item.get("id")) for item in items}
    for item in nanobot_subagent_items():
        if item["id"] not in seen:
            items.append(item)
    status["items"] = items
    return status


def update_subagents(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "status")
    if action == "start":
        return native_tools.longtask_start(tool_context(), payload)
    if action == "cancel":
        return native_tools.longtask_cancel(tool_context(), str(payload.get("id") or ""))
    if action == "mark_notified":
        return native_tools.longtask_mark_notified(tool_context(), str(payload.get("id") or ""))
    if action == "clear_finished":
        return native_tools.longtask_clear_finished(tool_context())
    return native_tools.longtask_status(tool_context(), str(payload.get("id") or "") or None)


def tools_status() -> dict[str, Any]:
    payload = nanobot_original_registry()
    if payload.get("tools"):
        return payload
    fallback = native_tools.registry()
    fallback["nanobotOriginal"] = payload.get("status", {})
    return fallback


def channels_status() -> dict[str, Any]:
    # Schema de configuracao de cada canal com campos especificos
    channel_schemas: dict[str, dict[str, Any]] = {
        "telegram": {"label": "Telegram", "fields": ["Bot Token", "Allow From (user IDs)", "Group Policy (open/mention)"], "hints": ["Token do BotFather", "Deixe vazio para todos", "open = responde todos, mention = so @"]},
        "discord": {"label": "Discord", "fields": ["Bot Token", "Channel IDs (opcional)", "Group Policy (open/mention)"], "hints": ["Token do Discord Developer Portal", "IDs separados por virgula", "open = responde todos, mention = so @"]},
        "whatsapp": {"label": "WhatsApp", "fields": ["Bridge URL", "Bridge Token"], "hints": ["ws://localhost:3001", "Token do bridge Node.js"]},
        "email": {"label": "Email", "fields": ["SMTP Server", "SMTP Port", "Email Address", "Password"], "hints": ["smtp.gmail.com", "587", "seu@email.com", "Senha do app"]},
        "msteams": {"label": "Microsoft Teams", "fields": ["App ID", "App Password", "Tenant ID"], "hints": ["ID do app no Azure", "Client secret", "ID do tenant"]},
        "matrix": {"label": "Matrix", "fields": ["Homeserver URL", "Access Token", "Room ID"], "hints": ["https://matrix.org", "Token de acesso", "!room:server.org"]},
        "signal": {"label": "Signal", "fields": ["Phone Number", "Signal URL"], "hints": ["+5511999999999", "http://localhost:8080"]},
        "slack": {"label": "Slack", "fields": ["Bot Token", "Signing Secret", "Channel ID"], "hints": ["xoxb-...", "Signing secret do app Slack", "C... ID do canal"]},
        "dingtalk": {"label": "DingTalk", "fields": ["App Key", "App Secret", "Agent ID"], "hints": ["App Key do DingTalk", "App Secret", "Agent ID do bot"]},
        "feishu": {"label": "Feishu", "fields": ["App ID", "App Secret", "Webhook URL"], "hints": ["App ID do Feishu", "App Secret", "URL do webhook"]},
        "wecom": {"label": "WeCom", "fields": ["Corp ID", "Agent ID", "Secret"], "hints": ["ID da empresa", "ID do agente", "Secret do agente"]},
    }
    
    # Tenta carregar canais do Nanobot original, mas sempre sobrescreve fields/hints
    payload_chan = nanobot_integration.channels_list()
    bridge_channels = payload_chan
    
    if bridge_channels:
        items = []
        for ch in bridge_channels:
            cid = str(ch.get("id", "")).lower()
            schema = channel_schemas.get(cid, {})
            items.append({
                "id": cid,
                "label": str(ch.get("label", schema.get("label", cid.title()))),
                "fields": schema.get("fields", []),
                "hints": schema.get("hints", []),
                "enabled": bool(ch.get("enabled", False)),
                "configured": bool(ch.get("configured", False)),
                "status": str(ch.get("status", "original-module")),
            })
        return {"channels": items, "items": items, "source": "nanobot-original"}

    items = []
    for name in sorted(channel_schemas.keys()):
        schema = channel_schemas[name]
        items.append({
            "id": name,
            "label": schema["label"],
            "fields": schema["fields"],
            "hints": schema.get("hints", []),
            "enabled": False,
            "configured": False,
            "status": "desconectado"
        })
    return {"channels": items, "items": items}


def list_skills() -> dict[str, Any]:
    skill_dir = ROOT / "data" / "skills"
    items = []
    if skill_dir.exists():
        for path in skill_dir.glob("*"):
            if not path.is_dir():
                continue
            # Ler SKILL.md para extrair descricao
            skill_md = path / "SKILL.md"
            description = ""
            if skill_md.exists():
                content = safe_read_text(skill_md)[:500]
                # Pega primeira linha nao vazia como descricao
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        description = stripped[:200]
                        break
            items.append({
                "id": path.name,
                "name": path.name,
                "path": str(path),
                "description": description,
                "status": "carregada" if skill_md.exists() else "erro",
            })
    return {"skills": items, "items": items}


def open_folder(path: Path) -> dict[str, Any]:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    return {"ok": True, "path": str(path)}


def create_file_from_message(message: str) -> dict[str, Any] | None:
    match = re.search(r"(?:arquivo|file)\s+(?:chamado\s+)?([A-Za-z0-9_.-]+\.(?:txt|md|json|csv|html))", message, re.I)
    if not match or not re.search(r"\b(crie|cria|criar|gere|gerar|salve|salvar)\b", message, re.I):
        return None
    name = match.group(1)
    content_match = re.search(r"(?:com|contendo)\s+(?:o texto\s+)?(.+)$", message, re.I)
    content = content_match.group(1).strip() if content_match else "Arquivo criado pelo BMO."
    target_dir = DESKTOP_DIR if DESKTOP_DIR.exists() and re.search(r"\b(area de trabalho|desktop)\b", folded(message)) else REPORTS_DIR
    path = target_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "name": path.name, "size": path.stat().st_size, "reply": f"Prontinho. Eu criei o arquivo: {path.name}"}


TICTACTOE_TKINTER_CODE = """import tkinter as tk
from tkinter import messagebox


class TicTacToe:
    def __init__(self, root):
        self.root = root
        self.root.title("Jogo da Velha")
        self.current_player = "X"
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.buttons = []
        self.status = tk.Label(root, text="Vez do jogador X", font=("Segoe UI", 12))
        self.status.grid(row=0, column=0, columnspan=3, pady=(8, 4))
        for row in range(3):
            button_row = []
            for col in range(3):
                button = tk.Button(
                    root,
                    text="",
                    font=("Segoe UI", 28, "bold"),
                    width=4,
                    height=2,
                    command=lambda r=row, c=col: self.play(r, c),
                )
                button.grid(row=row + 1, column=col, padx=3, pady=3)
                button_row.append(button)
            self.buttons.append(button_row)
        tk.Button(root, text="Reiniciar", command=self.reset).grid(row=4, column=0, columnspan=3, sticky="ew", padx=3, pady=8)

    def play(self, row, col):
        if self.board[row][col] or self.winner():
            return
        self.board[row][col] = self.current_player
        self.buttons[row][col].config(text=self.current_player)
        winner = self.winner()
        if winner:
            self.status.config(text=f"Jogador {winner} venceu!")
            messagebox.showinfo("Fim de jogo", f"Jogador {winner} venceu!")
            return
        if all(self.board[r][c] for r in range(3) for c in range(3)):
            self.status.config(text="Empate!")
            messagebox.showinfo("Fim de jogo", "Empate!")
            return
        self.current_player = "O" if self.current_player == "X" else "X"
        self.status.config(text=f"Vez do jogador {self.current_player}")

    def winner(self):
        lines = []
        lines.extend(self.board)
        lines.extend([[self.board[row][col] for row in range(3)] for col in range(3)])
        lines.append([self.board[i][i] for i in range(3)])
        lines.append([self.board[i][2 - i] for i in range(3)])
        for line in lines:
            if line[0] and line[0] == line[1] == line[2]:
                return line[0]
        return ""

    def reset(self):
        self.current_player = "X"
        for row in range(3):
            for col in range(3):
                self.board[row][col] = ""
                self.buttons[row][col].config(text="")
        self.status.config(text="Vez do jogador X")


if __name__ == "__main__":
    window = tk.Tk()
    TicTacToe(window)
    window.mainloop()
"""


def launch_python_file(path: Path) -> dict[str, Any]:
    python_cmd = shutil.which("pythonw") or shutil.which("pythonw.exe") or shutil.which("python") or sys.executable
    startupinfo, creationflags = windows_process_options()
    proc = subprocess.Popen(
        [python_cmd, str(path)],
        cwd=str(path.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    return {"ok": True, "path": str(path), "pid": proc.pid, "command": [python_cmd, str(path)]}


def create_python_game_from_message(message: str) -> dict[str, Any] | None:
    clean = folded(message)
    if not re.search(r"\b(crie|cria|criar|gere|gerar)\b", clean):
        return None
    if "jogo da velha" not in clean or "python" not in clean:
        return None
    path = DESKTOP_DIR / "jogo_da_velha.py" if DESKTOP_DIR.exists() else RUNTIME_WORKSPACE / "jogo_da_velha.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TICTACTOE_TKINTER_CODE, encoding="utf-8")
    launched = launch_python_file(path)
    log_event("local_python_game_created", path=str(path), pid=launched.get("pid"))
    return {
        "path": str(path),
        "name": path.name,
        "pid": launched.get("pid"),
        "reply": f"Prontinho. Criei {path.name} e abri o jogo para voce.",
    }


def create_subagent_from_message(message: str) -> dict[str, Any] | None:
    clean = folded(message)
    if "subagente" not in clean or not re.search(r"\b(crie|cria|criar|gere|gerar)\b", clean):
        return None
    objective_match = re.search(r"\bpara\s+(.+)$", message, re.I)
    objective = objective_match.group(1).strip() if objective_match else message.strip()
    title = "Subagente de Pesquisa sobre IA" if re.search(r"\bia\b", clean) else f"Subagente: {objective[:48]}"
    result = create_subagent_tool({"title": title, "objective": objective})
    task = result.get("task") if isinstance(result, dict) else {}
    log_event("local_subagent_created", title=title, id=(task or {}).get("id"))
    subagent = dict(result) if isinstance(result, dict) else {"ok": False, "result": result}
    if isinstance(task, dict) and task.get("id"):
        subagent.setdefault("id", task.get("id"))
        subagent.setdefault("status", task.get("status"))
    # Pegar summary se disponivel
    summary = str(result.get("summary", "")) if isinstance(result, dict) else ""
    task_id = (task or {}).get("id", "") if isinstance(task, dict) else ""
    output_path = str(result.get("outputPath", "")) if isinstance(result, dict) else ""
    if output_path:
        reply = f"Prontinho. Criei o subagente e salvei o resultado em {output_path}."
    elif summary:
        reply = f"Prontinho. Subagente concluiu: {summary}"
    else:
        reply = "Prontinho. Criei o subagente e ele ja esta trabalhando."
    return {
        "reply": reply,
        "subagent": subagent,
    }


def create_reminder_from_message(message: str) -> dict[str, Any] | None:
    if not re.search(r"\b(lembre|lembrar|lembra)\b", folded(message)):
        return None
    time_match = re.search(r"\b(?:daqui(?:\s+a)?|em)\s+(\d+)\s*(segundos?|seg|s|minutos?|mins?|min|m|horas?|h)\b", message, re.I)
    if not time_match:
        return None
    amount = int(time_match.group(1))
    unit = folded(time_match.group(2))
    seconds = amount * 3600 if unit.startswith("h") else amount if unit.startswith(("s", "seg")) else amount * 60
    text = re.sub(r"\b(?:daqui(?:\s+a)?|em)\s+\d+\s*(?:segundos?|seg|s|minutos?|mins?|min|m|horas?|h)\b", "", message, count=1, flags=re.I)
    text = re.sub(r"(?i)\b(?:me\s+)?(?:lembre|lembra|lembrar)(?:-me)?\s+(?:de\s+)?", "", text, count=1).strip()
    text = re.sub(r"(?i)\bpor\s+favor\b", "", text).strip(" .,!?:;-")
    if not text:
        text = "Lembrete"
    due_at = int(time.time()) + max(1, seconds)
    data = update_reminder({"action": "create", "text": text, "dueAt": due_at})
    log_event("reminder_created_from_chat", text=text, dueAt=due_at)
    when = datetime.fromtimestamp(due_at, SAO_PAULO_TZ).strftime("%H:%M")
    return {"reply": f"Combinado. Eu vou te lembrar: {text}.", "reminder": data["items"][-1] if data.get("items") else None, "scheduledFor": when}


def openapi_spec() -> dict[str, Any]:
    paths = {}
    for route in ALL_ROUTES:
        methods = ["get"] if route in GET_ROUTES else ["post"]
        paths[route] = {methods[0]: {"summary": f"BMO {route}", "responses": {"200": {"description": "OK"}}}}
    return {"openapi": "3.0.0", "info": {"title": "BMO Nanobot API", "version": "1.0.0"}, "paths": paths}


GET_ROUTES = {
    "/api/health", "/api/config", "/api/settings", "/api/voices", "/api/system", "/api/reminders",
    "/api/subagents", "/api/tasks", "/api/microphones", "/api/memory", "/api/history", "/api/logs",
    "/api/tools", "/api/skills", "/api/channels", "/api/file/list", "/api/cron/list",
    "/api/tools/list", "/api/nanobot/tools", "/openapi.json", "/docs",
}
POST_ROUTES = {
    "/api/chat", "/api/speak", "/api/sound", "/api/listen", "/api/whisper/test", "/api/voice-chat",
    "/api/settings", "/api/provider/test", "/api/memory", "/api/history", "/api/history/export", "/api/reminders",
    "/api/subagents", "/api/tasks", "/api/tools", "/api/skills", "/api/channels", "/api/open-folder",
    "/api/service/restart", "/api/run-python", "/api/file/list", "/api/file/read", "/api/file/write",
    "/api/file/delete", "/api/file/move", "/api/file/metadata", "/api/shell/exec", "/api/web/search",
    "/api/cron/create", "/api/cron/delete", "/api/cron/run", "/api/longtask/start",
    "/api/longtask/status", "/api/longtask/cancel", "/api/memory/vector/upsert",
    "/api/memory/vector/search", "/api/memory/vector/summary", "/api/channel/telegram",
    "/api/channel/discord", "/api/channel/slack", "/api/channel/whatsapp", "/api/channel/email",
    "/api/channel/msteams", "/api/channel/wecom", "/api/channel/feishu", "/api/tools/info",
    "/api/nanobot/tool",
}
ALL_ROUTES = sorted(GET_ROUTES | POST_ROUTES)


class BmoHandler(BaseHTTPRequestHandler):
    server_version = "BMONanobotBackend/1.0"

    def end_headers(self) -> None:
        # Permitir apenas Origin local (Electron, localhost)
        origin = self.headers.get("Origin") or ""
        allowed_origins = ["", "http://localhost", "http://127.0.0.1", "file://", "app://"]
        if any(origin.startswith(ao) for ao in allowed_origins):
            self.send_header("Access-Control-Allow-Origin", origin or "*")
        else:
            self.send_header("Access-Control-Allow-Origin", "http://localhost")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-BMO-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def parsed_path(self) -> tuple[str, dict[str, list[str]]]:
        parsed = urllib.parse.urlparse(self.path)
        return parsed.path, urllib.parse.parse_qs(parsed.query)

    def rate_limited(self, path: str) -> bool:
        allowed, retry_after = check_rate_limit(self.client_address[0], path)
        if allowed:
            return False
        self.send_json({"error": "Too Many Requests"}, status=429, headers={"Retry-After": str(retry_after)})
        return True

    def do_GET(self) -> None:
        path, query = self.parsed_path()
        # Rotas publicas (health e docs) nao precisam de token
        if path not in {"/api/health"}:
            if not require_bmo_token(self.headers):
                self.send_json({"error": "Unauthorized - X-BMO-Token header required"}, status=401)
                return
        if self.rate_limited(path):
            return
        started = time.perf_counter()
        try:
            if path == "/api/health":
                self.send_json({"ok": True, "status": "ok"})
            elif path == "/api/config":
                self.send_json(load_app_config())
            elif path == "/api/settings":
                self.send_json(current_settings())
            elif path == "/api/voices":
                self.send_json({"voices": list_voice_models(), "selected": load_app_config().get("voice", {}).get("model")})
            elif path == "/api/system":
                if _chat_busy.is_set():
                    self.send_json({"busy": True})
                else:
                    self.send_json(system_status())
            elif path == "/api/reminders":
                self.send_json(reminders_status(due_only=(query.get("due") or ["0"])[0] == "1"))
            elif path == "/api/subagents":
                if _chat_busy.is_set():
                    self.send_json({"busy": True})
                else:
                    self.send_json(subagents_status())
            elif path == "/api/tasks":
                self.send_json(tasks_status())
            elif path == "/api/microphones":
                self.send_json({"devices": microphone_devices()})
            elif path == "/api/memory":
                self.send_json({"items": read_memories(), "nanobot": nanobot_original_memory()})
            elif path == "/api/history":
                self.send_json({"sessions": read_history()})
            elif path == "/api/logs":
                log_path = LOG_DIR / "bmo.log"
                lines = safe_read_text(log_path).splitlines()[-200:] if log_path.exists() else []
                self.send_json({"logFile": str(log_path), "lines": lines})
            elif path in {"/api/tools", "/api/tools/list"}:
                self.send_json(tools_status())
            elif path == "/api/tools/detail":
                detail = tools_status()
                tools_list = detail.get("tools", [])
                enriched = []
                for t in tools_list:
                    t["status"] = "Online"
                    # Categorizar por dominio
                    name_lower = str(t.get("id", "")).lower()
                    if any(x in name_lower for x in ["web", "search", "fetch"]):
                        t["category"] = "Web"
                    elif any(x in name_lower for x in ["file", "read", "write", "edit", "patch", "find", "grep", "list", "dir"]):
                        t["category"] = "Arquivos"
                    elif any(x in name_lower for x in ["exec", "shell", "cli", "run"]):
                        t["category"] = "Execucao"
                    elif any(x in name_lower for x in ["cron", "long", "task"]):
                        t["category"] = "Tarefas"
                    elif any(x in name_lower for x in ["message", "spawn", "my"]):
                        t["category"] = "Agente"
                    elif any(x in name_lower for x in ["complete", "goal"]):
                        t["category"] = "Meta"
                    else:
                        t["category"] = "Geral"
                    enriched.append(t)
                self.send_json({"tools": enriched, "count": len(enriched)})
            elif path.startswith("/api/tools/info/"):
                self.send_json(nanobot_original_info(path.rsplit("/", 1)[-1]))
            elif path == "/api/nanobot/tools":
                self.send_json(nanobot_original_registry())
            elif path == "/api/skills":
                self.send_json(list_skills())
            elif path == "/api/channels":
                self.send_json(channels_status())
            elif path == "/api/workspace":
                ws = RUNTIME_WORKSPACE
                items = []
                if ws.exists():
                    for entry in sorted(ws.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                        if entry.name.startswith("."):
                            continue
                        info = {
                            "name": entry.name,
                            "path": str(entry),
                            "is_dir": entry.is_dir(),
                            "size": entry.stat().st_size if entry.is_file() else 0,
                            "modified": entry.stat().st_mtime,
                        }
                        name_lower = entry.name.lower()
                        if entry.is_dir():
                            info["category"] = "pasta"
                        elif any(x in name_lower for x in ["resultado", "pesquisa", "pesq", "search", "report"]):
                            info["category"] = "pesquisa"
                        elif any(x in name_lower for x in ["download", "baixado"]):
                            info["category"] = "download"
                        elif any(x in name_lower for x in ["subagent", "subagente", "agent"]):
                            info["category"] = "subagente"
                        elif any(x in name_lower for x in ["relatorio", "report"]):
                            info["category"] = "relatorio"
                        elif any(x in name_lower for x in [".txt", ".md", ".json", ".csv", ".log"]):
                            info["category"] = "documento"
                        else:
                            info["category"] = "arquivo"
                        items.append(info)
                self.send_json({"items": items, "path": str(ws)})
            elif path == "/api/file/list":
                original = nanobot_original_tool("list_dir", {
                    "path": (query.get("path") or ["."])[0] or ".",
                    "recursive": (query.get("recursive") or ["0"])[0] == "1",
                })
                compatible = native_tools.list_dir(tool_context(), (query.get("path") or [""])[0], (query.get("recursive") or ["0"])[0] == "1")
                compatible["original"] = original
                self.send_json(compatible)
            elif path == "/api/cron/list":
                self.send_json(nanobot_original_tool("cron", {"action": "list"}))
            elif path == "/openapi.json":
                self.send_json(openapi_spec())
            elif path == "/docs":
                self.send_html("<!doctype html><title>BMO API</title><h1>BMO API</h1><p>OpenAPI: <a href='/openapi.json'>/openapi.json</a></p>")
            else:
                self.send_json({"error": "not found"}, status=404)
        except Exception as error:
            log_event("get_error", path=path, error=str(error), trace=traceback.format_exc()[-2000:])
            self.send_json({"error": str(error)}, status=500)
        finally:
            log_event("request", ip=self.client_address[0], method="GET", path=path, ms=int((time.perf_counter() - started) * 1000))

    def read_payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(body or "{}")

    def do_POST(self) -> None:
        path, _query = self.parsed_path()
        if not require_bmo_token(self.headers):
            self.send_json({"error": "Unauthorized - X-BMO-Token header required"}, status=401)
            return
        if self.rate_limited(path):
            return
        started = time.perf_counter()
        try:
            payload = self.read_payload()
            ctx = tool_context()
            if path == "/api/settings":
                self.send_json(update_settings(payload))
            elif path == "/api/provider/test":
                self.send_json(provider_test_result(payload))
            elif path == "/api/sound":
                self.send_json(play_ui_sound(str(payload.get("type") or "ack"), str(payload.get("language") or "pt-BR")))
            elif path == "/api/open-folder":
                target = str(payload.get("target") or "")
                folders = {"memory": MEMORY_DIR, "voices": PIPER_ROOT, "config": CONFIG_DIR, "appData": APP_DATA_DIR}
                self.send_json(open_folder(folders.get(target, APP_DATA_DIR)))
            elif path == "/api/memory":
                self.handle_memory(payload)
            elif path == "/api/history/export":
                self.send_json(history_export_payload(payload))
            elif path == "/api/history":
                self.handle_history(payload)
            elif path == "/api/reminders":
                self.send_json(update_reminder(payload))
            elif path == "/api/subagents":
                self.send_json(update_subagents(payload))
            elif path == "/api/tasks":
                self.send_json(update_tasks(payload))
            elif path == "/api/service/restart":
                self.restart_service()
            elif path == "/api/speak":
                self.send_json(speak_text(str(payload.get("text") or ""), str(payload.get("voice") or "")))
            elif path == "/api/listen":
                seconds = float(payload.get("seconds") or 5)
                try:
                    transcript = listen_once(seconds=max(1, min(seconds, 12)))
                    self.send_json({"ok": True, "transcript": transcript})
                except Exception as error:
                    log_event("listen_failed", error=str(error))
                    self.send_json({"ok": False, "transcript": "", "error": str(error)})
            elif path == "/api/whisper/test":
                self.send_json(test_whisper_runtime())
            elif path == "/api/voice-chat":
                _chat_busy.set()
                try:
                    seconds = float(payload.get("seconds") or 5)
                    session_id = str(payload.get("sessionId") or "") or None
                    language = str(payload.get("language") or "pt-BR")
                    try:
                        transcript = listen_once(seconds=max(1, min(seconds, 12)))
                    except Exception as error:
                        log_event("voice_chat_listen_failed", error=str(error))
                        self.send_json({"ok": False, "transcript": "", "reply": "", "error": str(error), "sessionId": session_id})
                        return
                    reminder = create_reminder_from_message(transcript)
                    reply = str(reminder["reply"]) if reminder else ask_nanobot(transcript, language, session_id)
                    session = save_chat_turn(session_id, transcript, reply)
                    if payload.get("speak", True):
                        speak_text(reply, str(payload.get("voice") or ""))
                    self.send_json({"ok": True, "transcript": transcript, "reply": reply, "sessionId": session.get("id")})
                finally:
                    _chat_busy.clear()
            elif path == "/api/chat":
                self.handle_chat(payload)
            elif path == "/api/run-python":
                filename = str(payload.get("filename") or "script.py")
                if not filename.lower().endswith(".py"):
                    self.send_json({"ok": False, "error": "filename precisa terminar com .py"}, status=400)
                    return
                if payload.get("code") is not None:
                    native_tools.write_file(ctx, filename, str(payload.get("code") or ""), overwrite=True)
                script_path = native_tools.resolve_workspace_path(ctx, filename, must_exist=True)
                self.send_json(native_tools.shell_exec(ctx, [sys.executable, str(script_path)], timeout=30))
            elif path == "/api/file/list":
                original = nanobot_original_tool("list_dir", {
                    "path": str(payload.get("path") or "."),
                    "recursive": bool(payload.get("recursive")),
                    "max_entries": int(payload.get("limit") or 500),
                })
                compatible = native_tools.list_dir(ctx, str(payload.get("path") or ""), bool(payload.get("recursive")), int(payload.get("limit") or 500))
                compatible["original"] = original
                self.send_json(compatible)
            elif path == "/api/file/read":
                original = nanobot_original_tool("read_file", {
                    "path": str(payload.get("path") or ""),
                    "offset": int(payload.get("offset") or 1),
                    "limit": int(payload.get("limit") or 2000),
                    "force": bool(payload.get("force")),
                })
                self.send_json({
                    "ok": original.get("ok", False),
                    "path": str(payload.get("path") or ""),
                    "content": original.get("result"),
                    "original": original,
                })
            elif path == "/api/file/write":
                if payload.get("append"):
                    result = native_tools.write_file(ctx, str(payload.get("path") or ""), str(payload.get("content") or ""), True, bool(payload.get("overwrite", True)))
                    result["source"] = "bmo-compat-append"
                    self.send_json(result)
                else:
                    original = nanobot_original_tool("write_file", {
                        "path": str(payload.get("path") or ""),
                        "content": str(payload.get("content") or ""),
                    })
                    self.send_json({
                        "ok": original.get("ok", False),
                        "path": str(payload.get("path") or ""),
                        "result": original.get("result"),
                        "original": original,
                    })
            elif path == "/api/file/delete":
                self.send_json(native_tools.delete_path(ctx, str(payload.get("path") or ""), bool(payload.get("recursive"))))
            elif path == "/api/file/move":
                self.send_json(native_tools.move_path(ctx, str(payload.get("src") or ""), str(payload.get("dst") or ""), bool(payload.get("overwrite"))))
            elif path == "/api/file/metadata":
                self.send_json(native_tools.metadata(ctx, str(payload.get("path") or "")))
            elif path == "/api/shell/exec":
                exec_params: dict[str, Any] = {
                    "command": str(payload.get("command") or ""),
                    "timeout": int(payload.get("timeout") or 30),
                }
                if payload.get("cwd"):
                    exec_params["working_dir"] = str(payload.get("cwd"))
                original = nanobot_original_tool("exec", exec_params)
                self.send_json({
                    "ok": original.get("ok", False),
                    "stdout": str(original.get("result") or ""),
                    "stderr": "",
                    "returncode": 0 if original.get("ok") else 1,
                    "original": original,
                })
            elif path == "/api/web/search":
                original = nanobot_original_tool("web_search", {
                    "query": str(payload.get("query") or ""),
                    "count": int(payload.get("limit") or 5),
                })
                self.send_json({"ok": original.get("ok", False), "resultsText": original.get("result"), "original": original})
            elif path == "/api/cron/create":
                cron_params: dict[str, Any] = {
                    "action": "add",
                    "name": str(payload.get("name") or payload.get("title") or "bmo-job"),
                    "message": str(payload.get("message") or payload.get("command") or payload.get("text") or ""),
                    "deliver": bool(payload.get("deliver", True)),
                }
                every_seconds = int(payload.get("every_seconds") or payload.get("everySeconds") or 0)
                cron_expr = str(payload.get("cron_expr") or payload.get("cronExpr") or "")
                at = str(payload.get("at") or "")
                if every_seconds:
                    cron_params["every_seconds"] = every_seconds
                if cron_expr:
                    cron_params["cron_expr"] = cron_expr
                if at:
                    cron_params["at"] = at
                original = nanobot_original_tool("cron", cron_params)
                self.send_json(original)
            elif path == "/api/cron/delete":
                self.send_json(nanobot_original_tool("cron", {"action": "remove", "job_id": str(payload.get("id") or payload.get("job_id") or "")}))
            elif path == "/api/cron/run":
                self.send_json(native_tools.cron_run(ctx, str(payload.get("id") or "")))
            elif path == "/api/longtask/start":
                self.send_json(native_tools.longtask_start(ctx, payload))
            elif path == "/api/longtask/status":
                self.send_json(native_tools.longtask_status(ctx, str(payload.get("id") or "") or None))
            elif path == "/api/longtask/cancel":
                self.send_json(native_tools.longtask_cancel(ctx, str(payload.get("id") or "")))
            elif path == "/api/memory/vector/upsert":
                self.send_json(native_tools.vector_upsert(ctx, [str(item) for item in payload.get("chunks") or []], payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None))
            elif path == "/api/memory/vector/search":
                self.send_json(native_tools.vector_search(ctx, str(payload.get("query") or ""), int(payload.get("top_k") or payload.get("topK") or 5)))
            elif path == "/api/memory/vector/summary":
                self.send_json(native_tools.vector_summary(ctx, int(payload.get("limit") or 12)))
            elif path.startswith("/api/channel/"):
                self.send_json(native_tools.send_channel(ctx, path.rsplit("/", 1)[-1], payload))
            elif path == "/api/tools/info":
                self.send_json(nanobot_original_info(str(payload.get("name") or "")))
            elif path in {"/api/tools", "/api/tools/list"}:
                self.send_json(tools_status())
            elif path == "/api/nanobot/tool":
                self.send_json(nanobot_original_tool(str(payload.get("name") or ""), payload.get("params") if isinstance(payload.get("params"), dict) else {}))
            elif path == "/api/channels":
                self.send_json(channels_status())
            elif path == "/api/skills":
                self.send_json(list_skills())
            else:
                self.send_json({"error": "not found"}, status=404)
        except urllib.error.HTTPError as error:
            message = friendly_http_error(error)
            log_event("post_http_error", path=path, error=message)
            self.send_json({"error": message}, status=502)
        except Exception as error:
            log_event("post_error", path=path, error=str(error), trace=traceback.format_exc()[-4000:])
            self.send_json({"error": str(error), "trace": traceback.format_exc()[-2000:]}, status=500)
        finally:
            log_event("request", ip=self.client_address[0], method="POST", path=path, ms=int((time.perf_counter() - started) * 1000))

    def handle_memory(self, payload: dict[str, Any]) -> None:
        with memory_lock:
            action = str(payload.get("action") or "add")
            items = read_items(MEMORY_FILE)
            if action == "delete":
                item_id = str(payload.get("id") or "")
                # Se for item do Nanobot, limpar o arquivo real
                if item_id == "nanobot-soul" and WORKSPACE_SOUL_MD and WORKSPACE_SOUL_MD.exists():
                    WORKSPACE_SOUL_MD.write_text("# (esquecido pelo usuario)\n", encoding="utf-8")
                elif item_id == "nanobot-user" and WORKSPACE_USER_MD and WORKSPACE_USER_MD.exists():
                    WORKSPACE_USER_MD.write_text("# (esquecido pelo usuario)\n", encoding="utf-8")
                else:
                    items = [item for item in items if item.get("id") != item_id]
            elif action == "clear":
                items = []
            elif action == "export":
                export_path = DESKTOP_DIR / f"backup_memoria_bmo_{time.strftime('%Y%m%d_%H%M%S')}.json"
                write_json(export_path, {"items": items, "memoryMd": safe_read_text(MEMORY_MD) if MEMORY_MD.exists() else ""})
                self.send_json({"items": items, "path": str(export_path)})
                return
            elif action == "import":
                imported = payload.get("items")
                items = [item for item in imported if isinstance(item, dict)] if isinstance(imported, list) else items
                if payload.get("memoryMd"):
                    MEMORY_MD.write_text(str(payload["memoryMd"]), encoding="utf-8")
            else:
                text = str(payload.get("text") or "").strip()
                if not text:
                    self.send_json({"error": "Memoria vazia."}, status=400)
                    return
                items.append({"id": str(int(time.time() * 1000)), "text": text, "createdAt": int(time.time())})
                try:
                    nanobot_original_append_history(f"USER MEMORY: {text}")
                except Exception as error:
                    log_event("nanobot_memory_append_failed", error=str(error))
            write_items(MEMORY_FILE, items)
        self.send_json({"items": items, "nanobot": nanobot_original_memory()})

    def handle_history(self, payload: dict[str, Any]) -> None:
        with history_lock:
            action = str(payload.get("action") or "list")
            sessions = read_history()
            if action == "delete":
                sessions = [session for session in sessions if session.get("id") != payload.get("id")]
                write_history(sessions)
            elif action == "clear":
                sessions = []
                write_history(sessions)
        self.send_json({"sessions": sessions})

    def handle_chat(self, payload: dict[str, Any]) -> None:
        _chat_busy.set()
        _chat_started = time.perf_counter()
        try:
            session_id = str(payload.get("sessionId") or "") or None
            message = str(payload.get("message") or "").strip()
            language = str(payload.get("language") or "pt-BR")
            attachments = process_chat_attachments(payload.get("attachments"))
            if not message and attachments:
                message = "Analise os anexos enviados."
            if not message:
                self.send_json({"error": "Mensagem vazia."}, status=400)
                return
            model_message = message
            context = attachment_context(attachments)
            if context:
                model_message = f"{message}\n\n{context}"
            profile_update = remember_profile_from_message(message)
            if profile_update:
                reply = str(profile_update["reply"])
                session = save_chat_turn(session_id, message, reply, {"attachments": attachments} if attachments else None)
                self.send_json({"reply": reply, "sessionId": session.get("id"), "memory": profile_update, "attachments": attachments})
                return
            reminder = create_reminder_from_message(message)
            if reminder:
                reply = str(reminder["reply"])
                session = save_chat_turn(session_id, message, reply, {"attachments": attachments} if attachments else None)
                self.send_json({"reply": reply, "sessionId": session.get("id"), "reminder": reminder.get("reminder"), "attachments": attachments})
                return
            created = create_file_from_message(message)
            if created:
                metadata = {"lastFilePath": created["path"], "lastFileName": created["name"]}
                if attachments:
                    metadata["attachments"] = attachments
                session = save_chat_turn(session_id, message, created["reply"], metadata)
                self.send_json({"reply": created["reply"], "sessionId": session.get("id"), "file": created, "attachments": attachments})
                return
            game = create_python_game_from_message(message)
            if game:
                metadata = {"lastFilePath": game["path"], "lastFileName": game["name"]}
                if attachments:
                    metadata["attachments"] = attachments
                session = save_chat_turn(session_id, message, game["reply"], metadata)
                self.send_json({"reply": game["reply"], "sessionId": session.get("id"), "file": game, "attachments": attachments})
                return
            subagent = create_subagent_from_message(message)
            if subagent:
                session = save_chat_turn(session_id, message, subagent["reply"], {"attachments": attachments} if attachments else None)
                self.send_json({"reply": subagent["reply"], "sessionId": session.get("id"), "subagent": subagent.get("subagent"), "attachments": attachments})
                return
            t_llm_start = time.perf_counter()
            reply = ask_nanobot(model_message, language, session_id)
            t_llm_ms = round((time.perf_counter() - t_llm_start) * 1000)
            session = save_chat_turn(session_id, message, reply, {"attachments": attachments} if attachments else None)
            total_ms = round((time.perf_counter() - _chat_started) * 1000)
            log_event("chat_completed", session=session_id, total_ms=total_ms, llm_ms=t_llm_ms, reply_len=len(reply))
            self.send_json({"reply": reply, "sessionId": session.get("id"), "attachments": attachments})
        finally:
            _chat_busy.clear()

    def restart_service(self) -> None:
        self.send_json({"ok": True, "status": system_status()})

    def send_json(self, payload: dict[str, Any], status: int = 200, headers: dict[str, str] | None = None) -> None:
        raw = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_html(self, html: str, status: int = 200) -> None:
        raw = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: Any) -> None:
        log_event("http_log", client=self.address_string(), message=format % args)


def cron_loop() -> None:
    while True:
        try:
            native_tools.cron_tick(tool_context())
        except Exception as error:
            log_event("cron_error", error=str(error))
        time.sleep(15)


def main() -> None:
    ensure_runtime_config()
    # Printa o token de autenticacao para o Electron capturar
    # Formato: BMO_TOKEN=<hex> em linha unica no stdout
    print(f"BMO_TOKEN={_BMO_API_TOKEN}", flush=True)
    try:
        result = native_tools.longtask_mark_existing_finished_notified(tool_context())
        if result.get("marked"):
            log_event("longtasks_marked_notified_on_start", marked=result.get("marked"))
    except Exception as error:
        log_event("longtasks_startup_notify_migration_failed", error=str(error))
    threading.Thread(target=cron_loop, name="BMO Cron", daemon=True).start()
    threading.Thread(target=reminder_loop, name="BMO Reminders", daemon=True).start()
    threading.Thread(target=wakeword_loop, name="BMO Wake Word", daemon=True).start()
    # Inicializa NanobotRuntime em background (nao bloqueia a inicializacao)
    def _init_nanobot():
        try:
            ok = nanobot_integration.initialize_runtime()
            log_event("nanobot_integration_init", ok=ok, status=nanobot_integration.runtime_status())
        except Exception as e:
            log_event("nanobot_integration_init_failed", error=str(e))
    threading.Thread(target=_init_nanobot, name="NanobotInit", daemon=True).start()
    log_event("backend_start", backend=f"http://{BACKEND_HOST}:{BACKEND_PORT}", nanobot_source=str(NANOBOT_SOURCE))
    server = ThreadingHTTPServer((BACKEND_HOST, BACKEND_PORT), BmoHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
