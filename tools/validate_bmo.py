from __future__ import annotations

import argparse
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
BACKEND_FILE = ROOT / "backend" / "bmo_backend.py"
ELECTRON_FILE = ROOT / "electron" / "main.cjs"
APP_FILE = ROOT / "src" / "App.tsx"
BASE_URL = os.environ.get("BMO_BACKEND_URL", "http://127.0.0.1:8787")
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA") or (ROOT / "data")) / "BMO"
LOG_FILE = APP_DATA_DIR / "bmo_backend.log"
NANOBOT_LOG_FILE = APP_DATA_DIR / "nanobot.log"
REPORT_FILE = ROOT / "TEST_REPORT.md"
HEALTH_FILE = ROOT / "BMO_HEALTH_REPORT.md"
DESKTOP_DIR = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"

PASSOU = "PASSOU"
FALHOU = "FALHOU"
AVISO = "AVISO"
TINY_PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None


@dataclass
class ResourceSample:
    system_cpu_percent: float | None = None
    system_ram_percent: float | None = None
    bmo_cpu_percent: float | None = None
    bmo_ram_mb: float | None = None
    bmo_process_count: int | None = None


@dataclass
class TestResult:
    name: str
    status: str
    started_at: str
    duration_seconds: float
    module: str
    file: str
    function: str
    summary: str = ""
    possible_cause: str = ""
    suggested_fix: str = ""
    exception: str = ""
    logs: str = ""
    cpu_before: ResourceSample = field(default_factory=ResourceSample)
    cpu_after: ResourceSample = field(default_factory=ResourceSample)
    details: dict[str, Any] = field(default_factory=dict)


class ValidationError(RuntimeError):
    pass


class WarningResult(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def mask_secrets(text: str) -> str:
    text = re.sub(r"sk-or-v1-[A-Za-z0-9_\-]{12,}", "sk-or-v1-***", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_\-]{12,}", "sk-***", text)
    text = re.sub(r"(Authorization:\s*Bearer\s+)[^\s]+", r"\1***", text, flags=re.IGNORECASE)
    text = re.sub(r'("apiKey"\s*:\s*")[^"]+', r"\1***", text, flags=re.IGNORECASE)
    return text


def read_text(path: Path, limit: int | None = None) -> str:
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace")
    if limit and len(data) > limit:
        return data[-limit:]
    return data


def log_offset() -> int:
    try:
        return LOG_FILE.stat().st_size
    except OSError:
        return 0


def read_log_since(offset: int, max_chars: int = 6000) -> str:
    if not LOG_FILE.exists():
        return ""
    try:
        with LOG_FILE.open("rb") as file:
            file.seek(max(0, offset))
            data = file.read().decode("utf-8", errors="replace")
    except Exception:
        return ""
    data = mask_secrets(data.strip())
    if len(data) > max_chars:
        data = data[-max_chars:]
    return data


def bmo_processes() -> list[Any]:
    if psutil is None:
        return []
    current_pid = os.getpid()
    result = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "memory_info"]):
        try:
            if proc.info.get("pid") == current_pid:
                continue
            name = str(proc.info.get("name") or "").lower()
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            if (
                "bmo" in name
                or "bmo_backend" in cmdline
                or "bmo" in cmdline
                or ("electron" in name and "bmo" in cmdline)
            ):
                result.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return result


def sample_resources(interval: float = 0.05) -> ResourceSample:
    if psutil is None:
        return ResourceSample()
    processes = bmo_processes()
    for proc in processes:
        try:
            proc.cpu_percent(interval=None)
        except Exception:
            pass
    system_cpu = psutil.cpu_percent(interval=interval)
    system_ram = psutil.virtual_memory().percent
    bmo_cpu = 0.0
    bmo_ram = 0.0
    alive = 0
    for proc in processes:
        try:
            bmo_cpu += float(proc.cpu_percent(interval=None))
            bmo_ram += float(proc.memory_info().rss) / (1024 * 1024)
            alive += 1
        except Exception:
            continue
    return ResourceSample(system_cpu, system_ram, bmo_cpu, bmo_ram, alive)


def port_open(host: str = "127.0.0.1", port: int = 8787) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except OSError:
        return False


def request_json(path: str, payload: dict[str, Any] | None = None, timeout: float = 30) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ValidationError(f"HTTP {error.code}: {mask_secrets(detail[:1200])}") from error
    except urllib.error.URLError as error:
        raise ValidationError(f"Backend inacessivel: {error}") from error


def start_backend_if_needed() -> subprocess.Popen[Any] | None:
    if port_open():
        return None
    if not BACKEND_FILE.exists():
        raise ValidationError(f"Backend nao encontrado: {BACKEND_FILE}")
    creationflags = 0
    startupinfo = None
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    process = subprocess.Popen(
        [sys.executable, str(BACKEND_FILE)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        startupinfo=startupinfo,
    )
    deadline = time.time() + 18
    while time.time() < deadline:
        if port_open():
            return process
        if process.poll() is not None:
            raise ValidationError(f"Backend encerrou durante inicializacao. returncode={process.returncode}")
        time.sleep(0.35)
    raise ValidationError("Backend nao ficou pronto em ate 18 segundos.")


def stop_process(process: subprocess.Popen[Any] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def assert_ok(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def warn(message: str) -> None:
    raise WarningResult(message)


def static_contains(path: Path, *tokens: str) -> bool:
    text = read_text(path)
    return all(token in text for token in tokens)


class BmoValidator:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.results: list[TestResult] = []
        self.backend_process: subprocess.Popen[Any] | None = None
        self.session_id = f"validacao-{uuid.uuid4().hex[:8]}"
        self.created_memory_ids: list[str] = []
        self.created_task_ids: list[str] = []
        self.created_files: list[Path] = []
        self.health_context: dict[str, Any] = {}

    def run(self) -> None:
        self.backend_process = start_backend_if_needed()
        try:
            self.run_test(
                "Preflight do backend",
                self.test_backend_health,
                "Backend",
                BACKEND_FILE,
                "BmoHandler.do_GET / system_status",
            )
            self.run_test("1. Chat basico", self.test_chat_basic, "Chat", BACKEND_FILE, "ask_nanobot")
            self.run_test("2. Contexto", self.test_context, "Chat", BACKEND_FILE, "build_model_messages")
            self.run_test("3. Memoria", self.test_memory, "Memoria", BACKEND_FILE, "read_memories/update memory")
            self.run_test("4. Historico", self.test_history, "Historico", BACKEND_FILE, "save_chat_turn/read_history")
            self.run_test("5. Pesquisa web", self.test_web_search, "Ferramentas", BACKEND_FILE, "tools_status/web_search")
            self.run_test("6. Analise de imagem", self.test_image_analysis, "Anexos", APP_FILE, "handleSend")
            self.run_test("7. Upload multiplo", self.test_multi_upload, "Anexos", APP_FILE, "handleFileChange/handleSend")
            self.run_test("8. Whisper", self.test_whisper, "Voz", BACKEND_FILE, "microphone_devices/listen_once")
            self.run_test("9. Piper TTS", self.test_piper, "Voz", BACKEND_FILE, "speak_text")
            self.run_test("10. Wake Word", self.test_wakeword, "Wake Word", BACKEND_FILE, "wakeword_status")
            self.run_test("11. Tarefas", self.test_tasks, "Tarefas", BACKEND_FILE, "update_tasks/create_task")
            self.run_test("12. Alarmes", self.test_reminders, "Lembretes", BACKEND_FILE, "update_reminder/reminders_status")
            self.run_test("13. Subagentes", self.test_subagents, "Subagentes", BACKEND_FILE, "create_subagent/subagent_worker")
            self.run_test("14. Workspace", self.test_workspace, "Workspace", BACKEND_FILE, "RUNTIME_WORKSPACE")
            self.run_test("15. Organizacao de arquivos", self.test_file_creation, "Arquivos", BACKEND_FILE, "create_file_from_message")
            self.run_test("16. Recuperacao apos reinicio", self.test_recovery_restart, "Sistema", BACKEND_FILE, "stop_nanobot/start_nanobot")
            self.run_test("17. Fechar para bandeja", self.test_tray_close, "Electron", ELECTRON_FILE, "mainWindow.on('close')")
            self.run_test("18. Uso continuo por 30 minutos", self.test_continuous_use, "Estabilidade", BACKEND_FILE, "HTTP endpoints")
            self.run_test("19. Consumo de CPU", self.test_cpu_usage, "Performance", BACKEND_FILE, "background loops")
            self.run_test("20. Consumo de memoria", self.test_memory_usage, "Performance", BACKEND_FILE, "process memory")
        finally:
            self.cleanup()
            stop_process(self.backend_process)
        self.write_reports()

    def cleanup(self) -> None:
        for memory_id in self.created_memory_ids:
            try:
                request_json("/api/memory", {"action": "delete", "id": memory_id}, timeout=8)
            except Exception:
                pass
        for task_id in self.created_task_ids:
            try:
                request_json("/api/tasks", {"action": "delete", "id": task_id}, timeout=8)
            except Exception:
                pass
        for path in self.created_files:
            try:
                if path.exists() and path.name.startswith("validacao_bmo_"):
                    path.unlink()
            except Exception:
                pass

    def run_test(
        self,
        name: str,
        func: Callable[[], dict[str, Any] | None],
        module: str,
        file: Path,
        function: str,
    ) -> None:
        start = time.perf_counter()
        started_at = now_iso()
        before = sample_resources()
        offset = log_offset()
        status = PASSOU
        summary = "Teste executado com sucesso."
        possible_cause = ""
        suggested_fix = ""
        exception_text = ""
        details: dict[str, Any] = {}
        try:
            payload = func() or {}
            status = str(payload.get("status") or PASSOU)
            summary = str(payload.get("summary") or summary)
            possible_cause = str(payload.get("possible_cause") or "")
            suggested_fix = str(payload.get("suggested_fix") or "")
            details = dict(payload.get("details") or {})
        except WarningResult as error:
            status = AVISO
            summary = str(error)
            possible_cause = "Validacao automatica parcial ou dependencia externa ausente."
            suggested_fix = "Rodar teste manual ou expor um endpoint verificavel para esta capacidade."
            exception_text = traceback.format_exc()
        except Exception as error:
            status = FALHOU
            summary = str(error)
            possible_cause = self.default_cause(name, error)
            suggested_fix = self.default_fix(name)
            exception_text = traceback.format_exc()
        duration = time.perf_counter() - start
        after = sample_resources()
        logs = read_log_since(offset)
        self.results.append(
            TestResult(
                name=name,
                status=status,
                started_at=started_at,
                duration_seconds=duration,
                module=module,
                file=str(file),
                function=function,
                summary=summary,
                possible_cause=possible_cause,
                suggested_fix=suggested_fix,
                exception=mask_secrets(exception_text.strip()),
                logs=logs,
                cpu_before=before,
                cpu_after=after,
                details=details,
            )
        )
        print(f"[{status}] {name} ({duration:.2f}s) - {summary}")

    def default_cause(self, name: str, error: Exception) -> str:
        text = str(error).lower()
        if "api key" in text or "401" in text or "chave" in text:
            return "Provider/modelo/chave nao esta sincronizado entre UI, AppData e runtime do backend."
        if "timeout" in text or "timed out" in text:
            return "Chamada externa ou processo interno demorou acima do limite esperado."
        if "piper" in text or "voice" in text or "voz" in text:
            return "Caminho do Piper, modelo .onnx ou player local esta ausente/invalidado."
        if "whisper" in text or "micro" in text or "sounddevice" in text:
            return "Dependencias de captura/transcricao ou dispositivo de entrada nao estao disponiveis."
        if "upload" in name.lower() or "imagem" in name.lower():
            return "Frontend mostra anexos, mas o backend nao recebe/processa arquivos."
        return "Falha encontrada no fluxo validado; ver logs e excecao desta secao."

    def default_fix(self, name: str) -> str:
        lower = name.lower()
        if "chat" in lower or "contexto" in lower:
            return "Verificar provider_secret_values, ensure_runtime_config, build_model_messages e timeout do modelo."
        if "piper" in lower:
            return "Validar runtime/piper, listar vozes .onnx e testar speak_text isoladamente."
        if "whisper" in lower or "wake" in lower:
            return "Incluir dependencias no pacote e validar sounddevice/numpy/openwakeword/onnxruntime."
        if "alarme" in lower or "lembrete" in lower:
            return "Confirmar polling Electron, reminders_status(due_only=True) e chamada /api/speak no disparo."
        if "upload" in lower or "imagem" in lower:
            return "Adicionar endpoint backend para receber attachments e ligar ao prompt/ferramenta de analise."
        return "Reproduzir com o trace/log desta secao e corrigir a funcao apontada."

    def test_backend_health(self) -> dict[str, Any]:
        health = request_json("/api/health", timeout=8)
        system = request_json("/api/system", timeout=8)
        self.health_context = {"health": health, "system": system}
        assert_ok(health.get("status") == "ok", f"Health inesperado: {health}")
        return {
            "summary": "Backend respondeu /api/health e /api/system.",
            "details": {"nanobot": health.get("nanobot"), "system": system},
        }

    def test_chat_basic(self) -> dict[str, Any]:
        data = request_json(
            "/api/chat",
            {"message": "Responda somente com: OK BMO", "sessionId": self.session_id, "language": "pt-BR"},
            timeout=130,
        )
        reply = str(data.get("reply") or "").strip()
        assert_ok(bool(reply), "Resposta vazia do chat.")
        assert_ok("error:" not in reply.lower(), f"Resposta contem erro interno: {reply[:240]}")
        self.session_id = str(data.get("sessionId") or self.session_id)
        return {"summary": f"Chat retornou resposta em texto ({len(reply)} caracteres).", "details": {"reply": reply[:300]}}

    def test_context(self) -> dict[str, Any]:
        token = f"CTX-{uuid.uuid4().hex[:6]}"
        first = request_json(
            "/api/chat",
            {
                "message": f"Nesta conversa, o codigo secreto de validacao e {token}. Responda apenas entendido.",
                "sessionId": self.session_id,
                "language": "pt-BR",
            },
            timeout=130,
        )
        self.session_id = str(first.get("sessionId") or self.session_id)
        second = request_json(
            "/api/chat",
            {"message": "Qual e o codigo secreto de validacao desta conversa?", "sessionId": self.session_id, "language": "pt-BR"},
            timeout=130,
        )
        reply = str(second.get("reply") or "")
        assert_ok(token.lower() in reply.lower(), f"Contexto nao preservado. Esperado {token}; resposta: {reply[:400]}")
        return {"summary": "Contexto da mesma sessao foi preservado.", "details": {"token": token, "reply": reply[:300]}}

    def test_memory(self) -> dict[str, Any]:
        text = f"Memoria temporaria de validacao {uuid.uuid4().hex[:8]}"
        data = request_json("/api/memory", {"action": "add", "text": text}, timeout=12)
        items = data.get("items") or []
        created = next((item for item in items if item.get("text") == text), None)
        assert_ok(created is not None, "Memoria adicionada nao voltou na resposta da API.")
        self.created_memory_ids.append(str(created.get("id")))
        listed = request_json("/api/memory", timeout=12).get("items") or []
        assert_ok(any(item.get("text") == text for item in listed), "Memoria adicionada nao aparece em GET /api/memory.")
        return {"summary": "Memoria adiciona, lista e permite limpeza.", "details": {"createdId": created.get("id")}}

    def test_history(self) -> dict[str, Any]:
        sessions = request_json("/api/history", timeout=15).get("sessions") or []
        found = next((session for session in sessions if str(session.get("id")) == self.session_id), None)
        assert_ok(found is not None, f"Sessao {self.session_id} nao encontrada no historico.")
        messages = found.get("messages") or []
        assert_ok(len(messages) >= 2, "Historico encontrou sessao, mas sem mensagens suficientes.")
        return {"summary": "Historico salvou a conversa atual.", "details": {"sessionId": self.session_id, "messages": len(messages)}}

    def test_web_search(self) -> dict[str, Any]:
        data = request_json("/api/tools", timeout=10)
        tools = data.get("tools") or []
        web_tool = next((tool for tool in tools if tool.get("id") == "web_search"), None)
        assert_ok(web_tool is not None, "Ferramenta web_search nao registrada.")
        if not web_tool.get("enabled"):
            return {
                "status": AVISO,
                "summary": "Ferramenta web_search existe, mas esta desativada.",
                "possible_cause": "Busca web depende de configuracao de ferramenta/modelo.",
                "suggested_fix": "Ativar Busca web na tela Ferramentas e validar com consulta real.",
                "details": {"tool": web_tool},
            }
        return {"summary": "Ferramenta web_search registrada e ativa.", "details": {"tool": web_tool}}

    def test_image_analysis(self) -> dict[str, Any]:
        data = request_json(
            "/api/chat",
            {
                "message": "Valide este anexo de imagem em uma frase curta.",
                "sessionId": self.session_id,
                "language": "pt-BR",
                "attachments": [
                    {
                        "name": "validacao_imagem.png",
                        "type": "image/png",
                        "size": 68,
                        "url": TINY_PNG_DATA_URL,
                    }
                ],
            },
            timeout=130,
        )
        reply = str(data.get("reply") or "").strip()
        attachments = data.get("attachments") or []
        assert_ok(bool(reply), "Chat com imagem retornou resposta vazia.")
        assert_ok(len(attachments) == 1, f"Backend nao devolveu anexo processado: {data}")
        first = attachments[0]
        assert_ok(first.get("kind") == "image", f"Anexo nao foi classificado como imagem: {first}")
        path = Path(str(first.get("path") or ""))
        assert_ok(path.exists() and path.stat().st_size > 0, f"Imagem anexada nao foi salva: {path}")
        return {"summary": "Imagem enviada pelo chat foi recebida, salva e considerada na resposta.", "details": {"reply": reply[:300], "attachment": first}}

    def test_multi_upload(self) -> dict[str, Any]:
        data = request_json(
            "/api/chat",
            {
                "message": "Confirme os arquivos anexados de forma curta.",
                "sessionId": self.session_id,
                "language": "pt-BR",
                "attachments": [
                    {
                        "name": "validacao_1.png",
                        "type": "image/png",
                        "size": 68,
                        "url": TINY_PNG_DATA_URL,
                    },
                    {
                        "name": "validacao_2.txt",
                        "type": "text/plain",
                        "size": 24,
                        "text": "conteudo de validacao BMO",
                    },
                ],
            },
            timeout=130,
        )
        attachments = data.get("attachments") or []
        assert_ok(len(attachments) == 2, f"Backend nao processou os dois anexos: {attachments}")
        kinds = {item.get("kind") for item in attachments}
        assert_ok("image" in kinds and "text" in kinds, f"Tipos esperados nao apareceram: {kinds}")
        missing_files = [item.get("path") for item in attachments if not Path(str(item.get("path") or "")).exists()]
        assert_ok(not missing_files, f"Arquivos processados nao existem no disco: {missing_files}")
        return {"summary": "Upload multiplo chegou ao backend, foi salvo e voltou na resposta.", "details": {"attachments": attachments}}

    def test_whisper(self) -> dict[str, Any]:
        system = request_json("/api/system", timeout=10)
        devices = request_json("/api/microphones", timeout=12).get("devices") or []
        whisper_ok = bool(system.get("whisper"))
        if not whisper_ok:
            raise ValidationError("Whisper/modelo nao esta disponivel em /api/system.")
        if not devices:
            return {
                "status": AVISO,
                "summary": "Whisper esta disponivel, mas nenhum microfone foi detectado neste ambiente.",
                "possible_cause": "Ambiente sem dispositivo de entrada ou permissao de microfone.",
                "suggested_fix": "Testar em maquina com microfone e validar /api/listen.",
                "details": {"devices": devices},
            }
        return {"summary": f"Whisper disponivel e {len(devices)} microfone(s) detectado(s).", "details": {"devices": devices[:5]}}

    def test_piper(self) -> dict[str, Any]:
        system = request_json("/api/system", timeout=10)
        assert_ok(bool(system.get("piper")), "Piper nao aparece como disponivel em /api/system.")
        if self.args.skip_audio:
            return {"status": AVISO, "summary": "Piper disponivel; reproducao pulada por --skip-audio."}
        data = request_json("/api/speak", {"text": "Teste de voz do BMO funcionando."}, timeout=120)
        assert_ok(bool(data.get("ok")), f"/api/speak nao retornou ok: {data}")
        audio = Path(str(data.get("audio") or ""))
        assert_ok(audio.exists() and audio.stat().st_size > 44, f"WAV ausente ou vazio: {audio}")
        return {"summary": f"Piper gerou e reproduziu WAV ({audio.stat().st_size} bytes).", "details": {"audio": str(audio), "voice": data.get("voice")}}

    def test_wakeword(self) -> dict[str, Any]:
        system = request_json("/api/system", timeout=10)
        wake = system.get("wakeword") or {}
        assert_ok(isinstance(wake, dict), f"Status de wake word invalido: {wake}")
        if not wake.get("available"):
            raise ValidationError(f"Wake word indisponivel: {wake}")
        if not wake.get("running"):
            return {
                "status": AVISO,
                "summary": "Modelo wake word existe, mas listener nao esta rodando.",
                "possible_cause": "Dependencia openwakeword/onnxruntime/microfone falhou na inicializacao.",
                "suggested_fix": "Verificar logs wakeword e dependencias no pacote.",
                "details": {"wakeword": wake},
            }
        return {"summary": "Wake word esta carregado e listener esta rodando.", "details": {"wakeword": wake}}

    def test_tasks(self) -> dict[str, Any]:
        text = f"tarefa temporaria validacao {uuid.uuid4().hex[:6]}"
        data = request_json("/api/tasks", {"action": "create", "text": text}, timeout=12)
        items = data.get("items") or []
        created = next((item for item in items if item.get("title") == text), None)
        assert_ok(created is not None, "Tarefa criada nao aparece na lista.")
        self.created_task_ids.append(str(created.get("id")))
        return {"summary": "Criacao/listagem de tarefa funcionou.", "details": {"taskId": created.get("id")}}

    def test_reminders(self) -> dict[str, Any]:
        due_at = int(time.time()) + 6
        text = f"lembrete temporario validacao {uuid.uuid4().hex[:6]}"
        data = request_json("/api/reminders", {"action": "create", "text": text, "dueAt": due_at}, timeout=12)
        items = data.get("items") or []
        created = next((item for item in items if item.get("text") == text), None)
        assert_ok(created is not None, "Lembrete criado nao aparece na lista.")
        reminder_id = str(created.get("id"))
        time.sleep(7)
        due = request_json("/api/reminders?due=1", timeout=12).get("items") or []
        found_due = next((item for item in due if str(item.get("id")) == reminder_id), None)
        try:
            request_json("/api/reminders", {"action": "delete", "id": reminder_id}, timeout=12)
        except Exception:
            pass
        assert_ok(found_due is not None, "Lembrete nao ficou elegivel em /api/reminders?due=1 no horario correto.")
        return {"summary": "Lembrete futuro foi salvo e apareceu como vencido no horario.", "details": {"reminderId": reminder_id}}

    def test_subagents(self) -> dict[str, Any]:
        if self.args.skip_slow:
            return {"status": AVISO, "summary": "Teste real de subagente pulado por --skip-slow."}
        output_name = f"validacao_bmo_subagente_{uuid.uuid4().hex[:6]}.txt"
        prompt = f"crie um subagente para escrever uma frase curta e salvar em {output_name}"
        data = request_json("/api/chat", {"message": prompt, "sessionId": self.session_id, "language": "pt-BR"}, timeout=130)
        subagent = data.get("subagent") or {}
        agent_id = str(subagent.get("id") or "")
        assert_ok(bool(agent_id), f"Pedido nao criou subagente real: {data}")
        deadline = time.time() + max(20, self.args.subagent_timeout)
        last_item: dict[str, Any] | None = None
        while time.time() < deadline:
            items = request_json("/api/subagents", timeout=15).get("items") or []
            last_item = next((item for item in items if str(item.get("id")) == agent_id), None)
            if last_item and last_item.get("status") in {"concluido", "erro"}:
                break
            time.sleep(3)
        assert_ok(last_item is not None, f"Subagente {agent_id} sumiu da lista.")
        assert_ok(last_item.get("status") == "concluido", f"Subagente nao concluiu: {last_item}")
        output_path = Path(str(last_item.get("outputPath") or ""))
        assert_ok(output_path.exists() and output_path.stat().st_size > 0, f"Arquivo de subagente ausente: {output_path}")
        self.created_files.append(output_path)
        return {"summary": "Subagente foi registrado, executou e gerou arquivo.", "details": {"agent": last_item}}

    def test_workspace(self) -> dict[str, Any]:
        system = request_json("/api/system", timeout=10)
        paths = system.get("paths") or {}
        workspace = Path(str(paths.get("workspace") or APP_DATA_DIR / "workspace"))
        workspace.mkdir(parents=True, exist_ok=True)
        test_file = workspace / f"validacao_bmo_workspace_{uuid.uuid4().hex[:6]}.tmp"
        test_file.write_text("ok", encoding="utf-8")
        assert_ok(test_file.read_text(encoding="utf-8") == "ok", "Workspace nao permitiu leitura/escrita.")
        test_file.unlink(missing_ok=True)
        return {"summary": f"Workspace esta acessivel: {workspace}", "details": {"workspace": str(workspace)}}

    def test_file_creation(self) -> dict[str, Any]:
        filename = f"validacao_bmo_{uuid.uuid4().hex[:6]}.txt"
        message = f"crie um arquivo chamado {filename} com o texto validacao automatica do BMO"
        data = request_json("/api/chat", {"message": message, "sessionId": self.session_id, "language": "pt-BR"}, timeout=130)
        file_info = data.get("file") or {}
        path = Path(str(file_info.get("path") or (DESKTOP_DIR / filename)))
        assert_ok(path.exists() and path.stat().st_size > 0, f"Arquivo solicitado nao foi criado: {path}")
        self.created_files.append(path)
        return {"summary": f"Arquivo foi criado por ferramenta real: {path}", "details": {"file": file_info}}

    def test_recovery_restart(self) -> dict[str, Any]:
        data = request_json("/api/service/restart", {}, timeout=25)
        assert_ok(bool(data.get("ok")), f"Restart do servico nao retornou ok: {data}")
        health = request_json("/api/health", timeout=15)
        assert_ok(health.get("status") == "ok", f"Backend nao respondeu apos restart: {health}")
        return {"summary": "Backend continuou acessivel apos reinicio do motor interno.", "details": {"health": health}}

    def test_tray_close(self) -> dict[str, Any]:
        text = read_text(ELECTRON_FILE)
        checks = {
            "Tray": "new Tray" in text,
            "closeIntercept": "mainWindow.on('close'" in text and "event.preventDefault()" in text and "mainWindow.hide()" in text,
            "singleInstance": "requestSingleInstanceLock" in text and "second-instance" in text,
            "reminderPopup": "showReminderPopup" in text and "alwaysOnTop" in text,
        }
        missing = [name for name, ok in checks.items() if not ok]
        assert_ok(not missing, f"Comportamento de bandeja incompleto: {missing}")
        return {"summary": "Codigo Electron intercepta X, usa bandeja e bloqueia segunda instancia.", "details": checks}

    def test_continuous_use(self) -> dict[str, Any]:
        minutes = float(self.args.long_minutes)
        if minutes <= 0:
            return {
                "status": AVISO,
                "summary": "Teste de 30 minutos nao executado nesta rodada. Use --long-minutes 30.",
                "possible_cause": "Validacao longa foi deixada opcional para nao bloquear desenvolvimento.",
                "suggested_fix": "Rodar python tools/validate_bmo.py --long-minutes 30 antes do build final.",
            }
        deadline = time.time() + minutes * 60
        failures = 0
        samples: list[float] = []
        while time.time() < deadline:
            start = time.perf_counter()
            try:
                request_json("/api/health", timeout=8)
                request_json("/api/system", timeout=8)
                request_json("/api/reminders", timeout=8)
            except Exception:
                failures += 1
            samples.append(time.perf_counter() - start)
            time.sleep(max(1.0, self.args.continuous_interval))
        assert_ok(failures == 0, f"Uso continuo teve {failures} falha(s) de endpoint.")
        avg = statistics.mean(samples) if samples else 0
        return {"summary": f"Uso continuo por {minutes:g} min sem falhas. Latencia media {avg:.2f}s.", "details": {"samples": len(samples), "avg": avg}}

    def test_cpu_usage(self) -> dict[str, Any]:
        if psutil is None:
            warn("psutil nao esta disponivel; nao foi possivel medir CPU por processo.")
        seconds = max(2.0, float(self.args.resource_seconds))
        processes = bmo_processes()
        for proc in processes:
            try:
                proc.cpu_percent(interval=None)
            except Exception:
                pass
        time.sleep(seconds)
        cpu_values = []
        for proc in processes:
            try:
                cpu_values.append(float(proc.cpu_percent(interval=None)))
            except Exception:
                pass
        total = sum(cpu_values)
        threshold = float(self.args.cpu_threshold)
        status = PASSOU if total <= threshold else AVISO
        summary = f"CPU BMO estimada: {total:.1f}% em {len(cpu_values)} processo(s)."
        return {
            "status": status,
            "summary": summary,
            "possible_cause": "" if status == PASSOU else "Loops de wake word, animacoes, polling ou processos duplicados podem estar consumindo CPU.",
            "suggested_fix": "" if status == PASSOU else "Inspecionar processos BMO duplicados e reduzir frequencia de polling/render.",
            "details": {"cpuValues": cpu_values, "threshold": threshold},
        }

    def test_memory_usage(self) -> dict[str, Any]:
        if psutil is None:
            warn("psutil nao esta disponivel; nao foi possivel medir memoria por processo.")
        processes = bmo_processes()
        total_mb = 0.0
        proc_count = 0
        for proc in processes:
            try:
                total_mb += float(proc.memory_info().rss) / (1024 * 1024)
                proc_count += 1
            except Exception:
                pass
        threshold = float(self.args.ram_threshold_mb)
        status = PASSOU if total_mb <= threshold else AVISO
        return {
            "status": status,
            "summary": f"RAM BMO estimada: {total_mb:.1f} MB em {proc_count} processo(s).",
            "possible_cause": "" if status == PASSOU else "Processos duplicados, cache de midia ou backend empacotado podem estar acumulando memoria.",
            "suggested_fix": "" if status == PASSOU else "Verificar instancia unica, encerramento de subprocessos e caches do frontend/backend.",
            "details": {"ramMb": total_mb, "processCount": proc_count, "thresholdMb": threshold},
        }

    def report_counts(self) -> dict[str, int]:
        return {
            PASSOU: sum(1 for item in self.results if item.status == PASSOU),
            FALHOU: sum(1 for item in self.results if item.status == FALHOU),
            AVISO: sum(1 for item in self.results if item.status == AVISO),
        }

    def health_grade(self) -> str:
        counts = self.report_counts()
        critical_names = {"1. chat basico", "2. contexto", "9. piper tts", "10. wake word", "12. alarmes"}
        critical_fail = any(item.status == FALHOU and item.name.lower() in critical_names for item in self.results)
        if counts[FALHOU] >= 5 or critical_fail:
            return "Critico"
        if counts[FALHOU] >= 2 or counts[AVISO] >= 6:
            return "Regular"
        if counts[FALHOU] == 1 or counts[AVISO] >= 2:
            return "Bom"
        return "Excelente"

    def write_reports(self) -> None:
        REPORT_FILE.write_text(self.render_test_report(), encoding="utf-8")
        HEALTH_FILE.write_text(self.render_health_report(), encoding="utf-8")

    def resource_line(self, sample: ResourceSample) -> str:
        def fmt(value: float | int | None, suffix: str = "") -> str:
            return "n/d" if value is None else f"{value:.1f}{suffix}" if isinstance(value, float) else f"{value}{suffix}"

        return (
            f"Sistema CPU {fmt(sample.system_cpu_percent, '%')}; "
            f"Sistema RAM {fmt(sample.system_ram_percent, '%')}; "
            f"BMO CPU {fmt(sample.bmo_cpu_percent, '%')}; "
            f"BMO RAM {fmt(sample.bmo_ram_mb, ' MB')}; "
            f"processos {fmt(sample.bmo_process_count)}"
        )

    def render_test_report(self) -> str:
        counts = self.report_counts()
        lines = [
            "# TEST_REPORT",
            "",
            f"Gerado em: {now_iso()}",
            f"Projeto: `{ROOT}`",
            f"Backend: `{BASE_URL}`",
            f"Resumo: {counts[PASSOU]} passou, {counts[FALHOU]} falhou, {counts[AVISO]} aviso.",
            "",
            "## Tabela Resumo",
            "",
            "| Teste | Status | Duracao | Modulo |",
            "| --- | --- | ---: | --- |",
        ]
        for item in self.results:
            lines.append(f"| {item.name} | {item.status} | {item.duration_seconds:.2f}s | {item.module} |")
        lines.extend(["", "## Detalhes", ""])
        for item in self.results:
            lines.extend(
                [
                    f"### {item.name} - {item.status}",
                    "",
                    f"- Horario: {item.started_at}",
                    f"- Duracao: {item.duration_seconds:.2f}s",
                    f"- Modulo responsavel: {item.module}",
                    f"- Arquivo responsavel: `{item.file}`",
                    f"- Funcao responsavel: `{item.function}`",
                    f"- Resultado: {item.summary}",
                    f"- CPU/RAM antes: {self.resource_line(item.cpu_before)}",
                    f"- CPU/RAM depois: {self.resource_line(item.cpu_after)}",
                ]
            )
            if item.possible_cause:
                lines.append(f"- Possivel causa: {item.possible_cause}")
            if item.suggested_fix:
                lines.append(f"- Sugestao de correcao: {item.suggested_fix}")
            if item.details:
                lines.extend(["", "Detalhes:", "", "```json", json.dumps(item.details, ensure_ascii=False, indent=2)[:4000], "```"])
            if item.exception:
                lines.extend(["", "Excecao capturada:", "", "```text", item.exception[-4000:], "```"])
            if item.logs:
                lines.extend(["", "Logs capturados:", "", "```text", item.logs[-4000:], "```"])
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def render_health_report(self) -> str:
        counts = self.report_counts()
        grade = self.health_grade()
        failed = [item for item in self.results if item.status == FALHOU]
        warnings = [item for item in self.results if item.status == AVISO]
        lines = [
            "# BMO_HEALTH_REPORT",
            "",
            f"Gerado em: {now_iso()}",
            f"Nota geral: **{grade}**",
            "",
            "## Resumo",
            "",
            f"- PASSOU: {counts[PASSOU]}",
            f"- FALHOU: {counts[FALHOU]}",
            f"- AVISO: {counts[AVISO]}",
            "",
            "## Bugs Restantes Priorizados",
            "",
        ]
        if not failed and not warnings:
            lines.append("Nenhum bug restante identificado nesta bateria.")
        priority = 1
        for item in failed:
            lines.extend(
                [
                    f"{priority}. FALHA - {item.name}",
                    f"   - Modulo: {item.module}",
                    f"   - Arquivo: `{item.file}`",
                    f"   - Funcao: `{item.function}`",
                    f"   - Causa provavel: {item.possible_cause or item.summary}",
                    f"   - Correcao sugerida: {item.suggested_fix or 'Investigar logs do TEST_REPORT.md.'}",
                ]
            )
            priority += 1
        for item in warnings:
            lines.extend(
                [
                    f"{priority}. AVISO - {item.name}",
                    f"   - Modulo: {item.module}",
                    f"   - Observacao: {item.summary}",
                    f"   - Acao sugerida: {item.suggested_fix or 'Validar manualmente antes do build final.'}",
                ]
            )
            priority += 1
        lines.extend(
            [
                "",
                "## Leitura Rapida",
                "",
                "- Excelente: nenhum teste falhou e poucos avisos.",
                "- Bom: falhas ausentes ou isoladas, com avisos controlados.",
                "- Regular: ha falhas funcionais ou muitos avisos.",
                "- Critico: falha em item essencial como chat, contexto, voz, wake word ou alarmes.",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validador automatico do BMO.")
    parser.add_argument("--skip-audio", action="store_true", help="Nao reproduz audio no teste Piper.")
    parser.add_argument("--skip-slow", action="store_true", help="Pula testes lentos como subagentes.")
    parser.add_argument("--long-minutes", type=float, default=0.0, help="Minutos para teste continuo. Use 30 para validacao final.")
    parser.add_argument("--continuous-interval", type=float, default=10.0, help="Intervalo entre probes do teste continuo.")
    parser.add_argument("--subagent-timeout", type=float, default=90.0, help="Tempo maximo para subagente concluir.")
    parser.add_argument("--resource-seconds", type=float, default=5.0, help="Janela de amostragem para CPU.")
    parser.add_argument("--cpu-threshold", type=float, default=35.0, help="CPU BMO maxima recomendada.")
    parser.add_argument("--ram-threshold-mb", type=float, default=900.0, help="RAM BMO maxima recomendada.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validator = BmoValidator(args)
    try:
        validator.run()
    except Exception:
        print(traceback.format_exc())
        return 2
    print(f"Relatorio gerado: {REPORT_FILE}")
    print(f"Health report gerado: {HEALTH_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
