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
import tools as native_tools
import nanobot_runtime


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

DEFAULT_FALLBACK_MODELS = ["openai/gpt-oss-20b:free", "meta-llama/llama-3.3-70b-instruct:free"]
PROVIDER_ENV_KEYS = {"openrouter": "OPENROUTER_API_KEY", "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "custom": "CUSTOM_API_KEY"}
PROVIDER_NAMES = ["openrouter", "openai", "ollama", "lm_studio", "custom", "anthropic", "gemini"]
MAX_CONTEXT_MESSAGES = 10
MAX_CONTEXT_CHARS = 6500
_chat_busy = threading.Event()
try:
    SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
except Exception as error:
    sys.stderr.write(f"BMO timezone fallback: {error}\n")
    SAO_PAULO_TZ = datetime.now().astimezone().tzinfo


def copy_if_missing(source: Path, target: Path) -> None:
    if target.exists() or not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)



def write_text_if_missing(path, text):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

def copy_if_missing(source, target):
    if target.exists() or not source.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        import shutil
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)

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
    # USER.md path check skipped
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
        return path.read_text(encoding=encoding, errors=errors)
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
    """Keep only fields accepted by Nanobot official Pydantic Config."""
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
    # nanobot_bridge.invalidate_runtime()
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
    # Status do NanobotRuntime
    rt_ready = False
    rt_error = ""
    rt_tools = []
    try:
        rt = nanobot_runtime.NanobotRuntime.get_instance()
        rt_ready = rt.is_ready
        if rt_ready:
            rt_tools = rt.tool_names
        else:
            rt_error = rt.error
    except Exception as exc:
        rt_error = str(exc)
    return {
        "backend": True,
        "nanobot": bool(original),
        "nanobotRuntimeReady": rt_ready,
        "nanobotRuntimeError": rt_error,
        "nanobotRuntimeTools": rt_tools,
        "nanobotOriginal": original,
        "piper": PIPER_EXE.exists() and bool(voices),
        "whisper": WHISPER_EXE.exists() and resolve_whisper_model_path().exists(),
        "python": sys.version.split()[0],
        "paths": current_settings()["paths"],
        "whisperConfig": whisper_status(),
        "wakeword": wakeword_status_snapshot(),
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


def read_memories() -> list[dict[str, Any]]:
    with memory_lock:
        items = read_items(MEMORY_FILE)
        if MEMORY_MD.exists():
            items.append({"id": "memory-md", "text": safe_read_text(MEMORY_MD)[-2000:], "source": "MEMORY.md"})
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
    # History append skipped (NanobotRuntime handles this)
    return selected




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
    defaults["workspace"] = str(RUNTIME_WORKSPACE).replace("\\", "/")
    write_json(RUNTIME_CONFIG, config)
    write_json(NANOBOT_RUNTIME_CONFIG, sanitize_nanobot_runtime_config(config))
    os.environ["NANOBOT_CONFIG_PATH"] = str(NANOBOT_RUNTIME_CONFIG)
    return NANOBOT_RUNTIME_CONFIG










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
    subprocess.run(command, input=speech, text=True, encoding="utf-8", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, startupinfo=startupinfo, creationflags=creationflags, timeout=90)
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

            mic = sd.query_devices(kind="input")
            set_wakeword_state(available=True, dependency=True, running=True, enabled=True, model=str(WAKEWORD_MODEL), message=f"Escutando Hey BMO em {mic.get('name', 'microfone padrao')}.", lastError="")
            log_event("wake_word_started", model=str(WAKEWORD_MODEL), microphone=mic.get("name", "default"))
            model = Model(wakeword_models=[str(WAKEWORD_MODEL)])
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
            set_wakeword_state(running=False, enabled=False, lastError=str(error), message=f"Wake word falhou: {error}")
            log_event("wake_word_error", error=str(error))
            time.sleep(5)


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




def subagents_status() -> dict[str, Any]:
    ctx = tool_context()
    status = native_tools.longtask_status(ctx)
    items = [item for item in status.get("items", []) if isinstance(item, dict)]
    if mark_stale_finished_subagents_notified(ctx, items):
        status = native_tools.longtask_status(ctx)
        items = [item for item in status.get("items", []) if isinstance(item, dict)]
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
    # Tenta pegar as tools reais do NanobotRuntime
    try:
        rt = nanobot_runtime.NanobotRuntime.get_instance()
        if rt.is_ready:
            tools = rt.definitions()
            if tools:
                return {"ok": True, "tools": tools, "source": "nanobot-runtime", "count": len(tools)}
    except Exception:
        pass
    # Fallback
    payload = nanobot_original_registry()
    if payload.get("tools"):
        return payload
    fallback = native_tools.registry()
    fallback["nanobotOriginal"] = payload.get("status", {})
    return fallback


def channels_status() -> dict[str, Any]:
    payload = nanobot_bridge.channels_payload(NANOBOT_SOURCE)
    channels = payload.get("channels") or []
    if channels:
        return {"channels": channels, "items": channels, "source": "nanobot-original"}
    items = [{"id": name, "enabled": False} for name in ["telegram", "discord", "slack", "whatsapp", "email", "msteams", "wecom", "feishu"]]
    return {"channels": items, "items": items}


def list_skills() -> dict[str, Any]:
    skill_dir = ROOT / "data" / "skills"
    items = [{"name": path.name, "path": str(path)} for path in skill_dir.glob("*") if path.is_dir()] if skill_dir.exists() else []
    return {"items": items}


def open_folder(path: Path) -> dict[str, Any]:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    return {"ok": True, "path": str(path)}










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
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
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
            elif path.startswith("/api/tools/info/"):
                self.send_json(nanobot_original_info(path.rsplit("/", 1)[-1]))
            elif path == "/api/nanobot/tools":
                self.send_json(nanobot_original_registry())
            elif path == "/api/skills":
                self.send_json(list_skills())
            elif path == "/api/channels":
                self.send_json(channels_status())
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
                items = [item for item in items if item.get("id") != payload.get("id")]
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
                # Memory history append skipped (NanobotRuntime handles this)
            write_items(MEMORY_FILE, items)
        self.send_json({"items": items})

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
        try:
            session_id = str(payload.get("sessionId") or "") or None
            message = str(payload.get("message") or "").strip()
            language = str(payload.get("language") or "pt-BR")
            if not message:
                self.send_json({"error": "Mensagem vazia."}, status=400)
                return
            # Tenta usar o NanobotRuntime
            try:
                rt = nanobot_runtime.NanobotRuntime.get_instance()
                if rt.is_ready:
                    sk = f"bmo_desktop:{session_id or 'local'}"
                    reply = rt.chat(message, session_key=sk)
                    if not reply:
                        reply = "BMO nao conseguiu processar sua mensagem. Tenta de novo?"
                else:
                    reply = f"BMO esta iniciando o motor de IA. Aguarde um momento. Erro: {rt.error}"
            except Exception as e:
                log_event("nanobot_chat_failed", error=str(e))
                reply = f"Nao consegui processar sua mensagem agora. Tenta de novo? (Erro interno: {str(e)[:100]})"
            session = save_chat_turn(session_id, message, reply)
            self.send_json({"reply": reply, "sessionId": session.get("id")})
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
    try:
        result = native_tools.longtask_mark_existing_finished_notified(tool_context())
        if result.get("marked"):
            log_event("longtasks_marked_notified_on_start", marked=result.get("marked"))
    except Exception as error:
        log_event("longtasks_startup_notify_migration_failed", error=str(error))

    # Inicializa o NanobotRuntime (AgentLoop real)
    try:
        rt_config = ensure_runtime_config()
        nanobot_runtime.NanobotRuntime.initialize(
            root=NANOBOT_SOURCE,
            config_path=rt_config,
            workspace=RUNTIME_WORKSPACE,
            app_data=APP_DATA_DIR,
            env={},
        )
        log_event("nanobot_runtime_started", ready=nanobot_runtime.NanobotRuntime.get_instance().is_ready)
    except Exception as error:
        log_event("nanobot_runtime_init_failed", error=str(error))
        sys.stderr.write(f"[BMO] NanobotRuntime init failed: {error}\n")

    threading.Thread(target=cron_loop, name="BMO Cron", daemon=True).start()
    threading.Thread(target=reminder_loop, name="BMO Reminders", daemon=True).start()
    threading.Thread(target=wakeword_loop, name="BMO Wake Word", daemon=True).start()
    log_event("backend_start", backend=f"http://{BACKEND_HOST}:{BACKEND_PORT}", nanobot_source=str(NANOBOT_SOURCE))
    server = ThreadingHTTPServer((BACKEND_HOST, BACKEND_PORT), BmoHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()


