"""
nanobot_runtime.py — Gerencia o AgentLoop real do Nanobot para o BMO.

Substitui o motor de chat manual do BMO pelo AgentLoop completo do Nanobot,
permitindo que TODAS as ferramentas nativas do Nanobot (filesystem, shell,
web search, spawn, cron, memory, MCP, skills, etc.) estejam disponíveis.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# ============================================================
# Logging
# ============================================================

def _log(event: str, **fields: Any) -> None:
    try:
        sys.stderr.write(
            json.dumps({"event": event, **fields}, ensure_ascii=False, default=str) + "\n"
        )
    except Exception:
        pass


# ============================================================
# Async runner — roda um async callable num thread com event loop
# ============================================================

_ASYNC_LOOP: asyncio.AbstractEventLoop | None = None
_ASYNC_THREAD: threading.Thread | None = None
_ASYNC_LOCK = threading.Lock()


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _ASYNC_LOOP, _ASYNC_THREAD
    if _ASYNC_LOOP is not None and not _ASYNC_LOOP.is_closed():
        return _ASYNC_LOOP
    with _ASYNC_LOCK:
        if _ASYNC_LOOP is not None and not _ASYNC_LOOP.is_closed():
            return _ASYNC_LOOP
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=loop.run_forever, name="NanobotAsyncLoop", daemon=True)
        t.start()
        _ASYNC_LOOP = loop
        _ASYNC_THREAD = t
        return loop


def _run_async(coro) -> Any:
    """Roda uma coroutine e retorna o resultado, seguro para chamar de qualquer thread."""
    loop = _ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=300)  # 5 min timeout


# ============================================================
# Adapter para o SubagentManager do Nanobot
# ============================================================

@dataclass
class _Paths:
    root: Path
    config: Path
    workspace: Path
    app_data: Path
    env: dict[str, str]


class _BmoSubagentAdapter:
    """Adapta a chamada de subagente do Nanobot para o sistema de subagentes do BMO."""

    def __init__(self, paths: _Paths):
        self.paths = paths
        self._store = paths.app_data / "nanobot" / "subagents.json"
        self._lock = threading.Lock()

    def _load(self) -> list[dict[str, Any]]:
        if not self._store.exists():
            return []
        try:
            return json.loads(self._store.read_text(encoding="utf-8")).get("items", [])
        except Exception:
            return []

    def _save(self, items: list[dict[str, Any]]) -> None:
        self._store.parent.mkdir(parents=True, exist_ok=True)
        self._store.write_text(
            json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_running_count(self) -> int:
        return sum(1 for item in self._load() if item.get("status") == "running")

    def spawn(
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
        import threading as _t

        item_id = uuid.uuid4().hex[:12]
        title = label or task[:80] or "Subagente BMO"

        with self._lock:
            items = self._load()
            items.insert(0, {
                "id": item_id,
                "title": title,
                "task": task,
                "status": "running",
                "progress": 0,
                "originChannel": origin_channel,
                "originChatId": origin_chat_id,
                "sessionKey": session_key,
                "createdAt": int(time.time()),
                "notified": False,
            })
            self._save(items)

        def _runner():
            try:
                runtime = NanobotRuntime.get_instance()
                result_text = _run_async(
                    runtime.agent_loop.process_direct(
                        content=task,
                        session_key=session_key,
                        channel=origin_channel,
                        chat_id=origin_chat_id,
                    )
                )
                out_dir = self.paths.workspace / "subagents"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / f"{item_id}.md"
                content_text = (result_text.content if result_text else "") or ""
                out_file.write_text(
                    f"# {title}\n\n**Tarefa:** {task}\n\n**Resultado:**\n\n{content_text}\n",
                    encoding="utf-8",
                )
                with self._lock:
                    items = self._load()
                    for it in items:
                        if it.get("id") == item_id:
                            it["status"] = "concluido"
                            it["updatedAt"] = int(time.time())
                            it["result"] = content_text
                            it["outputPath"] = str(out_file)
                            break
                    self._save(items)
                _log("subagent_finished", id=item_id, title=title)
            except Exception as exc:
                _log("subagent_failed", id=item_id, title=title, error=str(exc))
                with self._lock:
                    items = self._load()
                    for it in items:
                        if it.get("id") == item_id:
                            it["status"] = "erro"
                            it["updatedAt"] = int(time.time())
                            it["error"] = str(exc)
                            break
                    self._save(items)

        _t.Thread(target=_runner, name=f"BmoSubagent-{item_id}", daemon=True).start()
        return f"Subagente criado: {item_id}"


# ============================================================
# NanobotRuntime — Singleton que gerencia o AgentLoop
# ============================================================

class NanobotRuntime:
    _instance: "NanobotRuntime | None" = None
    _lock = threading.Lock()

    def __init__(self, paths: _Paths):
        self.paths = paths
        self._agent_loop: Any = None
        self._initialized = False
        self._error = ""
        self._cron_service: Any = None
        self._init()

    @classmethod
    def get_instance(cls) -> "NanobotRuntime":
        if cls._instance is None:
            raise RuntimeError("NanobotRuntime nao foi inicializado. Chame NanobotRuntime.initialize() primeiro.")
        return cls._instance

    @classmethod
    def initialize(cls, root: Path, config_path: Path, workspace: Path, app_data: Path, env: dict[str, str]) -> "NanobotRuntime":
        with cls._lock:
            if cls._instance is not None:
                # Se mudou a config, recria
                return cls._instance
            paths = _Paths(root, config_path, workspace, app_data, env)
            rt = cls(paths)
            cls._instance = rt
            return rt

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            if cls._instance is not None:
                try:
                    _run_async(cls._instance._agent_loop.close_mcp())
                except Exception:
                    pass
                cls._instance = None

    def _init(self) -> None:
        try:
            self.paths.root.mkdir(parents=True, exist_ok=True)
            self.paths.workspace.mkdir(parents=True, exist_ok=True)

            # Garantir que o nanobot source está no path
            source = str(self.paths.root)
            if source not in sys.path:
                sys.path.insert(0, source)

            # Carregar env vars
            for key, value in self.paths.env.items():
                if value and key not in os.environ:
                    os.environ[key] = value

            # Importar nanobot (deve estar no PYTHONPATH ou sys.path)
            from nanobot.agent.loop import AgentLoop
            from nanobot.agent.memory import MemoryStore
            from nanobot.agent.tools.context import ToolContext
            from nanobot.agent.tools.file_state import FileStates
            from nanobot.agent.tools.loader import ToolLoader
            from nanobot.agent.tools.registry import ToolRegistry
            from nanobot.bus.queue import MessageBus
            from nanobot.config.loader import load_config, resolve_config_env_vars, set_config_path
            from nanobot.config.schema import AgentDefaults, Config
            from nanobot.cron.service import CronService
            from nanobot.providers.factory import make_provider
            from nanobot.security.workspace_access import default_workspace_scope
            from nanobot.session.manager import SessionManager

            # Marcar path do config
            set_config_path(self.paths.config)

            # Carregar config
            config = resolve_config_env_vars(load_config(self.paths.config))
            config.agents.defaults.workspace = str(self.paths.workspace)

            # Remover any AI providers
            # Já que o BMO quer usar OpenRouter (configurado pelo usuário)
            
            # Criar subagente adapter
            subagent_adapter = _BmoSubagentAdapter(self.paths)
            
            # Workspace scope
            restrict = bool(config.tools.restrict_to_workspace) if hasattr(config.tools, 'restrict_to_workspace') else True
            workspace_scope = default_workspace_scope(
                self.paths.workspace,
                restrict,
                source_channel="websocket"
            )
            sandbox_status = workspace_scope.sandbox_status

            # Session manager
            sessions = SessionManager(self.paths.workspace)

            # File states
            file_states = FileStates()

            # Memory store
            memory_store = MemoryStore(self.paths.workspace)

            # Cron
            cron_dir = self.paths.config.parent / "cron"
            cron_dir.mkdir(parents=True, exist_ok=True)
            cron_service = CronService(cron_dir / "jobs.json")

            # Tool context
            ctx = ToolContext(
                config=config.tools,
                workspace=str(self.paths.workspace),
                subagent_manager=subagent_adapter,
                cron_service=cron_service,
                sessions=sessions,
                file_state_store=file_states,
                timezone="America/Sao_Paulo",
                workspace_sandbox=sandbox_status,
                image_generation_provider_configs=(
                    config.providers.model_dump() 
                    if hasattr(config.providers, "model_dump") 
                    else None
                ),
            )

            # Carregar tools
            registry = ToolRegistry()
            ToolLoader().load(ctx, registry, scope="core")

            # Bus
            bus = MessageBus()

            # Provider
            provider = make_provider(config)

            # Pegar model presets
            model_presets = {}
            if hasattr(config.agents, 'defaults') and hasattr(config.agents.defaults, 'model_preset'):
                mp = config.agents.defaults.model_preset
                if mp and hasattr(config.agents, 'model_presets'):
                    model_presets = dict(config.agents.model_presets) if config.agents.model_presets else {}

            # Criar AgentLoop
            image_cfgs = (
                config.providers.model_dump()
                if hasattr(config.providers, "model_dump")
                else None
            )

            loop = AgentLoop(
                bus=bus,
                provider=provider,
                workspace=self.paths.workspace,
                model=config.agents.defaults.model,
                max_iterations=getattr(config.agents.defaults, 'max_tool_iterations', 25),
                context_window_tokens=config.agents.defaults.context_window_tokens,
                max_concurrent_subagents=getattr(config.agents.defaults, 'max_concurrent_subagents', 3),
                restrict_to_workspace=restrict,
                session_manager=sessions,
                cron_service=cron_service,
                tools_config=config.tools,
                image_generation_provider_configs=image_cfgs,
                timezone="America/Sao_Paulo",
                disabled_skills=list(getattr(config.agents.defaults, 'disabled_skills', [])),
                model_presets=model_presets,
            )

            self._agent_loop = loop
            self._cron_service = cron_service
            self._registry = registry
            self._sessions = sessions
            self._memory_store = memory_store
            self._tool_context = ctx
            self._initialized = True
            self._error = ""

            _log("nanobot_runtime_initialized", workspace=str(self.paths.workspace), tools=registry.tool_names)

        except Exception as exc:
            self._error = str(exc)
            self._initialized = False
            _log("nanobot_runtime_init_failed", error=str(exc))
            raise

    @property
    def agent_loop(self) -> Any:
        if not self._initialized or self._agent_loop is None:
            raise RuntimeError(f"NanobotRuntime nao inicializado: {self._error}")
        return self._agent_loop

    @property
    def registry(self) -> Any:
        return self._registry

    @property
    def sessions(self) -> Any:
        return self._sessions

    @property
    def memory_store(self) -> Any | None:
        return self._memory_store

    @property
    def is_ready(self) -> bool:
        return self._initialized and self._agent_loop is not None

    @property
    def error(self) -> str:
        return self._error

    @property
    def tool_names(self) -> list[str]:
        names = set()
        if self._registry:
            names.update(self._registry.tool_names)
        if self._agent_loop is not None:
            names.update(self._agent_loop.tool_names)
        return sorted(names)

    def chat(self, message: str, session_key: str | None = None) -> str:
        """Envia mensagem para o AgentLoop real do Nanobot e retorna a resposta."""
        if not self.is_ready:
            raise RuntimeError(f"NanobotRuntime nao esta pronto: {self._error}")

        sk = session_key or "bmo_desktop:local"

        result = _run_async(
            self._agent_loop.process_direct(
                content=message,
                session_key=sk,
                channel="bmo_desktop",
                chat_id="local",
            )
        )
        return (result.content if result else "") or ""

    def execute_tool(self, name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Executa uma ferramenta via Nanobot ToolRegistry diretamente."""
        if not self.is_ready or not self._registry:
            raise RuntimeError("NanobotRuntime nao esta pronto")

        from nanobot.agent.tools.context import (
            RequestContext,
            bind_request_context,
            reset_request_context,
        )
        from nanobot.security.workspace_access import (
            bind_workspace_scope,
            reset_workspace_scope,
        )
        from nanobot.agent.tools.file_state import bind_file_states, reset_file_states

        req = RequestContext(
            channel="bmo_desktop",
            chat_id="local",
            session_key="bmo_desktop:local",
            metadata={"source": "bmo_desktop"},
        )
        request_token = bind_request_context(req)
        scope_token = bind_workspace_scope(self._agent_loop.workspace_scopes.default_scope())
        fs_token = bind_file_states(self._agent_loop._file_state_store.for_session("bmo_desktop:local"))

        try:
            return _run_async(self._registry.execute(name, params or {}))
        finally:
            reset_workspace_scope(scope_token)
            reset_request_context(request_token)
            reset_file_states(fs_token)

    def definitions(self) -> list[dict[str, Any]]:
        """Retorna definições de tools para expor ao LLM."""
        if not self._registry:
            return []
        return self._registry.get_definitions()

    def close(self) -> None:
        if self._agent_loop is not None:
            try:
                _run_async(self._agent_loop.close_mcp())
            except Exception:
                pass
            self._agent_loop = None
