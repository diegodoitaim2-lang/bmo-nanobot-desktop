from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BridgePaths:
    root: Path
    config_path: Path
    workspace: Path
    app_data_dir: Path


class BmoSubagentAdapter:
    """Small adapter so Nanobot's original spawn tool has a desktop backend."""

    def __init__(self, app_data_dir: Path, max_concurrent_subagents: int = 1):
        self.max_concurrent_subagents = max(1, int(max_concurrent_subagents or 1))
        self._store = app_data_dir / "nanobot" / "subagents.json"

    def _load(self) -> list[dict[str, Any]]:
        if not self._store.exists():
            return []
        try:
            data = json.loads(self._store.read_text(encoding="utf-8"))
            return [item for item in data.get("items", []) if isinstance(item, dict)]
        except Exception:
            return []

    def _save(self, items: list[dict[str, Any]]) -> None:
        self._store.parent.mkdir(parents=True, exist_ok=True)
        self._store.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_running_count(self) -> int:
        return sum(1 for item in self._load() if item.get("status") == "running")

    async def spawn(
        self,
        *,
        task: str,
        label: str | None = None,
        origin_channel: str = "bmo_desktop",
        origin_chat_id: str = "local",
        session_key: str = "bmo_desktop:local",
        origin_message_id: str | None = None,
        temperature: float | None = None,
        workspace_scope: Any | None = None,
    ) -> str:
        items = self._load()
        item = {
            "id": uuid.uuid4().hex[:12],
            "title": label or task[:80] or "Subagent task",
            "task": task,
            "status": "queued",
            "originChannel": origin_channel,
            "originChatId": origin_chat_id,
            "sessionKey": session_key,
            "originMessageId": origin_message_id,
            "temperature": temperature,
            "createdAt": int(time.time()),
        }
        items.insert(0, item)
        self._save(items)
        return f"Spawned desktop subagent task {item['id']}: {item['title']}"


class NanobotRuntime:
    def __init__(self, paths: BridgePaths, env: dict[str, str]):
        self.paths = paths
        self.env = dict(env)
        self.error = ""
        self.config: Any | None = None
        self.tools_config: Any | None = None
        self.registry: Any | None = None
        self.cron_service: Any | None = None
        self.memory_store: Any | None = None
        self.sessions: Any | None = None
        self.file_states: Any | None = None
        self.workspace_scope: Any | None = None
        self.registered: list[str] = []
        self._load()

    def _load(self) -> None:
        self.paths.root.mkdir(parents=True, exist_ok=True)
        self.paths.workspace.mkdir(parents=True, exist_ok=True)
        if str(self.paths.root) not in sys.path:
            sys.path.insert(0, str(self.paths.root))
        for key, value in self.env.items():
            if value and key not in os.environ:
                os.environ[key] = value

        try:
            from nanobot.agent.memory import MemoryStore
            from nanobot.agent.tools.context import ToolContext
            from nanobot.agent.tools.file_state import FileStates
            from nanobot.agent.tools.loader import ToolLoader
            from nanobot.agent.tools.registry import ToolRegistry
            from nanobot.config.loader import load_config, resolve_config_env_vars, set_config_path
            from nanobot.cron.service import CronService
            from nanobot.security.workspace_access import default_workspace_scope
            from nanobot.session.manager import SessionManager
        except Exception as exc:
            self.error = f"import failed: {exc}"
            raise

        set_config_path(self.paths.config_path)
        config = resolve_config_env_vars(load_config(self.paths.config_path))
        config.agents.defaults.workspace = str(self.paths.workspace)

        self.config = config
        self.tools_config = config.tools
        self.file_states = FileStates()
        self.sessions = SessionManager(self.paths.workspace)
        self.memory_store = MemoryStore(self.paths.workspace)
        self.cron_service = CronService(self.paths.config_path.parent / "cron" / "jobs.json")
        self.workspace_scope = default_workspace_scope(
            self.paths.workspace,
            bool(config.tools.restrict_to_workspace),
            source_channel="websocket",
        )
        subagents = BmoSubagentAdapter(
            self.paths.app_data_dir,
            max_concurrent_subagents=config.agents.defaults.max_concurrent_subagents,
        )
        ctx = ToolContext(
            config=config.tools,
            workspace=str(self.paths.workspace),
            subagent_manager=subagents,
            cron_service=self.cron_service,
            sessions=self.sessions,
            file_state_store=self.file_states,
            timezone=config.agents.defaults.timezone,
            workspace_sandbox=self.workspace_scope.sandbox_status,
            image_generation_provider_configs=config.providers.model_dump() if hasattr(config.providers, "model_dump") else None,
        )
        registry = ToolRegistry()
        self.registered = ToolLoader().load(ctx, registry, scope="core")
        self.registry = registry

    def definitions(self) -> list[dict[str, Any]]:
        if not self.registry:
            return []
        return self.registry.get_definitions()

    def tool_names(self) -> list[str]:
        if not self.registry:
            return []
        return list(self.registry.tool_names)

    def execute(
        self,
        name: str,
        params: dict[str, Any] | None = None,
        *,
        channel: str = "bmo_desktop",
        chat_id: str = "local",
        session_key: str = "bmo_desktop:local",
    ) -> Any:
        if not self.registry:
            raise RuntimeError("Nanobot registry is not loaded")
        params = params or {}

        from nanobot.agent.tools.context import RequestContext, bind_request_context, reset_request_context
        from nanobot.security.workspace_access import bind_workspace_scope, reset_workspace_scope

        req = RequestContext(
            channel=channel,
            chat_id=chat_id,
            session_key=session_key,
            metadata={"source": "bmo_desktop"},
        )
        request_token = bind_request_context(req)
        scope_token = bind_workspace_scope(self.workspace_scope)
        try:
            for tool_name in self.registry.tool_names:
                tool = self.registry.get(tool_name)
                setter = getattr(tool, "set_context", None)
                if callable(setter):
                    setter(req)
            return _run_async(self.registry.execute(name, params))
        finally:
            reset_workspace_scope(scope_token)
            reset_request_context(request_token)

    def status(self) -> dict[str, Any]:
        return {
            "available": bool(self.registry),
            "error": self.error,
            "source": str(self.paths.root),
            "config": str(self.paths.config_path),
            "workspace": str(self.paths.workspace),
            "toolCount": len(self.tool_names()),
            "tools": self.tool_names(),
            "cronStore": str(self.paths.config_path.parent / "cron" / "jobs.json"),
            "memoryDir": str(self.paths.workspace / "memory"),
        }


_LOCK = threading.Lock()
_RUNTIME: NanobotRuntime | None = None
_FINGERPRINT: tuple[Any, ...] | None = None


def _run_async(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    thread_result: dict[str, Any] = {}

    def runner() -> None:
        try:
            thread_result["value"] = asyncio.run(coro)
        except BaseException as exc:
            thread_result["error"] = exc

    thread = threading.Thread(target=runner, name="NanobotBridgeAsync", daemon=True)
    thread.start()
    thread.join()
    if "error" in thread_result:
        raise thread_result["error"]
    return thread_result.get("value")


def _fingerprint(paths: BridgePaths, env: dict[str, str]) -> tuple[Any, ...]:
    try:
        mtime = paths.config_path.stat().st_mtime
    except OSError:
        mtime = 0
    env_sig = tuple(sorted((key, bool(value)) for key, value in env.items()))
    return (str(paths.root), str(paths.config_path), str(paths.workspace), mtime, env_sig)


def runtime(root: Path, config_path: Path, workspace: Path, app_data_dir: Path, env: dict[str, str]) -> NanobotRuntime:
    global _RUNTIME, _FINGERPRINT
    paths = BridgePaths(root=root, config_path=config_path, workspace=workspace, app_data_dir=app_data_dir)
    fp = _fingerprint(paths, env)
    with _LOCK:
        if _RUNTIME is None or _FINGERPRINT != fp:
            _RUNTIME = NanobotRuntime(paths, env)
            _FINGERPRINT = fp
        return _RUNTIME


def execute_tool(
    root: Path,
    config_path: Path,
    workspace: Path,
    app_data_dir: Path,
    env: dict[str, str],
    name: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rt = runtime(root, config_path, workspace, app_data_dir, env)
    result = rt.execute(name, params or {})
    ok = not (isinstance(result, str) and result.startswith("Error"))
    return {"ok": ok, "tool": name, "params": params or {}, "result": result, "source": "nanobot-original"}


def registry_payload(root: Path, config_path: Path, workspace: Path, app_data_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    try:
        rt = runtime(root, config_path, workspace, app_data_dir, env)
        tools = []
        for definition in rt.definitions():
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
        return {"tools": tools, "definitions": rt.definitions(), "status": rt.status()}
    except Exception as exc:
        return {
            "tools": [],
            "definitions": [],
            "status": {"available": False, "error": str(exc), "source": str(root)},
        }


def tool_info(root: Path, config_path: Path, workspace: Path, app_data_dir: Path, env: dict[str, str], name: str) -> dict[str, Any]:
    payload = registry_payload(root, config_path, workspace, app_data_dir, env)
    for definition in payload.get("definitions", []):
        fn = definition.get("function", {}) if isinstance(definition, dict) else {}
        if fn.get("name") == name:
            return {"ok": True, "tool": definition, "source": "nanobot-original"}
    return {"ok": False, "error": f"Tool not found: {name}", "available": [item["id"] for item in payload.get("tools", [])]}


def channels_payload(root: Path) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    items: list[dict[str, Any]] = []
    try:
        channels_pkg = importlib.import_module("nanobot.channels")
        for finder in getattr(channels_pkg, "__path__", []):
            pass
        import pkgutil

        internal = {"base", "manager", "registry"}
        for module in pkgutil.iter_modules(channels_pkg.__path__):
            if module.name.startswith("_") or module.name in internal:
                continue
            items.append({
                "id": module.name,
                "label": module.name.replace("_", " ").title(),
                "fields": [],
                "enabled": False,
                "configured": False,
                "status": "original-module",
            })
    except Exception:
        items = []
    return {"channels": sorted(items, key=lambda item: item["id"])}


def memory_payload(root: Path, config_path: Path, workspace: Path, app_data_dir: Path, env: dict[str, str]) -> dict[str, Any]:
    rt = runtime(root, config_path, workspace, app_data_dir, env)
    store = rt.memory_store
    if store is None:
        return {"ok": False, "error": "MemoryStore is not loaded"}
    return {
        "ok": True,
        "memory": store.read_memory(),
        "soul": store.read_soul(),
        "user": store.read_user(),
        "historyPath": str(store.history_file),
        "memoryPath": str(store.memory_file),
    }


def append_history(root: Path, config_path: Path, workspace: Path, app_data_dir: Path, env: dict[str, str], text: str) -> dict[str, Any]:
    rt = runtime(root, config_path, workspace, app_data_dir, env)
    store = rt.memory_store
    if store is None:
        return {"ok": False, "error": "MemoryStore is not loaded"}
    cursor = store.append_history(text)
    return {"ok": True, "cursor": cursor, "historyPath": str(store.history_file)}
