# Relatório: Análise das Pontes Nanobot

**Data:** 19/06/2026 02:06 GMT-3
**Projeto:** `backend/` do BMO

---

## Arquivo 1: `nanobot_runtime.py` (760 linhas)

**Implementação completa do NanobotRuntime como Singleton.** Gerencia AgentLoop, ferramentas, memória, cron, subagentes. Usa `asyncio` em thread separada.

### 1. Quem usa
- **`nanobot_integration.py`** — importa e chama `nr.NanobotRuntime.initialize()`, `nr.NanobotRuntime.reset()`, `_runtime.chat()`, `_runtime.definitions()`, `_runtime.execute_tool()`, `_runtime.tool_names`

### 2. Quem importa
- **Apenas `nanobot_integration.py`** (linha: `from backend import nanobot_runtime as nr`)

### 3. Ativo em runtime?
**✅ Sim.** Inicializado via `nanobot_integration.initialize_runtime()` que é chamado:
1. Na inicialização do backend (thread `NanobotInit` em `bmo_backend.py` linha 3135)
2. Lazy na primeira chamada de `nanobot_integration.chat()` (linha 2006)

### 4. Morto?
**❌ Não.** É o motor ativo.

### 5. Duplica funcionalidade?
**É a implementação mais recente e completa.** Não duplica — as outras duas são versões anteriores.

---

## Arquivo 2: `nanobot_bridge.py` (530 linhas)

**Primeira implementação da ponte Nanobot.** Usa função `runtime()` com cache por fingerprint. Expõe funções utilitárias (execute_tool, registry_payload, memory_payload, channels_payload, spawn_subagent, etc.).

### 1. Quem usa
- **`bmo_backend.py`** — chamadas diretas para:
  - `nanobot_bridge.execute_tool()` → `nanobot_original_tool()` (usado em handlers de arquivo)
  - `nanobot_bridge.registry_payload()` → `nanobot_original_registry()` (usado em `/api/nanobot/tools`)
  - `nanobot_bridge.tool_info()` → `nanobot_original_info()` (usado em `/api/tools/info`)
  - `nanobot_bridge.memory_payload()` → `nanobot_original_memory()` (usado em `/api/memory`)
  - `nanobot_bridge.append_history()` → `nanobot_original_append_history()` (usado ao salvar histórico)
  - `nanobot_bridge.channels_payload()` → direto em `channels_list()` (para listar canais)
  - `nanobot_bridge.spawn_subagent()` → dentro de `create_subagent_tool()` (DEPRECATED mas ainda chamado por subagentes)
  - `nanobot_bridge.invalidate_runtime()` → em `save_settings()` (reload de config)

### 2. Quem importa
- **Apenas `bmo_backend.py`** (linha 29: `import nanobot_bridge`)

### 3. Ativo em runtime?
**✅ Sim, ativamente.** Toda chamada a `nanobot_original_tool()`, `nanobot_original_registry()`, etc. passa por ele. Também usado para listar canais e criar subagentes.

### 4. Morto?
**❌ Não.** Mesmo sendo a implementação mais antiga, ainda é chamada por vários caminhos no `bmo_backend.py`.

### 5. Duplica funcionalidade?
**Sim, com `nanobot_integration.py`.** Ambos fazem a mesma coisa fundamental (inicializar NanobotRuntime e expor chat + tools), mas:
- `nanobot_bridge` → cache por fingerprint, API funcional (execute_tool, registry_payload, etc.), roda em subprocess-style
- `nanobot_integration` → singleton inicializado uma vez na thread principal, mais simples, foco em chat

**Diferença crítica:** `nanobot_bridge` é usado para **operações internas** (tools, memória, canais, subagentes), enquanto `nanobot_integration` é usado **apenas para chat**. Ambos criam suas próprias instâncias do NanobotRuntime — **duas instâncias do mesmo motor podem coexistir**.

---

## Arquivo 3: `nanobot_integration.py` (210 linhas)

**Segunda implementação, mais enxuta.** Usa singleton do `NanobotRuntime` de `nanobot_runtime.py`. Foco em `chat()` + `runtime_status()`. Camada fina entre `bmo_backend.py` e `nanobot_runtime.py`.

### 1. Quem usa
- **`bmo_backend.py`** — chamadas para:
  - `nanobot_integration.chat()` → dentro de `ask_nanobot()` (chat principal)
  - `nanobot_integration.runtime_status()` → em `system_status()` (status do sistema)
  - `nanobot_integration.tool_names()` → em `system_status()` (lista de tools)
  - `nanobot_integration.initialize_runtime()` → na inicialização (thread `NanobotInit`)

### 2. Quem importa
- **Apenas `bmo_backend.py`** (linha 31: `import nanobot_integration`)

### 3. Ativo em runtime?
**✅ Sim.** É a via de chat principal. `ask_nanobot()` chama `nanobot_integration.chat()`.

### 4. Morto?
**❌ Não.** É a via ativa de chat e a "oficial" no fluxo `ask_nanobot()`.

### 5. Duplica funcionalidade?
**Sim, com `nanobot_bridge.py`** — ambos importam e usam `NanobotRuntime`, mas oferecem APIs diferentes:
- `nanobot_integration` → chat + status
- `nanobot_bridge` → tools + registry + memory + channels + subagents

---

## Fluxo Real em Produção

```
App.tsx (frontend)
  │
  │ fetch /api/chat ──POST──→  bmo_backend.py::handle_chat()
  │                              │
  │                              ├── process_chat_attachments()
  │                              ├── remember_profile_from_message()
  │                              ├── create_reminder_from_message()
  │                              ├── create_file_from_message()
  │                              ├── create_python_game_from_message()
  │                              ├── create_subagent_from_message()
  │                              │       └── create_subagent_tool()  ──→  nanobot_bridge.spawn_subagent()
  │                              │
  │                              └── ask_nanobot() ←── VIA ÚNICA DE RESPOSTA
  │                                      │
  │                                      └── nanobot_integration.chat()
  │                                              │
  │                                              └── NanobotRuntime (nanobot_runtime.py)
  │                                                      │
  │                                                      └── AgentLoop process_direct()
  │                                                              │
  │                                                              └── Nanobot (ferramentas, skills, provedor)
  │
  │ fetch /api/tools ──GET───→  bmo_backend.py
  │                              └── nanobot_original_registry()  ──→  nanobot_bridge.registry_payload()
  │
  │ fetch /api/memory ──GET───→  bmo_backend.py
  │                              └── nanobot_original_memory()  ──→  nanobot_bridge.memory_payload()
  │
  │ fetch /api/channels ──GET──→  bmo_backend.py
  │                              └── nanobot_bridge.channels_payload()
  │
  │ fetch /api/settings ──POST─→  bmo_backend.py
  │                              └── save_settings()
  │                                   └── nanobot_bridge.invalidate_runtime()
  │
  │ fetch /api/nanobot/tools ─GET→ bmo_backend.py
  │                              └── nanobot_original_registry()
```

---

## Sumário

| Arquivo | Linhas | Importado por | Usado para | Pode remover? | 
|---------|--------|---------------|------------|---------------|
| `nanobot_runtime.py` | 760 | `nanobot_integration.py` | Engine real do Nanobot | **❌ Não — core** |
| `nanobot_integration.py` | 210 | `bmo_backend.py` | Chat principal + status | **❌ Não — via de chat** |
| `nanobot_bridge.py` | 530 | `bmo_backend.py` | Tools, memória, canais, subagentes | **⚠️ Parcialmente — 5 usos** |

### Observações

1. **`nanobot_integration` e `nanobot_bridge` duplicam** a inicialização do NanobotRuntime. Ambos criam instâncias separadas do mesmo motor. Cada um carrega config, tools e memória independentemente.

2. **`nanobot_bridge` é mais usado que `nanobot_integration` em número de chamadas** (8 pontos de uso vs 4), mas o mais crítico (chat) passa por `nanobot_integration`.

3. **Consolidar** exigiria:
   - Fazer `nanobot_integration` expor também tools, memory, channels (hoje só faz chat/status)
   - Redirecionar as 8 chamadas de `nanobot_bridge` para `nanobot_integration`
   - Remover `nanobot_bridge` depois

4. **Não recomendado fazer agora** — há muitas dependências. Precisa de refatoração cuidadosa.
