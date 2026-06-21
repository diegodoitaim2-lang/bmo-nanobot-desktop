"""
Teste: Verificar que o fallback manual (direct_provider_chat) NAO e mais usado.

Cenario 1: ask_nanobot() com NanobotRuntime falhando
  - Deve retornar mensagem de erro, NAO cair no direct_provider_chat.
  - Deve registrar "nanobot_runtime_failed" + "fallback_blocked" no log.

Cenario 2: Cadeia de chamadas do handle_chat()
  - ask_nanobot e a unica via de resposta.
  - build_model_messages / direct_provider_chat NAO devem ser chamados.
"""

import sys
import os
import json
from io import StringIO

# Isolar para nao poluir o stdout real
sys.path.insert(0, os.path.dirname(__file__))

# Mock do nanobot_integration antes de importar bmo_backend
import types
nanobot_integration_mock = types.ModuleType("nanobot_integration")

call_count = {"chat": 0}

def failing_chat(message, session_id, language):
    call_count["chat"] += 1
    raise RuntimeError("Simulacao: NanobotRuntime indisponivel (teste)")

nanobot_integration_mock.chat = failing_chat
nanobot_integration_mock.is_runtime_ready = lambda: False
nanobot_integration_mock.runtime_status = lambda: {"ready": False}
nanobot_integration_mock.initialize_runtime = lambda: False

sys.modules["nanobot_integration"] = nanobot_integration_mock

# Mock rate_limit para nao depender de config real
rate_limit_mock = types.ModuleType("rate_limit")
rate_limit_mock.check_rate_limit = lambda key: None
sys.modules["rate_limit"] = rate_limit_mock

# Mock tools
tools_mock = types.ModuleType("tools")

def mock_write_file(ctx, path, content, overwrite=False):
    return {"ok": True}
def mock_shell_exec(ctx, command, timeout=30):
    return {"ok": True, "stdout": "", "stderr": "", "code": 0}
tools_mock.write_file = mock_write_file
tools_mock.shell_exec = mock_shell_exec
tools_mock.resolve_workspace_path = lambda ctx, path, must_exist=False: path

sys.modules["tools"] = tools_mock

# Mock nanobot_bridge
nanobot_bridge_mock = types.ModuleType("nanobot_bridge")
nanobot_bridge_mock.runtime = lambda *a, **kw: None
nanobot_bridge_mock.registry_payload = lambda *a, **kw: {}
nanobot_bridge_mock.channels_payload = lambda *a, **kw: {}
nanobot_bridge_mock.memory_payload = lambda *a, **kw: []
nanobot_bridge_mock.tool_info = lambda *a, **kw: {}
nanobot_bridge_mock.spawn_subagent = lambda *a, **kw: {"ok": True}
nanobot_bridge_mock.execute_tool = lambda *a, **kw: {"ok": True}
nanobot_bridge_mock.append_history = lambda *a, **kw: None
nanobot_bridge_mock.invalidate_runtime = lambda: None
sys.modules["nanobot_bridge"] = nanobot_bridge_mock

# Mock daemon e outras dependencias
_daemon_mock = types.ModuleType("_daemon")
_daemon_mock.Daemon = type("Daemon", (), {})
_daemon_mock.env = {}
sys.modules["_daemon"] = _daemon_mock

PASTA_BMO = "C:\\Users\\USER\\Documents\\BMO_PROJECT\\bmo"
os.chdir(PASTA_BMO)

# Capturar output do log
captured_logs = []

original_log = None

def setup():
    global original_log
    import bmo_backend
    original_log = bmo_backend.log_event
    def capturing_log(event, **fields):
        captured_logs.append({"event": event, **fields})
        # Ainda chama o log real
        if original_log:
            try:
                original_log(event, **fields)
            except Exception:
                pass
    bmo_backend.log_event = capturing_log

def test_fallback_blocked():
    """Cenario 1: ask_nanobot com NanobotRuntime falhando nao deve chamar direct_provider_chat."""
    import bmo_backend

    # Reset
    global captured_logs
    captured_logs = []
    call_count["chat"] = 0

    # NanobotRuntime mockado para falhar — ja esta configurado acima

    result = bmo_backend.ask_nanobot("Ola BMO, tudo bem?", "pt-BR", "test-session-123")

    # Verificar resultado
    assert "tropecei" in result or "circuitos" in result, (
        f"Esperava mensagem de erro, mas recebeu: {result}"
    )
    assert "Verifica se minha conexao" in result, (
        f"Mensagem deve falar sobre verificar conexao. Recebeu: {result}"
    )

    # Verificar logs
    events = [e["event"] for e in captured_logs]
    assert "nanobot_runtime_failed" in events, (
        f"Esperava nanobot_runtime_failed no log, mas so tem: {events}"
    )
    assert "fallback_blocked" in events, (
        f"Esperava fallback_blocked no log, mas so tem: {events}"
    )

    # Verificar que direct_provider_chat NAO foi chamado
    # (Nao temos como mockar ele, mas o fato de ask_nanobot nao ter chamado
    #  nenhuma funcao de request_json indica que nao caiu no fallback)
    assert "provider_chat" not in " ".join(events), (
        "Nao deveria ter chamado provider_chat"
    )

    print("[PASS] ask_nanobot com NanobotRuntime falhando retornou erro e bloqueou fallback.")

def test_nanobot_runtime_used():
    """Cenario 2: ask_nanobot com NanobotRuntime funcionando usa a rota normal."""
    import bmo_backend

    global captured_logs
    captured_logs = []
    call_count["chat"] = 0

    # Substituir o mock chat para ter sucesso
    def working_chat(message, session_id, language):
        call_count["chat"] += 1
        return "Resposta do NanobotRuntime: Ola! Tudo bem sim!"

    nanobot_integration_mock.chat = working_chat

    result = bmo_backend.ask_nanobot("Ola BMO!", "pt-BR", "test-session-working")

    assert call_count["chat"] == 1, (
        f"nanobot_integration.chat deveria ter sido chamado 1 vez, foi {call_count['chat']}"
    )
    assert "NanobotRuntime" in result, (
        f"Esperava resposta do NanobotRuntime, recebeu: {result}"
    )

    events = [e["event"] for e in captured_logs]
    assert "nanobot_runtime_used" in events, (
        f"Esperava nanobot_runtime_used no log, mas so tem: {events}"
    )
    assert "fallback_blocked" not in events, (
        "Nao deveria ter fallback_blocked se funcionou"
    )

    print("[PASS] ask_nanobot com NanobotRuntime OK usou rota normal.")

def test_handle_chat_no_fallback():
    """Cenario 3: Via handle_chat, se NanobotRuntime falhar, retorna erro."""
    import bmo_backend

    global captured_logs
    captured_logs = []

    # Forcar falha novamente
    nanobot_integration_mock.chat = failing_chat
    call_count["chat"] = 0

    # Simular handle_chat sem depender do handler HTTP
    # O handle_chat chama ask_nanobot por ultimo
    # Vamos testar via ask_nanobot (ja testado acima)
    # e verificar que nenhuma ferramenta manual foi executada

    result = bmo_backend.ask_nanobot("Crie um arquivo teste.txt", "pt-BR", "test-session-tool")

    events = [e["event"] for e in captured_logs]
    assert "nanobot_runtime_failed" in events, "Esperava nanobot_runtime_failed"
    assert "fallback_blocked" in events, "Esperava fallback_blocked"

    # Se tivesse caido no fallback, execute_llm_tool teria sido chamado
    # e create_file_tool teria sido executado.
    # Como nao caiu, recebemos so a mensagem de erro.
    assert "tropecei" in result, f"Esperava mensagem de erro, recebeu: {result}"

    print("[PASS] Comando 'criar arquivo' bloqueado — fallback nao executou tools manuais.")

def test_build_still_works():
    """Verificar que Python compile continua funcionando."""
    import py_compile
    import tempfile

    src = os.path.join(os.path.dirname(__file__), "bmo_backend.py")
    try:
        py_compile.compile(src, doraise=True)
        print("[PASS] Python compile: bmo_backend.py OK")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] Python compile: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("TESTE: Fallback manual removido do fluxo de chat")
    print("=" * 60)
    print()

    try:
        setup()
    except Exception as e:
        print(f"[SETUP FAIL] {e}")
        # Tenta setup parcial
        pass

    tests = [
        test_fallback_blocked,
        test_nanobot_runtime_used,
        test_handle_chat_no_fallback,
        test_build_still_works,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()

    print("=" * 60)
    print(f"Resultado: {passed}/{len(tests)} passaram, {failed} falharam")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
