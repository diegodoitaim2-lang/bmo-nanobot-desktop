# TEST_REPORT

Gerado em: 2026-06-05T18:13:13
Projeto: `C:\Users\USER\Documents\Codex\bmo`
Backend: `http://127.0.0.1:8787`
Resumo: 20 passou, 0 falhou, 1 aviso.

## Tabela Resumo

| Teste | Status | Duracao | Modulo |
| --- | --- | ---: | --- |
| Preflight do backend | PASSOU | 4.86s | Backend |
| 1. Chat basico | PASSOU | 22.89s | Chat |
| 2. Contexto | PASSOU | 39.50s | Chat |
| 3. Memoria | PASSOU | 1.22s | Memoria |
| 4. Historico | PASSOU | 1.21s | Historico |
| 5. Pesquisa web | PASSOU | 1.21s | Ferramentas |
| 6. Analise de imagem | PASSOU | 21.38s | Anexos |
| 7. Upload multiplo | PASSOU | 21.50s | Anexos |
| 8. Whisper | PASSOU | 1.29s | Voz |
| 9. Piper TTS | PASSOU | 4.54s | Voz |
| 10. Wake Word | PASSOU | 1.28s | Wake Word |
| 11. Tarefas | PASSOU | 1.18s | Tarefas |
| 12. Alarmes | PASSOU | 8.22s | Lembretes |
| 13. Subagentes | PASSOU | 25.43s | Subagentes |
| 14. Workspace | PASSOU | 1.32s | Workspace |
| 15. Organizacao de arquivos | PASSOU | 1.27s | Arquivos |
| 16. Recuperacao apos reinicio | PASSOU | 3.78s | Sistema |
| 17. Fechar para bandeja | PASSOU | 1.28s | Electron |
| 18. Uso continuo por 30 minutos | AVISO | 1.26s | Estabilidade |
| 19. Consumo de CPU | PASSOU | 7.46s | Performance |
| 20. Consumo de memoria | PASSOU | 2.35s | Performance |

## Detalhes

### Preflight do backend - PASSOU

- Horario: 2026-06-05T18:09:53
- Duracao: 4.86s
- Modulo responsavel: Backend
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `BmoHandler.do_GET / system_status`
- Resultado: Backend respondeu /api/health e /api/system.
- CPU/RAM antes: Sistema CPU 50.0%; Sistema RAM 50.7%; BMO CPU 99.7%; BMO RAM 135.3 MB; processos 5
- CPU/RAM depois: Sistema CPU 46.2%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 219.6 MB; processos 5

Detalhes:

```json
{
  "nanobot": false,
  "system": {
    "backend": true,
    "nanobot": false,
    "piper": true,
    "whisper": true,
    "whisperConfig": {
      "gpu_enabled": true,
      "gpu_index": 0,
      "model": "base",
      "fallback_to_cpu": true,
      "exe": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\whisper.cpp\\Win32\\Release\\whisper-cli.exe",
      "exeExists": true,
      "modelPath": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\whisper.cpp\\models\\ggml-base.bin",
      "modelExists": true,
      "models": [
        {
          "id": "tiny",
          "label": "Leve (Tiny)",
          "file": "ggml-tiny.bin",
          "path": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\whisper.cpp\\models\\ggml-tiny.bin",
          "exists": false
        },
        {
          "id": "base",
          "label": "Equilibrado (Base)",
          "file": "ggml-base.bin",
          "path": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\whisper.cpp\\models\\ggml-base.bin",
          "exists": true
        },
        {
          "id": "small",
          "label": "Preciso (Small)",
          "file": "ggml-small.bin",
          "path": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\whisper.cpp\\models\\ggml-small.bin",
          "exists": false
        }
      ],
      "lastMode": "cpu",
      "lastError": ""
    },
    "wakeword": {
      "enabled": true,
      "available": true,
      "dependency": true,
      "eventId": 0,
      "running": true,
      "message": "Wake word pronto.",
      "model": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\wakeword.onnx"
    },
    "cpuPercent": 56,
    "memoryPercent": 50,
    "python": "3.11.15",
    "paths": {
      "root": "C:\\Users\\USER\\Documents\\Codex\\bmo",
      "appData": "C:\\Users\\USER\\AppData\\Local\\BMO",
      "config": "C:\\Users\\USER\\Documents\\Codex\\bmo\\config",
      "memory": "C:\\Users\\USER\\AppData\\Local\\BMO",
      "voices": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\piper",
      "sounds": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\sounds",
      "ffmpeg": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\ffmpeg\\ffmpeg.exe",
      "piper": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\piper\\piper\\piper.exe",
      "whisper": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\whisper.cpp\\Win32\\Release\\whisper-cli.exe",
      "wakeword": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\wakeword.onnx"
    }
  }
}
```

Logs capturados:

```text
2026-06-05 18:09:56 voice ignored invalid_size file=C:\Users\USER\Documents\Codex\bmo\runtime\piper\razo-piper-voice.onnx size=15
```

### 1. Chat basico - PASSOU

- Horario: 2026-06-05T18:09:59
- Duracao: 22.89s
- Modulo responsavel: Chat
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `ask_nanobot`
- Resultado: Chat retornou resposta em texto (6 caracteres).
- CPU/RAM antes: Sistema CPU 6.7%; Sistema RAM 42.0%; BMO CPU 0.0%; BMO RAM 219.6 MB; processos 5
- CPU/RAM depois: Sistema CPU 82.4%; Sistema RAM 42.9%; BMO CPU 0.0%; BMO RAM 224.8 MB; processos 5

Detalhes:

```json
{
  "reply": "OK BMO"
}
```

Logs capturados:

```text
O\Documents\Codex\bmo command=C:\Users\USER\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m nanobot serve --host 127.0.0.1 --port 8900 --timeout 180 --config C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json --workspace C:\Users\USER\AppData\Local\BMO\workspace

2026-06-05 18:10:18 chat context session=validacao-e5d79809 context_messages=0 chars=0 prompt_chars=4635

2026-06-05 18:10:18 chat http error model=openai/gpt-oss-120b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:18 chat request model=openai/gpt-oss-20b:free model_fallback=1 key=3/3

2026-06-05 18:10:18 restarting nanobot to apply model/key requested_model=openai/gpt-oss-20b:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:10:18 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:10:18 chat context session=validacao-e5d79809 context_messages=0 chars=0 prompt_chars=4635

2026-06-05 18:10:18 chat http error model=openai/gpt-oss-20b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:18 chat request model=meta-llama/llama-3.3-70b-instruct:free model_fallback=2 key=3/3

2026-06-05 18:10:19 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.3-70b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:10:19 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:10:19 chat context session=validacao-e5d79809 context_messages=0 chars=0 prompt_chars=4635

2026-06-05 18:10:19 chat http error model=meta-llama/llama-3.3-70b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:19 chat request model=meta-llama/llama-3.2-3b-instruct:free model_fallback=3 key=3/3

2026-06-05 18:10:19 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.2-3b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:10:19 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:10:20 chat context session=validacao-e5d79809 context_messages=0 chars=0 prompt_chars=4635

2026-06-05 18:10:20 chat http error model=meta-llama/llama-3.2-3b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:20 chat request model=qwen/qwen3-coder:free model_fallback=4 key=3/3

2026-06-05 18:10:20 restarting nanobot to apply model/key requested_model=qwen/qwen3-coder:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:10:20 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:10:20 chat context session=validacao-e5d79809 context_messages=0 chars=0 prompt_chars=4635

2026-06-05 18:10:20 chat http error model=qwen/qwen3-coder:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:20 nanobot chat exhausted, using direct provider fallback: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:20 direct chat request provider=openrouter model=openai/gpt-oss-120b:free model_fallback=0 key=1/3

2026-06-05 18:10:20 chat context session=validacao-e5d79809 context_messages=0 chars=0 prompt_chars=4635
```

### 2. Contexto - PASSOU

- Horario: 2026-06-05T18:10:23
- Duracao: 39.50s
- Modulo responsavel: Chat
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `build_model_messages`
- Resultado: Contexto da mesma sessao foi preservado.
- CPU/RAM antes: Sistema CPU 75.0%; Sistema RAM 43.2%; BMO CPU 0.0%; BMO RAM 224.8 MB; processos 5
- CPU/RAM depois: Sistema CPU 16.7%; Sistema RAM 42.6%; BMO CPU 0.0%; BMO RAM 226.3 MB; processos 5

Detalhes:

```json
{
  "token": "CTX-38911d",
  "reply": "CTX-38911d"
}
```

Logs capturados:

```text
Codex\bmo command=C:\Users\USER\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m nanobot serve --host 127.0.0.1 --port 8900 --timeout 180 --config C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json --workspace C:\Users\USER\AppData\Local\BMO\workspace

2026-06-05 18:10:58 chat context session=validacao-e5d79809 context_messages=4 chars=130 prompt_chars=4782

2026-06-05 18:10:58 chat http error model=openai/gpt-oss-120b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:58 chat request model=openai/gpt-oss-20b:free model_fallback=1 key=3/3

2026-06-05 18:10:58 restarting nanobot to apply model/key requested_model=openai/gpt-oss-20b:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:10:58 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:10:59 chat context session=validacao-e5d79809 context_messages=4 chars=130 prompt_chars=4782

2026-06-05 18:10:59 chat http error model=openai/gpt-oss-20b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:59 chat request model=meta-llama/llama-3.3-70b-instruct:free model_fallback=2 key=3/3

2026-06-05 18:10:59 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.3-70b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:10:59 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:10:59 chat context session=validacao-e5d79809 context_messages=4 chars=130 prompt_chars=4782

2026-06-05 18:10:59 chat http error model=meta-llama/llama-3.3-70b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:10:59 chat request model=meta-llama/llama-3.2-3b-instruct:free model_fallback=3 key=3/3

2026-06-05 18:10:59 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.2-3b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:00 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:00 chat context session=validacao-e5d79809 context_messages=4 chars=130 prompt_chars=4782

2026-06-05 18:11:00 chat http error model=meta-llama/llama-3.2-3b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:00 chat request model=qwen/qwen3-coder:free model_fallback=4 key=3/3

2026-06-05 18:11:00 restarting nanobot to apply model/key requested_model=qwen/qwen3-coder:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:00 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:01 chat context session=validacao-e5d79809 context_messages=4 chars=130 prompt_chars=4782

2026-06-05 18:11:01 chat http error model=qwen/qwen3-coder:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:01 nanobot chat exhausted, using direct provider fallback: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:01 direct chat request provider=openrouter model=openai/gpt-oss-120b:free model_fallback=0 key=1/3

2026-06-05 18:11:01 chat context session=validacao-e5d79809 context_messages=4 chars=130 prompt_chars=4782
```

### 3. Memoria - PASSOU

- Horario: 2026-06-05T18:11:04
- Duracao: 1.22s
- Modulo responsavel: Memoria
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `read_memories/update memory`
- Resultado: Memoria adiciona, lista e permite limpeza.
- CPU/RAM antes: Sistema CPU 47.1%; Sistema RAM 42.6%; BMO CPU 0.0%; BMO RAM 226.3 MB; processos 5
- CPU/RAM depois: Sistema CPU 58.3%; Sistema RAM 42.6%; BMO CPU 0.0%; BMO RAM 226.3 MB; processos 5

Detalhes:

```json
{
  "createdId": "1780693865730"
}
```

### 4. Historico - PASSOU

- Horario: 2026-06-05T18:11:06
- Duracao: 1.21s
- Modulo responsavel: Historico
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `save_chat_turn/read_history`
- Resultado: Historico salvou a conversa atual.
- CPU/RAM antes: Sistema CPU 62.5%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 226.3 MB; processos 5
- CPU/RAM depois: Sistema CPU 8.3%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 226.5 MB; processos 5

Detalhes:

```json
{
  "sessionId": "validacao-e5d79809",
  "messages": 6
}
```

### 5. Pesquisa web - PASSOU

- Horario: 2026-06-05T18:11:09
- Duracao: 1.21s
- Modulo responsavel: Ferramentas
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `tools_status/web_search`
- Resultado: Ferramenta web_search registrada e ativa.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 226.5 MB; processos 5
- CPU/RAM depois: Sistema CPU 0.0%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 226.5 MB; processos 5

Detalhes:

```json
{
  "tool": {
    "id": "web_search",
    "label": "Busca web",
    "description": "Permite pesquisar na web quando o provedor/modelo suportar essa habilidade.",
    "native": true,
    "configKey": "web_search",
    "enabled": true,
    "status": "ativo"
  }
}
```

### 6. Analise de imagem - PASSOU

- Horario: 2026-06-05T18:11:11
- Duracao: 21.38s
- Modulo responsavel: Anexos
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\src\App.tsx`
- Funcao responsavel: `handleSend`
- Resultado: Imagem enviada pelo chat foi recebida, salva e considerada na resposta.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 226.5 MB; processos 5
- CPU/RAM depois: Sistema CPU 58.3%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 227.9 MB; processos 5

Detalhes:

```json
{
  "reply": "A imagem está anexada corretamente, mas como é um arquivo 1 × 1 px não há conteúdo visual para descrever.",
  "attachment": {
    "name": "validacao_imagem.png",
    "type": "image/png",
    "kind": "image",
    "size": 68,
    "path": "C:\\Users\\USER\\AppData\\Local\\BMO\\uploads\\validacao-e5d79809\\1780693872_1_validacao_imagem.png",
    "image": {
      "width": 1,
      "height": 1,
      "format": "PNG"
    }
  }
}
```

Logs capturados:

```text
Codex\bmo command=C:\Users\USER\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m nanobot serve --host 127.0.0.1 --port 8900 --timeout 180 --config C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json --workspace C:\Users\USER\AppData\Local\BMO\workspace

2026-06-05 18:11:27 chat context session=validacao-e5d79809 context_messages=6 chars=192 prompt_chars=5248

2026-06-05 18:11:27 chat http error model=openai/gpt-oss-120b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:27 chat request model=openai/gpt-oss-20b:free model_fallback=1 key=3/3

2026-06-05 18:11:27 restarting nanobot to apply model/key requested_model=openai/gpt-oss-20b:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:27 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:28 chat context session=validacao-e5d79809 context_messages=6 chars=192 prompt_chars=5248

2026-06-05 18:11:28 chat http error model=openai/gpt-oss-20b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:28 chat request model=meta-llama/llama-3.3-70b-instruct:free model_fallback=2 key=3/3

2026-06-05 18:11:28 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.3-70b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:28 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:28 chat context session=validacao-e5d79809 context_messages=6 chars=192 prompt_chars=5248

2026-06-05 18:11:28 chat http error model=meta-llama/llama-3.3-70b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:29 chat request model=meta-llama/llama-3.2-3b-instruct:free model_fallback=3 key=3/3

2026-06-05 18:11:29 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.2-3b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:29 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:29 chat context session=validacao-e5d79809 context_messages=6 chars=192 prompt_chars=5248

2026-06-05 18:11:29 chat http error model=meta-llama/llama-3.2-3b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:29 chat request model=qwen/qwen3-coder:free model_fallback=4 key=3/3

2026-06-05 18:11:29 restarting nanobot to apply model/key requested_model=qwen/qwen3-coder:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:29 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:30 chat context session=validacao-e5d79809 context_messages=6 chars=192 prompt_chars=5248

2026-06-05 18:11:30 chat http error model=qwen/qwen3-coder:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:30 nanobot chat exhausted, using direct provider fallback: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:30 direct chat request provider=openrouter model=openai/gpt-oss-120b:free model_fallback=0 key=1/3

2026-06-05 18:11:30 chat context session=validacao-e5d79809 context_messages=6 chars=192 prompt_chars=5248
```

### 7. Upload multiplo - PASSOU

- Horario: 2026-06-05T18:11:34
- Duracao: 21.50s
- Modulo responsavel: Anexos
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\src\App.tsx`
- Funcao responsavel: `handleFileChange/handleSend`
- Resultado: Upload multiplo chegou ao backend, foi salvo e voltou na resposta.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 227.9 MB; processos 5
- CPU/RAM depois: Sistema CPU 58.3%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "attachments": [
    {
      "name": "validacao_1.png",
      "type": "image/png",
      "kind": "image",
      "size": 68,
      "path": "C:\\Users\\USER\\AppData\\Local\\BMO\\uploads\\validacao-e5d79809\\1780693895_1_validacao_1.png",
      "image": {
        "width": 1,
        "height": 1,
        "format": "PNG"
      }
    },
    {
      "name": "validacao_2.txt",
      "type": "text/plain",
      "kind": "text",
      "size": 25,
      "path": "C:\\Users\\USER\\AppData\\Local\\BMO\\uploads\\validacao-e5d79809\\1780693895_2_validacao_2.txt",
      "textPreview": "conteudo de validacao BMO"
    }
  ]
}
```

Logs capturados:

```text
Codex\bmo command=C:\Users\USER\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m nanobot serve --host 127.0.0.1 --port 8900 --timeout 180 --config C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json --workspace C:\Users\USER\AppData\Local\BMO\workspace

2026-06-05 18:11:50 chat context session=validacao-e5d79809 context_messages=8 chars=737 prompt_chars=6006

2026-06-05 18:11:50 chat http error model=openai/gpt-oss-120b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:50 chat request model=openai/gpt-oss-20b:free model_fallback=1 key=3/3

2026-06-05 18:11:50 restarting nanobot to apply model/key requested_model=openai/gpt-oss-20b:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:50 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:50 chat context session=validacao-e5d79809 context_messages=8 chars=737 prompt_chars=6006

2026-06-05 18:11:50 chat http error model=openai/gpt-oss-20b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:50 chat request model=meta-llama/llama-3.3-70b-instruct:free model_fallback=2 key=3/3

2026-06-05 18:11:50 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.3-70b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:51 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:51 chat context session=validacao-e5d79809 context_messages=8 chars=737 prompt_chars=6006

2026-06-05 18:11:51 chat http error model=meta-llama/llama-3.3-70b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:51 chat request model=meta-llama/llama-3.2-3b-instruct:free model_fallback=3 key=3/3

2026-06-05 18:11:51 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.2-3b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:51 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:52 chat context session=validacao-e5d79809 context_messages=8 chars=737 prompt_chars=6006

2026-06-05 18:11:52 chat http error model=meta-llama/llama-3.2-3b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:52 chat request model=qwen/qwen3-coder:free model_fallback=4 key=3/3

2026-06-05 18:11:52 restarting nanobot to apply model/key requested_model=qwen/qwen3-coder:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:11:52 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:11:52 chat context session=validacao-e5d79809 context_messages=8 chars=737 prompt_chars=6006

2026-06-05 18:11:52 chat http error model=qwen/qwen3-coder:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:52 nanobot chat exhausted, using direct provider fallback: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:11:52 direct chat request provider=openrouter model=openai/gpt-oss-120b:free model_fallback=0 key=1/3

2026-06-05 18:11:52 chat context session=validacao-e5d79809 context_messages=8 chars=737 prompt_chars=6006
```

### 8. Whisper - PASSOU

- Horario: 2026-06-05T18:11:56
- Duracao: 1.29s
- Modulo responsavel: Voz
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `microphone_devices/listen_once`
- Resultado: Whisper disponivel e 6 microfone(s) detectado(s).
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 8.3%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "devices": [
    {
      "id": 0,
      "name": "Microsoft Sound Mapper - Input",
      "channels": 2
    },
    {
      "id": 1,
      "name": "Microphone (WO Mic Device)",
      "channels": 1
    },
    {
      "id": 4,
      "name": "Driver de captura de som primário",
      "channels": 2
    },
    {
      "id": 5,
      "name": "Microphone (WO Mic Device)",
      "channels": 1
    },
    {
      "id": 9,
      "name": "Microphone (WO Mic Device)",
      "channels": 1
    }
  ]
}
```

### 9. Piper TTS - PASSOU

- Horario: 2026-06-05T18:11:59
- Duracao: 4.54s
- Modulo responsavel: Voz
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `speak_text`
- Resultado: Piper gerou e reproduziu WAV (84696 bytes).
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 25.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "audio": "C:\\Users\\USER\\AppData\\Local\\BMO\\voice\\bmo_reply_d9cbc70f.wav",
  "voice": "pt_BR-faber-medium.onnx"
}
```

Logs capturados:

```text
2026-06-05 18:12:00 [AUDIO] iniciando teste/fala TTS

2026-06-05 18:12:00 [AUDIO] texto enviado ao TTS chars=32 preview=Teste de voz do BMO funcionando.

2026-06-05 18:12:00 [AUDIO] comando Piper exe=C:\Users\USER\Documents\Codex\bmo\runtime\piper\piper\piper.exe model=C:\Users\USER\Documents\Codex\bmo\runtime\piper\pt_BR-faber-medium.onnx espeak=C:\Users\USER\Documents\Codex\bmo\runtime\piper\piper\espeak-ng-data wav=C:\Users\USER\AppData\Local\BMO\voice\bmo_reply_d9cbc70f.wav

2026-06-05 18:12:01 [AUDIO] wav gerado path=C:\Users\USER\AppData\Local\BMO\voice\bmo_reply_d9cbc70f.wav

2026-06-05 18:12:01 [AUDIO] tamanho do wav bytes=84696

2026-06-05 18:12:01 [AUDIO] reproduzindo wav path=C:\Users\USER\AppData\Local\BMO\voice\bmo_reply_d9cbc70f.wav

2026-06-05 18:12:03 [AUDIO] playback ok wav=C:\Users\USER\AppData\Local\BMO\voice\bmo_reply_d9cbc70f.wav
```

### 10. Wake Word - PASSOU

- Horario: 2026-06-05T18:12:05
- Duracao: 1.28s
- Modulo responsavel: Wake Word
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `wakeword_status`
- Resultado: Wake word esta carregado e listener esta rodando.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "wakeword": {
    "enabled": true,
    "available": true,
    "dependency": true,
    "eventId": 0,
    "running": true,
    "message": "Wake word pronto.",
    "model": "C:\\Users\\USER\\Documents\\Codex\\bmo\\runtime\\wakeword.onnx"
  }
}
```

### 11. Tarefas - PASSOU

- Horario: 2026-06-05T18:12:07
- Duracao: 1.18s
- Modulo responsavel: Tarefas
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `update_tasks/create_task`
- Resultado: Criacao/listagem de tarefa funcionou.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 61.5%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "taskId": "0232caeba8"
}
```

Logs capturados:

```text
2026-06-05 18:12:08 task created id=0232caeba8 title=tarefa temporaria validacao bb8bf0
```

### 12. Alarmes - PASSOU

- Horario: 2026-06-05T18:12:09
- Duracao: 8.22s
- Modulo responsavel: Lembretes
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `update_reminder/reminders_status`
- Resultado: Lembrete futuro foi salvo e apareceu como vencido no horario.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 0.0%; Sistema RAM 42.6%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "reminderId": "561f97adf2a6"
}
```

Logs capturados:

```text
2026-06-05 18:12:10 reminder created id=561f97adf2a6 dueAt=1780693936 text=lembrete temporario validacao 831701

2026-06-05 18:12:10 reminders saved count=9 file=C:\Users\USER\AppData\Local\BMO\reminders.json

2026-06-05 18:12:17 reminder scheduler check pending=1 due=1 now=1780693937

2026-06-05 18:12:17 reminders saved count=8 file=C:\Users\USER\AppData\Local\BMO\reminders.json
```

### 13. Subagentes - PASSOU

- Horario: 2026-06-05T18:12:19
- Duracao: 25.43s
- Modulo responsavel: Subagentes
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `create_subagent/subagent_worker`
- Resultado: Subagente foi registrado, executou e gerou arquivo.
- CPU/RAM antes: Sistema CPU 8.3%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 43.8%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "agent": {
    "id": "008-edf37f",
    "title": "crie um subagente para escrever uma frase curta e salvar em validacao_bmo_subage",
    "task": "crie um subagente para escrever uma frase curta e salvar em validacao_bmo_subagente_5655d2.txt",
    "status": "concluido",
    "progress": 100,
    "createdAt": 1780693940,
    "updatedAt": 1780693962,
    "outputFile": "validacao_bmo_subagente_5655d2.txt",
    "notified": false,
    "log": "Arquivo salvo em C:\\Users\\USER\\Desktop\\validacao_bmo_subagente_5655d2.txt",
    "result": "Oba, deixei prontinho!  \nFrase curta: “Validação concluída com sucesso!”  \n\nProntinho! Salvei o texto em: C:\\Users\\USER\\AppData\\Local\\BMO\\uploads\\validacao-bmo\\validacao_bmo_subagente_5655d2.txt",
    "outputPath": "C:\\Users\\USER\\Desktop\\validacao_bmo_subagente_5655d2.txt",
    "completedAt": 1780693962
  }
}
```

Logs capturados:

```text
-desktop command=C:\Users\USER\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -m nanobot serve --host 127.0.0.1 --port 8900 --timeout 180 --config C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json --workspace C:\Users\USER\AppData\Local\BMO\workspace

2026-06-05 18:12:35 chat context session=new context_messages=0 chars=0 prompt_chars=4903

2026-06-05 18:12:35 chat http error model=openai/gpt-oss-120b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:12:35 chat request model=openai/gpt-oss-20b:free model_fallback=1 key=3/3

2026-06-05 18:12:35 restarting nanobot to apply model/key requested_model=openai/gpt-oss-20b:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:12:35 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:12:35 chat context session=new context_messages=0 chars=0 prompt_chars=4903

2026-06-05 18:12:35 chat http error model=openai/gpt-oss-20b:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:12:35 chat request model=meta-llama/llama-3.3-70b-instruct:free model_fallback=2 key=3/3

2026-06-05 18:12:35 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.3-70b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:12:36 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:12:36 chat context session=new context_messages=0 chars=0 prompt_chars=4903

2026-06-05 18:12:36 chat http error model=meta-llama/llama-3.3-70b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:12:36 chat request model=meta-llama/llama-3.2-3b-instruct:free model_fallback=3 key=3/3

2026-06-05 18:12:36 restarting nanobot to apply model/key requested_model=meta-llama/llama-3.2-3b-instruct:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:12:36 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:12:37 chat context session=new context_messages=0 chars=0 prompt_chars=4903

2026-06-05 18:12:37 chat http error model=meta-llama/llama-3.2-3b-instruct:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:12:37 chat request model=qwen/qwen3-coder:free model_fallback=4 key=3/3

2026-06-05 18:12:37 restarting nanobot to apply model/key requested_model=qwen/qwen3-coder:free running_model=openai/gpt-oss-120b:free requested_key=3 running_key=3

2026-06-05 18:12:37 could not stop stale nanobot port=8900: 'NoneType' object has no attribute 'splitlines'

2026-06-05 18:12:37 chat context session=new context_messages=0 chars=0 prompt_chars=4903

2026-06-05 18:12:37 chat http error model=qwen/qwen3-coder:free key=3/3: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:12:37 nanobot chat exhausted, using direct provider fallback: Erro 400 do provedor: {"error": {"message": "Only configured model 'anthropic/claude-opus-4-5' is available", "type": "invalid_request_error", "code": 400}}

2026-06-05 18:12:37 direct chat request provider=openrouter model=openai/gpt-oss-120b:free model_fallback=0 key=1/3

2026-06-05 18:12:37 chat context session=new context_messages=0 chars=0 prompt_chars=4903

2026-06-05 18:12:42 subagent completed id=008-edf37f output=C:\Users\USER\Desktop\validacao_bmo_subagente_5655d2.txt
```

### 14. Workspace - PASSOU

- Horario: 2026-06-05T18:12:45
- Duracao: 1.32s
- Modulo responsavel: Workspace
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `RUNTIME_WORKSPACE`
- Resultado: Workspace esta acessivel: C:\Users\USER\AppData\Local\BMO\workspace
- CPU/RAM antes: Sistema CPU 6.2%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 0.0%; Sistema RAM 42.4%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "workspace": "C:\\Users\\USER\\AppData\\Local\\BMO\\workspace"
}
```

### 15. Organizacao de arquivos - PASSOU

- Horario: 2026-06-05T18:12:48
- Duracao: 1.27s
- Modulo responsavel: Arquivos
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `create_file_from_message`
- Resultado: Arquivo foi criado por ferramenta real: C:\Users\USER\Desktop\validacao_bmo_0e0c6d.txt
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.4%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 0.0%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "file": {
    "path": "C:\\Users\\USER\\Desktop\\validacao_bmo_0e0c6d.txt",
    "name": "validacao_bmo_0e0c6d.txt",
    "size": 29,
    "reply": "Prontinho. Eu criei o arquivo na sua area de trabalho: validacao_bmo_0e0c6d.txt"
  }
}
```

Logs capturados:

```text
2026-06-05 18:12:49 file created path=C:\Users\USER\Desktop\validacao_bmo_0e0c6d.txt size=29
```

### 16. Recuperacao apos reinicio - PASSOU

- Horario: 2026-06-05T18:12:50
- Duracao: 3.78s
- Modulo responsavel: Sistema
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `stop_nanobot/start_nanobot`
- Resultado: Backend continuou acessivel apos reinicio do motor interno.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.5%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 64.3%; Sistema RAM 42.1%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "health": {
    "status": "ok",
    "nanobot": false
  }
}
```

### 17. Fechar para bandeja - PASSOU

- Horario: 2026-06-05T18:12:56
- Duracao: 1.28s
- Modulo responsavel: Electron
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\electron\main.cjs`
- Funcao responsavel: `mainWindow.on('close')`
- Resultado: Codigo Electron intercepta X, usa bandeja e bloqueia segunda instancia.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.1%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 0.0%; Sistema RAM 42.2%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "Tray": true,
  "closeIntercept": true,
  "singleInstance": true,
  "reminderPopup": true
}
```

### 18. Uso continuo por 30 minutos - AVISO

- Horario: 2026-06-05T18:12:58
- Duracao: 1.26s
- Modulo responsavel: Estabilidade
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `HTTP endpoints`
- Resultado: Teste de 30 minutos nao executado nesta rodada. Use --long-minutes 30.
- CPU/RAM antes: Sistema CPU 0.0%; Sistema RAM 42.1%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 6.2%; Sistema RAM 42.1%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- Possivel causa: Validacao longa foi deixada opcional para nao bloquear desenvolvimento.
- Sugestao de correcao: Rodar python tools/validate_bmo.py --long-minutes 30 antes do build final.

### 19. Consumo de CPU - PASSOU

- Horario: 2026-06-05T18:13:01
- Duracao: 7.46s
- Modulo responsavel: Performance
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `background loops`
- Resultado: CPU BMO estimada: 0.3% em 5 processo(s).
- CPU/RAM antes: Sistema CPU 66.7%; Sistema RAM 42.1%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 25.0%; Sistema RAM 42.0%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "cpuValues": [
    0.0,
    0.0,
    0.3,
    0.0,
    0.0
  ],
  "threshold": 35.0
}
```

### 20. Consumo de memoria - PASSOU

- Horario: 2026-06-05T18:13:09
- Duracao: 2.35s
- Modulo responsavel: Performance
- Arquivo responsavel: `C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py`
- Funcao responsavel: `process memory`
- Resultado: RAM BMO estimada: 228.0 MB em 5 processo(s).
- CPU/RAM antes: Sistema CPU 37.5%; Sistema RAM 42.0%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5
- CPU/RAM depois: Sistema CPU 0.0%; Sistema RAM 42.0%; BMO CPU 0.0%; BMO RAM 228.0 MB; processos 5

Detalhes:

```json
{
  "ramMb": 228.015625,
  "processCount": 5,
  "thresholdMb": 900.0
}
```
