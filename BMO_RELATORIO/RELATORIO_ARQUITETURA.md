# RELATORIO DE ARQUITETURA - BMO Desktop

## Visao geral

O BMO Desktop e um assistente local para Windows construido com frontend em Electron + React + TypeScript e backend em Python. A interface roda no Electron, enquanto o backend Python expoe uma API HTTP local em `127.0.0.1:8787`.

O projeto integra o Nanobot como biblioteca interna, sem depender de um processo filho do Nanobot para responder ao chat. O backend monta o contexto, chama o provider configurado, executa ferramentas quando o modelo solicita `tool_calls`, persiste historico/memoria/lembretes e controla recursos locais como Piper TTS, Whisper.cpp, wake word e subagentes.

## Como o projeto foi construido

- Frontend: `src/App.tsx`, `src/main.tsx`, React, TypeScript, Vite e Electron.
- Backend: `backend/bmo_backend.py`, com apoio de `backend/tools.py`, `backend/nanobot_bridge.py` e `backend/rate_limit.py`.
- Motor de agente: Nanobot incluido no repositorio e carregado por bridge Python.
- Provider LLM: OpenRouter/OpenAI via API compativel com Chat Completions.
- Voz TTS: Piper local.
- Voz STT: Whisper.cpp local.
- Wake word: OpenWakeWord com modelo `wakeword.onnx`.
- Build: PyInstaller gera o backend Python empacotado; Electron Builder gera instalador NSIS.

## Decisoes de arquitetura

1. Backend local separado da interface

   O Electron nao executa a logica pesada diretamente. Ele conversa com o backend Python via HTTP local. Isso simplifica acesso a bibliotecas Python, audio, Whisper, Piper e Nanobot.

2. Nanobot como biblioteca

   O BMO nao deve subir o Nanobot como processo filho para cada resposta. O backend importa o Nanobot, le o registry de ferramentas e executa ferramentas pelo bridge. Isso reduz latencia e evita o "double-hop".

3. Dados do usuario fora do projeto

   O workspace padrao do BMO fica em `%USERPROFILE%\.bmo`, com subpastas para memoria, historico, sessoes, logs, config, voz e lembretes. Isso separa dados do usuario dos arquivos do app.

4. Runtime local para voz

   Piper, Whisper.cpp, modelos e wake word ficam em `runtime/` no desenvolvimento e sao copiados como `extraResources` no build do Electron.

5. API local simples

   O backend usa `ThreadingHTTPServer`, endpoints REST e JSON. O frontend usa `fetch` com `AbortController` e timeout.

## Comunicacao frontend/backend

O frontend chama diretamente `http://127.0.0.1:8787`.

Funcoes centrais:

- `getJson(path)`: faz `GET` com timeout.
- `postJson(path, payload)`: faz `POST` com JSON e timeout.

Endpoints principais:

- `GET /api/health`
- `GET/POST /api/settings`
- `POST /api/chat`
- `POST /api/speak`
- `POST /api/listen`
- `POST /api/voice-chat`
- `POST /api/whisper/test`
- `GET/POST /api/reminders`
- `GET/POST /api/subagents`
- `GET/POST /api/history`
- `POST /api/history/export`
- `GET /api/tools`
- `POST /api/nanobot/tool`
- `POST /api/file/write`
- `POST /api/shell/exec`

O fluxo normal do chat e:

1. Usuario envia mensagem no React.
2. Frontend chama `POST /api/chat`.
3. Backend verifica lembrete, criacao local simples, jogo/subagente local claro ou chama o provider.
4. Backend monta mensagens e inclui `tools` no payload.
5. Se o modelo retorna `tool_calls`, o backend executa a ferramenta e envia resultado de volta ao modelo.
6. Backend salva historico e devolve resposta ao frontend.
7. Frontend atualiza UI e, se voz estiver ativa, chama `/api/speak`.

## Integracao com Nanobot

A integracao fica concentrada em `backend/nanobot_bridge.py` e no uso feito por `backend/bmo_backend.py`.

O bridge:

- Localiza o codigo do Nanobot.
- Carrega configuracao runtime.
- Expoe o registry original de ferramentas.
- Converte definicoes para formato compativel com OpenAI/OpenRouter:
  - `type: "function"`
  - `function.name`
  - `function.description`
  - `function.parameters`
- Executa ferramentas pelo registry original.

O backend tambem adiciona ferramentas de compatibilidade do BMO:

- `create_file`
- `shell_exec`
- `create_subagent`

Essas ferramentas garantem que pedidos como criar arquivo, executar Python e criar subagente funcionem mesmo quando o modelo nao conhece nomes internos do Nanobot.

## Piper TTS

O Piper e usado para transformar texto em audio local.

Fluxo:

1. Backend recebe `/api/speak`.
2. `speak_text()` limpa o texto com `text_for_speech()`.
3. Escolhe modelo `.onnx` em `runtime/piper` ou recurso empacotado.
4. Executa `piper.exe` com:
   - `--model`
   - `--output_file`
   - `--espeak_data`
   - `--quiet`
5. Gera `bmo_reply.wav` em `.bmo/voice`.
6. No Windows, toca o WAV com `winsound.PlaySound`.

O subprocess do Piper usa flags para nao abrir janela de terminal.

## Whisper STT

O Whisper usa `sounddevice` para capturar audio do microfone e `whisper-cli.exe` do Whisper.cpp para transcrever.

Fluxo:

1. `record_microphone()` grava audio em 16 kHz mono.
2. Salva `input.wav` em `.bmo/voice`.
3. `transcribe_wav()` chama `whisper-cli.exe`.
4. Se GPU estiver habilitada e houver backend Vulkan disponivel, tenta GPU.
5. Se a GPU falhar e `fallback_to_cpu` estiver ativo, repete com `--no-gpu`.
6. Primeiro tenta idioma `pt`; se falhar, tenta `en`.

O status do Whisper informa:

- modelo selecionado (`tiny`, `base`, `small`);
- caminho do modelo;
- backends GPU detectados;
- ultimo modo usado (`gpu` ou `cpu`);
- ultimo erro.

## Wake word

A wake word usa OpenWakeWord com `wakeword.onnx`.

Fluxo:

1. `wakeword_loop()` roda em thread daemon.
2. Verifica se o modelo existe.
3. Seleciona microfone padrao via `sounddevice`.
4. Abre `InputStream` em 16 kHz.
5. Envia blocos de audio ao modelo OpenWakeWord.
6. Se score >= `0.55`, registra:
   - `wake_word_detected`
   - frase `Hey BMO`
   - score detectado
7. Atualiza `wakeword_state.eventId`, que pode ser consultado pelo frontend em `/api/system`.

O loop tem pausa de `0.1s` entre ciclos e retry com `sleep(5)` em caso de erro.

## Lembretes

Os lembretes ficam em `.bmo/reminders/reminders.json`.

Fluxo:

1. Usuario cria lembrete por chat ou endpoint `/api/reminders`.
2. Backend salva:
   - `id`
   - `text`
   - `dueAt`
   - `createdAt`
   - `completed`
   - `notified`
3. `reminder_loop()` roda em thread daemon a cada 1 segundo.
4. Quando `dueAt <= now`, chama `fire_due_reminders_once()`.
5. Marca `backendFired`.
6. Registra `reminder_fired`.
7. Tenta falar o lembrete via Piper.
8. Frontend tambem consulta lembretes e exibe popup visual.

## Build e empacotamento

O build tem duas etapas principais.

### PyInstaller

Arquivo encontrado:

- `build/pyinstaller/bmo_backend.spec`

Esse `.spec` empacota `backend/bmo_backend.py` como `bmo_backend`, com `console=False`.

Hidden imports e coletas relevantes:

- `nanobot`
- `sounddevice`
- `numpy`
- `psutil`
- `openwakeword`
- `scipy`
- `sklearn`

Isso e importante para evitar erros como `No module named 'numpy'` no executavel empacotado.

### Electron Builder

Nao existe `electron-builder.yml` na raiz do projeto. A configuracao do Electron Builder esta dentro de `package.json`, no campo `build`.

Configuracao principal:

- `appId`: `com.bmo.desktop`
- `productName`: `BMO`
- output: `electron-release`
- target Windows: `nsis`
- `afterPack`: `build-support/after-pack.cjs`
- recursos extras:
  - `backend-dist/bmo_backend`
  - `config`
  - `nanobot`
  - `bridge`
  - `runtime/piper`
  - `runtime/whisper.cpp`
  - `runtime/sounds`
  - `runtime/ffmpeg`
  - `runtime/wakeword.onnx`
  - icone
  - VC redist

O build filtra secrets em `config`, evitando empacotar `secrets.env` e backups `.env`.

## O que esta funcionando

- Frontend React/Electron abre e conversa com backend local.
- Backend Python sobe API local.
- `POST /api/chat` salva historico.
- Provider OpenRouter/OpenAI e configuravel.
- Payload do provider agora inclui `tools`.
- Tool calls sao executadas no backend.
- `create_file` funciona para criar arquivo real.
- `shell_exec` funciona para comandos permitidos.
- `create_subagent` cria item visivel em `/api/subagents`.
- Criacao direta de `teste.txt` na area de trabalho foi testada.
- Criacao e abertura de `jogo_da_velha.py` com Tkinter foi testada.
- Subagente "Subagente de Pesquisa sobre IA" foi testado e apareceu na lista.
- Piper esta integrado ao endpoint `/api/speak`.
- Whisper esta integrado aos endpoints `/api/listen`, `/api/voice-chat` e `/api/whisper/test`.
- Wake word inicia em thread daemon quando dependencias/modelo estao presentes.
- Lembretes possuem loop backend e disparo de voz.
- Historico de conversa possui exportacao em TXT, JSON e Markdown.

## O que nao esta funcionando ou precisa de atencao

- `electron-builder.yml` solicitado nao existe; a configuracao esta no `package.json`.
- O provider pode retornar erro de chave/permissao. Quando isso acontece antes de qualquer `tool_call`, tarefas puramente locais precisam de fallback local.
- Alguns comportamentos ainda dependem da qualidade da resposta do modelo. Exemplo: o modelo pode criar script no Desktop e tentar executar a partir do workspace. Foi adicionada normalizacao para scripts `.py`, mas esse ponto merece regressao futura.
- Os testes finais desta etapa validaram ferramentas locais, arquivo, jogo e subagente. Nao foi gerado instalador.
- Piper, Whisper, wake word e lembretes estao implementados, mas devem ser retestados no app empacotado final, porque dependem de binarios/modelos/dispositivos de audio.
- Whisper depende de `numpy`, `sounddevice`, modelos `ggml` e runtime Whisper.cpp. Se qualquer item faltar no ambiente empacotado, STT falha.
- Wake word depende de `openwakeword`, `sounddevice`, modelo `wakeword.onnx` e microfone padrao correto.
- O app usa HTTP local fixo em `127.0.0.1:8787`; se a porta estiver ocupada, o frontend pode nao encontrar o backend.
- Ha arquivos e pastas de build/teste antigos no projeto (`backend-dist`, `electron-release`, `dist`, logs e executaveis). Eles podem confundir revisoes se nao forem separados de artefatos finais.
- Ainda nao foi validado nesta etapa em VM limpa sem Node/Python instalado.

## Estado atual recomendado

Antes de gerar o executavel final, recomenda-se:

1. Rodar o app pelo atalho/dev normal e testar chat com chave OpenRouter valida.
2. Testar Piper em `/api/speak`.
3. Testar Whisper em `/api/whisper/test`.
4. Testar "Hey BMO" com o microfone correto.
5. Testar lembrete de 10 segundos com popup e voz.
6. Rodar build PyInstaller em pasta limpa.
7. Rodar Electron Builder/NSIS.
8. Testar instalador em ambiente limpo.

## Arquivos copiados para este relatorio

- `backend/bmo_backend.py`
- `backend/tools.py`
- `backend/nanobot_bridge.py`
- `backend/rate_limit.py`
- `package.json`
- `build/pyinstaller/bmo_backend.spec`
- `src/App.tsx`
- `src/main.tsx`

Observacao: `electron-builder.yml` nao foi copiado porque nao existe no projeto no momento desta coleta.
