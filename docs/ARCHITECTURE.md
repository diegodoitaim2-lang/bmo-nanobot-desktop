# Arquitetura do BMO

Visão geral de como o BMO funciona internamente.

---

## Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────┐
│                 Electron (Janela)                │
│  ┌─────────────────────────────────────────────┐ │
│  │          React + Vite (Frontend)             │ │
│  │  Chat • Painéis • Voz • Tema                │ │
│  └────────────────┬────────────────────────────┘ │
└───────────────────┼──────────────────────────────┘
                    │ HTTP (localhost:8787)
┌───────────────────┼──────────────────────────────┐
│  ┌────────────────┴────────────────────────────┐ │
│  │        bmo_backend.py (Python HTTP Server)   │ │
│  │  Chat • Memória • Ferramentas • Voz • Cron   │ │
│  └────────────────┬────────────────────────────┘ │
│                   │                              │
│  ┌────────────────┴────────────────────────────┐ │
│  │         nanobot_integration.py               │ │
│  │  Singleton → NanobotRuntime                  │ │
│  └────────────────┬────────────────────────────┘ │
│                   │                              │
│  ┌────────────────┴────────────────────────────┐ │
│  │          Nanobot Runtime (nanobot/)           │ │
│  │  Loop • Tools • Memory • Skills • Channels   │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   Piper TTS  │  │   Whisper     │  │OpenWake  │ │
│  │   (voz)      │  │   (microfone) │  │Word      │ │
│  └─────────────┘  └──────────────┘  └──────────┘ │
└───────────────────────────────────────────────────┘
```

---

## Componentes Principais

### 1. Frontend (React + TypeScript)
- **Localização**: `src/`
- **Tecnologias**: React 18, TypeScript, Vite, Lucide React (ícones)
- **Estilo**: CSS customizado com temas (7 temas visuais)
- **Sprites**: Animações faciais do BMO usando faces SVG
- **Painéis**: Chat, Memória, Histórico, Modelos, Provedores, Voz, Ferramentas, Canais, Sistema, Configurações

### 2. Backend (Python)
- **Localização**: `backend/bmo_backend.py`
- **Tecnologias**: Python 3.11+, servidor HTTP embutido (`http.server`)
- **API REST**: ~50 endpoints em `localhost:8787`
- **Voz**: Piper TTS (texto→fala) + Whisper (fala→texto)
- **Wake Word**: OpenWakeWord com modelo ONNX

### 3. Nanobot Runtime
- **Localização**: `nanobot/` (submódulo/biblioteca)
- **Função**: Motor de IA — gerencia loop de conversa, ferramentas, memória, canais
- **Singleton**: Uma única instância compartilhada via `nanobot_integration.py`

### 4. Electron
- **Localização**: `electron/main.cjs`, `electron/preload.cjs`
- **Função**: Empacota frontend + backend + runtime em um executável
- **Build**: Electron Builder + NSIS para instalador Windows

---

## Fluxo de uma Mensagem

```
Usuário digita → React envia POST /api/chat
    → bmo_backend recebe
    → envia para NanobotRuntime.process_message()
    → Nanobot chama o provider de IA (LLM)
    → LLM retorna resposta + possíveis tool calls
    → Nanobot executa ferramentas (web search, arquivos, etc.)
    → Resposta final é retornada ao frontend
    → Frontend renderiza no chat
    → Se voz ativa, Piper TTS reproduz a resposta
```

---

## Dados do Usuário

Tudo fica em `%APPDATA%\bmo\`:

| Pasta | Conteúdo |
|---|---|
| `config/` | Configurações, chaves de API, secrets |
| `memory/` | Memória persistente (`memory.json`, `MEMORY.md`) |
| `history/` | Histórico de conversas (`history.json`) |
| `workspace/` | Arquivos criados pelo BMO e subagentes |
| `logs/` | Logs do backend (`bmo.log`) |
| `uploads/` | Arquivos enviados pelo usuário |
| `reminders/` | Lembretes agendados |
| `sessions/` | Sessões de subagentes |
| `voices/` | Vozes Piper baixadas |
| `records/` | Gravações de áudio temporárias |

---

## Portas e Rede

| Porta | Serviço |
|---|---|
| `8787` | API HTTP do backend (localhost apenas) |
| `8788` | WebSocket para transcrição (opcional) |

> O BMO não expõe portas para a rede externa. Toda comunicação é local.
