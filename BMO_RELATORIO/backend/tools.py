from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import smtplib
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any


MAX_TEXT_READ_BYTES = 1_000_000
MAX_STDIO_CHARS = 80_000
ALLOWED_COMMANDS = {
    "python",
    "python.exe",
    "pythonw",
    "pythonw.exe",
    "py",
    "py.exe",
    "pip",
    "pip.exe",
    "git",
    "git.exe",
    "node",
    "node.exe",
    "npm",
    "npm.cmd",
}


@dataclass(frozen=True)
class ToolContext:
    workspace: Path
    app_data_dir: Path
    root: Path
    env: dict[str, str]


class ToolError(RuntimeError):
    pass


def windows_process_options() -> tuple[Any, int]:
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return startupinfo, creationflags


def _json_load(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> int:
    return int(time.time())


def ensure_workspace(ctx: ToolContext) -> Path:
    ctx.workspace.mkdir(parents=True, exist_ok=True)
    return ctx.workspace.resolve(strict=False)


def resolve_workspace_path(ctx: ToolContext, raw_path: str | None, *, must_exist: bool = False) -> Path:
    root = ensure_workspace(ctx)
    value = str(raw_path or "").strip()
    candidate = Path(value) if value else root
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ToolError("Caminho bloqueado: fora do workspace do BMO.") from exc
    return resolved


def _file_info(path: Path, root: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "name": path.name,
        "path": str(path),
        "relativePath": str(path.relative_to(root)).replace("\\", "/"),
        "isDir": path.is_dir(),
        "size": stat.st_size,
        "modifiedAt": int(stat.st_mtime),
    }


def list_dir(ctx: ToolContext, path: str = "", recursive: bool = False, limit: int = 500) -> dict[str, Any]:
    target = resolve_workspace_path(ctx, path, must_exist=True)
    if not target.is_dir():
        raise ToolError("O caminho informado nao e uma pasta.")
    root = ensure_workspace(ctx)
    iterator = target.rglob("*") if recursive else target.iterdir()
    items = []
    for item in iterator:
        items.append(_file_info(item, root))
        if len(items) >= max(1, min(int(limit), 5000)):
            break
    return {"ok": True, "root": str(root), "path": str(target), "items": items}


def read_file(ctx: ToolContext, path: str, offset: int = 1, limit: int = 2000, force: bool = False) -> dict[str, Any]:
    target = resolve_workspace_path(ctx, path, must_exist=True)
    if target.is_dir():
        raise ToolError("O caminho informado e uma pasta.")
    size = target.stat().st_size
    if size > MAX_TEXT_READ_BYTES and not force:
        raise ToolError("Arquivo grande demais para leitura direta. Use force=true se tiver certeza.")
    data = target.read_text(encoding="utf-8", errors="replace")
    lines = data.splitlines()
    start = max(1, int(offset)) - 1
    end = min(len(lines), start + max(1, min(int(limit), 20_000)))
    return {
        "ok": True,
        "path": str(target),
        "size": size,
        "offset": start + 1,
        "lineCount": len(lines),
        "content": "\n".join(lines[start:end]),
    }


def write_file(
    ctx: ToolContext,
    path: str,
    content: str,
    append: bool = False,
    overwrite: bool = True,
) -> dict[str, Any]:
    target = resolve_workspace_path(ctx, path, must_exist=False)
    if target.exists() and target.is_dir():
        raise ToolError("O caminho informado e uma pasta.")
    if target.exists() and not overwrite and not append:
        raise ToolError("Arquivo ja existe e overwrite=false.")
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with target.open(mode, encoding="utf-8", newline="") as file:
        file.write(str(content))
    return {"ok": True, "path": str(target), "size": target.stat().st_size}


def delete_path(ctx: ToolContext, path: str, recursive: bool = False) -> dict[str, Any]:
    target = resolve_workspace_path(ctx, path, must_exist=True)
    if target.is_dir():
        if not recursive:
            raise ToolError("Para apagar pasta, envie recursive=true.")
        shutil.rmtree(target)
    else:
        target.unlink()
    return {"ok": True, "path": str(target), "deleted": True}


def move_path(ctx: ToolContext, src: str, dst: str, overwrite: bool = False) -> dict[str, Any]:
    source = resolve_workspace_path(ctx, src, must_exist=True)
    target = resolve_workspace_path(ctx, dst, must_exist=False)
    if target.exists():
        if not overwrite:
            raise ToolError("Destino ja existe e overwrite=false.")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    return {"ok": True, "from": str(source), "to": str(target)}


def metadata(ctx: ToolContext, path: str) -> dict[str, Any]:
    root = ensure_workspace(ctx)
    target = resolve_workspace_path(ctx, path, must_exist=True)
    info = _file_info(target, root)
    if target.is_file():
        h = hashlib.sha256()
        with target.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                h.update(chunk)
        info["sha256"] = h.hexdigest()
    return {"ok": True, "metadata": info}


def _split_command(command: str | list[str]) -> list[str]:
    if isinstance(command, list):
        return [str(part) for part in command if str(part)]
    if os.name == "nt":
        return [part.strip('"') for part in re.findall(r'"[^"]+"|\S+', str(command)) if part]
    import shlex

    return shlex.split(str(command))


def shell_exec(
    ctx: ToolContext,
    command: str | list[str],
    cwd: str | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    args = _split_command(command)
    if not args:
        raise ToolError("Comando vazio.")
    executable = Path(args[0].strip('"')).name.lower()
    if executable not in ALLOWED_COMMANDS:
        raise ToolError(f"Comando nao permitido pelo sandbox: {executable}")
    workdir = resolve_workspace_path(ctx, cwd or "", must_exist=True)
    if not workdir.is_dir():
        raise ToolError("cwd precisa ser uma pasta dentro do workspace.")
    startupinfo, creationflags = windows_process_options()
    result = subprocess.run(
        args,
        cwd=str(workdir),
        env={**os.environ, **ctx.env},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=max(1, min(int(timeout), 120)),
        shell=False,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout[-MAX_STDIO_CHARS:],
        "stderr": result.stderr[-MAX_STDIO_CHARS:],
        "cwd": str(workdir),
        "command": args,
    }


def web_search(ctx: ToolContext, query: str, limit: int = 5) -> dict[str, Any]:
    clean = str(query or "").strip()
    if not clean:
        raise ToolError("Consulta vazia.")
    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": clean})
    request = urllib.request.Request(url, headers={"User-Agent": "BMO/1.0"})
    with urllib.request.urlopen(request, timeout=12) as response:
        html = response.read().decode("utf-8", errors="replace")
    results = []
    pattern = re.compile(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    for match in pattern.finditer(html):
        href = urllib.parse.unquote(match.group(1))
        title = re.sub(r"<[^>]+>", "", match.group(2))
        title = re.sub(r"\s+", " ", title).strip()
        if href.startswith("//duckduckgo.com/l/?"):
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
            href = parsed.get("uddg", [href])[0]
        results.append({"title": title, "url": href})
        if len(results) >= max(1, min(int(limit), 10)):
            break
    return {"ok": True, "query": clean, "results": results}


def _cron_file(ctx: ToolContext) -> Path:
    return ctx.app_data_dir / "cron" / "jobs.json"


def _load_cron(ctx: ToolContext) -> list[dict[str, Any]]:
    data = _json_load(_cron_file(ctx), {"items": []})
    return data.get("items", []) if isinstance(data, dict) else []


def _save_cron(ctx: ToolContext, items: list[dict[str, Any]]) -> None:
    _json_write(_cron_file(ctx), {"items": items})


def _next_run_from_payload(payload: dict[str, Any]) -> int:
    if payload.get("runAt"):
        return int(payload["runAt"])
    if payload.get("seconds"):
        return _now() + max(1, int(payload["seconds"]))
    cron = str(payload.get("cron") or "").strip()
    match = re.fullmatch(r"\*/(\d+)\s+\*\s+\*\s+\*\s+\*", cron)
    if match:
        return _now() + max(60, int(match.group(1)) * 60)
    return _now() + 60


def cron_create(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    command = str(payload.get("command") or "").strip()
    if not command:
        raise ToolError("Job sem command.")
    items = _load_cron(ctx)
    job = {
        "id": uuid.uuid4().hex[:12],
        "cron": str(payload.get("cron") or ""),
        "command": command,
        "next_run": _next_run_from_payload(payload),
        "status": "scheduled",
        "createdAt": _now(),
        "lastResult": None,
    }
    items.append(job)
    _save_cron(ctx, items)
    return {"ok": True, "job": job, "items": items}


def cron_list(ctx: ToolContext) -> dict[str, Any]:
    return {"ok": True, "items": _load_cron(ctx)}


def cron_delete(ctx: ToolContext, job_id: str) -> dict[str, Any]:
    items = [item for item in _load_cron(ctx) if str(item.get("id")) != str(job_id)]
    _save_cron(ctx, items)
    return {"ok": True, "items": items}


def cron_run(ctx: ToolContext, job_id: str) -> dict[str, Any]:
    items = _load_cron(ctx)
    selected = next((item for item in items if str(item.get("id")) == str(job_id)), None)
    if not selected:
        raise ToolError("Job nao encontrado.")
    result = shell_exec(ctx, str(selected.get("command") or ""), timeout=60)
    selected["lastResult"] = result
    selected["lastRun"] = _now()
    selected["status"] = "scheduled"
    selected["next_run"] = _next_run_from_payload(selected)
    _save_cron(ctx, items)
    return {"ok": True, "job": selected}


def cron_tick(ctx: ToolContext) -> None:
    items = _load_cron(ctx)
    changed = False
    for item in items:
        if str(item.get("status")) != "scheduled":
            continue
        if int(item.get("next_run") or 0) > _now():
            continue
        try:
            item["lastResult"] = shell_exec(ctx, str(item.get("command") or ""), timeout=60)
        except Exception as exc:
            item["lastResult"] = {"ok": False, "error": str(exc)}
        item["lastRun"] = _now()
        item["next_run"] = _next_run_from_payload(item)
        changed = True
    if changed:
        _save_cron(ctx, items)


_long_tasks_lock = threading.Lock()
_long_task_threads: dict[str, threading.Thread] = {}


def _longtask_file(ctx: ToolContext) -> Path:
    return ctx.app_data_dir / "longtasks" / "tasks.json"


def _load_longtasks(ctx: ToolContext) -> list[dict[str, Any]]:
    data = _json_load(_longtask_file(ctx), {"items": []})
    return data.get("items", []) if isinstance(data, dict) else []


def _save_longtasks(ctx: ToolContext, items: list[dict[str, Any]]) -> None:
    _json_write(_longtask_file(ctx), {"items": items})


def _update_longtask(ctx: ToolContext, task_id: str, **changes: Any) -> None:
    with _long_tasks_lock:
        items = _load_longtasks(ctx)
        for item in items:
            if str(item.get("id")) == task_id:
                item.update(changes)
                break
        _save_longtasks(ctx, items)


def longtask_start(ctx: ToolContext, payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title") or payload.get("objective") or "Tarefa longa do BMO").strip()
    command = str(payload.get("command") or "").strip()
    task_id = uuid.uuid4().hex[:12]
    output_file = resolve_workspace_path(ctx, f"longtask_{task_id}.txt", must_exist=False)
    task = {
        "id": task_id,
        "title": title,
        "command": command,
        "status": "running",
        "progress": 0,
        "createdAt": _now(),
        "updatedAt": _now(),
        "outputPath": str(output_file),
        "result": None,
    }
    items = _load_longtasks(ctx)
    items.append(task)
    _save_longtasks(ctx, items)

    def worker() -> None:
        try:
            _update_longtask(ctx, task_id, progress=15, updatedAt=_now())
            if command:
                result = shell_exec(ctx, command, timeout=int(payload.get("timeout") or 120))
                output_file.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            else:
                result = {"ok": True, "message": f"Tarefa registrada: {title}"}
                output_file.write_text(result["message"], encoding="utf-8")
            _update_longtask(ctx, task_id, status="concluido", progress=100, result=result, updatedAt=_now())
        except Exception as exc:
            output_file.write_text(f"Erro: {exc}", encoding="utf-8")
            _update_longtask(ctx, task_id, status="erro", progress=100, result={"ok": False, "error": str(exc)}, updatedAt=_now())

    thread = threading.Thread(target=worker, name=f"BMO longtask {task_id}", daemon=True)
    _long_task_threads[task_id] = thread
    thread.start()
    return {"ok": True, "task": task}


def longtask_status(ctx: ToolContext, task_id: str | None = None) -> dict[str, Any]:
    items = _load_longtasks(ctx)
    if task_id:
        item = next((item for item in items if str(item.get("id")) == str(task_id)), None)
        if not item:
            raise ToolError("Tarefa longa nao encontrada.")
        return {"ok": True, "task": item}
    return {"ok": True, "items": items}


def longtask_cancel(ctx: ToolContext, task_id: str) -> dict[str, Any]:
    _update_longtask(ctx, task_id, status="cancelado", updatedAt=_now())
    return longtask_status(ctx, task_id)


def _embedding_file(ctx: ToolContext) -> Path:
    return ctx.app_data_dir / "embeddings" / "index.json"


def _tokens(text: str) -> dict[str, float]:
    counts: dict[str, float] = {}
    for token in re.findall(r"[A-Za-zÀ-ÿ0-9]{3,}", text.lower()):
        counts[token] = counts.get(token, 0.0) + 1.0
    return counts


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[key] * b[key] for key in common)
    na = math.sqrt(sum(value * value for value in a.values()))
    nb = math.sqrt(sum(value * value for value in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def vector_upsert(ctx: ToolContext, chunks: list[str], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    index = _json_load(_embedding_file(ctx), {"items": []})
    items = index.get("items", []) if isinstance(index, dict) else []
    inserted = []
    for chunk in chunks:
        text = str(chunk or "").strip()
        if not text:
            continue
        item_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        item = {
            "id": item_id,
            "text": text,
            "vector": _tokens(text),
            "metadata": metadata or {},
            "updatedAt": _now(),
        }
        items = [old for old in items if old.get("id") != item_id]
        items.append(item)
        inserted.append({"id": item_id, "text": text[:160]})
    _json_write(_embedding_file(ctx), {"items": items})
    return {"ok": True, "inserted": inserted, "count": len(items)}


def vector_search(ctx: ToolContext, query: str, top_k: int = 5) -> dict[str, Any]:
    qv = _tokens(str(query or ""))
    index = _json_load(_embedding_file(ctx), {"items": []})
    items = index.get("items", []) if isinstance(index, dict) else []
    scored = []
    for item in items:
        score = _cosine(qv, item.get("vector") or {})
        if score > 0:
            scored.append({"score": score, "id": item.get("id"), "text": item.get("text"), "metadata": item.get("metadata")})
    scored.sort(key=lambda item: float(item["score"]), reverse=True)
    return {"ok": True, "query": query, "items": scored[: max(1, min(int(top_k), 20))]}


def vector_summary(ctx: ToolContext, limit: int = 12) -> dict[str, Any]:
    index = _json_load(_embedding_file(ctx), {"items": []})
    items = index.get("items", []) if isinstance(index, dict) else []
    recent = items[-max(1, min(int(limit), 50)) :]
    return {"ok": True, "count": len(items), "summary": "\n".join(str(item.get("text") or "")[:300] for item in recent)}


def send_channel(ctx: ToolContext, name: str, payload: dict[str, Any]) -> dict[str, Any]:
    channel = name.lower().strip()
    text = str(payload.get("payload") or payload.get("text") or payload.get("message") or "").strip()
    if not text:
        raise ToolError("Mensagem vazia.")
    if channel == "discord":
        webhook = ctx.env.get("DISCORD_WEBHOOK_URL") or str(payload.get("webhook") or "")
        if not webhook:
            raise ToolError("Webhook do Discord nao configurado.")
        data = json.dumps({"content": text}).encode("utf-8")
        req = urllib.request.Request(webhook, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return {"ok": 200 <= response.status < 300, "channel": channel, "status": response.status}
    if channel == "slack":
        webhook = ctx.env.get("SLACK_WEBHOOK_URL") or str(payload.get("webhook") or "")
        if not webhook:
            raise ToolError("Webhook do Slack nao configurado.")
        data = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(webhook, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return {"ok": 200 <= response.status < 300, "channel": channel, "status": response.status}
    if channel == "telegram":
        token = ctx.env.get("TELEGRAM_BOT_TOKEN") or str(payload.get("token") or "")
        chat_id = ctx.env.get("TELEGRAM_CHAT_ID") or str(payload.get("chat_id") or payload.get("chatId") or "")
        if not token or not chat_id:
            raise ToolError("Token/chat_id do Telegram nao configurado.")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        with urllib.request.urlopen(url, data=data, timeout=15) as response:
            return {"ok": 200 <= response.status < 300, "channel": channel, "status": response.status}
    if channel == "email":
        host = ctx.env.get("SMTP_HOST")
        user = ctx.env.get("SMTP_USER")
        password = ctx.env.get("SMTP_PASSWORD")
        to_addr = str(payload.get("to") or ctx.env.get("EMAIL_TO") or "")
        if not host or not user or not password or not to_addr:
            raise ToolError("SMTP_HOST, SMTP_USER, SMTP_PASSWORD e destinatario sao obrigatorios.")
        msg = EmailMessage()
        msg["From"] = user
        msg["To"] = to_addr
        msg["Subject"] = str(payload.get("subject") or "Mensagem do BMO")
        msg.set_content(text)
        with smtplib.SMTP_SSL(host, int(ctx.env.get("SMTP_PORT") or 465), timeout=20) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        return {"ok": True, "channel": channel}
    raise ToolError(f"Canal {channel} ainda precisa de credenciais ou adaptador especifico.")


def registry() -> dict[str, Any]:
    tools = [
        {"name": "file.list", "description": "Lista arquivos dentro do workspace.", "scopes": ["core", "filesystem"]},
        {"name": "file.read", "description": "Le arquivo de texto dentro do workspace.", "scopes": ["core", "filesystem"]},
        {"name": "file.write", "description": "Escreve arquivo dentro do workspace.", "scopes": ["core", "filesystem"]},
        {"name": "file.delete", "description": "Remove arquivo ou pasta dentro do workspace.", "scopes": ["filesystem"]},
        {"name": "file.move", "description": "Move arquivo dentro do workspace.", "scopes": ["filesystem"]},
        {"name": "shell.exec", "description": "Executa comando permitido no workspace.", "scopes": ["sandbox"]},
        {"name": "web.search", "description": "Busca web simples.", "scopes": ["web"]},
        {"name": "cron", "description": "Cria, lista, executa e remove jobs.", "scopes": ["scheduler"]},
        {"name": "longtask", "description": "Executa tarefas assincronas monitoraveis.", "scopes": ["async"]},
        {"name": "memory.vector", "description": "Memoria vetorial local baseada em similaridade lexical.", "scopes": ["memory"]},
        {"name": "channel", "description": "Envio por canais configurados.", "scopes": ["channels"]},
    ]
    return {"ok": True, "tools": tools}


def registry_info(name: str) -> dict[str, Any]:
    tools = registry()["tools"]
    selected = next((item for item in tools if item["name"] == name), None)
    if not selected:
        raise ToolError("Ferramenta nao encontrada.")
    return {"ok": True, "tool": selected}
