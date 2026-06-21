# NANOBOT_RUNTIME_UNIFICATION.md — Proposta de Runtime Único

**Data:** 19/06/2026 02:09 GMT-3
**Status:** Proposta — nenhuma alteração foi feita

---

## 1. Problema

Existem **duas instâncias independentes** do NanobotRuntime:

| Runtime | Gerenciado por | Usado para |
|---------|---------------|------------|
| **Runtime A** | `nanobot_integration.py` | Chat (`ask_nanobot`) + status |
| **Runtime B** | `nanobot_bridge.py` | Tools, memória, canais, subagentes |

Cada um carrega config, tools, memória e agent loop separadamente — dobra o tempo de inicialização e consome 2x recursos.

---

## 2. Fluxo Atual

```
bmo_backend.py
│
├── nanobot_integration.py (modulo singleton)
│   ├── _runtime = nr.NanobotRuntime.initialize(...)  ← INSTANCIA #1
│   │      ├── Carrega config
│   │      ├── Carrega tools (ToolLoader)
│   │      ├── Cria AgentLoop
│   │      └── Cria MemoryStore
│   │
│   ├── chat() → _runtime.chat()            ← Chat principal
│   ├── runtime_status() → _runtime.status()
│   └── tool_names() → _runtime.tool_names
│
└── nanobot_bridge.py (funcoes utilitarias)
    ├── _RUNTIME = NanobotRuntime(paths, env) ← INSTANCIA #2
    │      ├── Carrega config               ← REPETIDO
    │      ├── Carrega tools (ToolLoader)   ← REPETIDO
    │      ├── Cria AgentLoop               ← REPETIDO
    │      └── Cria MemoryStore             ← REPETIDO
    │
    ├── execute_tool()   → _RUNTIME.execute()
    ├── registry_payload() → _RUNTIME.definitions()
    ├── tool_info()      → registry_payload()
    ├── memory_payload() → _RUNTIME.memory_store
    ├── append_history() → _RUNTIME.memory_store
    ├── spawn_subagent() → _RUNTIME.chat()
    └── channels_payload() → import nanobot.channels (lightweight, sem runtime)
```

**Cada chamada que passa por `nanobot_bridge.runtime()` verifica fingerprint e pode recriar o runtime.**

---

## 3. Mapeamento Detalhado

### 3.1 Quem instancia

| Arquivo | Variável | Método de criação | Cache |
|---------|----------|-------------------|-------|
| `nanobot_runtime.py` | `NanobotRuntime._instance` | `NanobotRuntime.initialize()` | Singleton (cls._instance) |
| `nanobot_integration.py` | `_runtime` | `nr.NanobotRuntime.initialize()` | Usa singleton de nanobot_runtime |
| `nanobot_bridge.py` | `_RUNTIME` | `NanobotRuntime(paths, env)` | Cache por fingerprint |
| `nanobot_bridge.py` | — | `runtime()` (função) | Cria `NanobotRuntime()` diretamente (NAO usa singleton de nanobot_runtime) |

### 3.2 Quem mantém cache

- **`nanobot_integration.py`**: Variável global `_runtime` (inicializada uma vez, nunca recriada)
- **`nanobot_bridge.py`**: Variável global `_RUNTIME` + `_FINGERPRINT` (recria se config mudar)
- **`nanobot_runtime.py`**: `NanobotRuntime._instance` (reset manual via `NanobotRuntime.reset()`)

### 3.3 Quem recarrega config

- **`nanobot_integration.py`**: `initialize_runtime()` — carrega config uma vez, depois mantém
- **`nanobot_bridge.py`**: `runtime()` — verifica fingerprint (mtime do config) e recria se mudou
- **`bmo_backend.py`**: `save_settings()` chama `nanobot_bridge.invalidate_runtime()` + `nanobot_integration.initialize_runtime()` para reinicializar ambos

### 3.4 Quem carrega tools

- Ambos os runtimes carregam `ToolLoader().load(ctx, registry, scope="core")` usando `ToolRegistry`. Cada runtime tem seu próprio registry independente.

### 3.5 Quem carrega memória

- Ambos criam `MemoryStore(workspace)`. Cada runtime aponta para o mesmo workspace, mas instâncias separadas podem ter estados divergentes.

---

## 4. Fluxo Proposto

```
nanobot_runtime.py (NOVO — agrega tudo)
│
└── NanobotRuntime (Singleton)
    ├── initialize()          ← chamado UMA vez
    ├── chat()                ← ask_nanobot
    ├── execute_tool()        ← tools
    ├── definitions()         ← registry
    ├── tool_info()           ← info de tool
    ├── memory_store          ← memória
    ├── append_history()      ← histórico
    ├── tool_names()          ← lista de tools
    ├── spawn_subagent()      ← subagentes
    ├── channels_list()       ← canais (leve, sem runtime)
    └── invalidate()          ← recarregar config

bmo_backend.py
│
└── interface unificada (funcoes em nanobot_integration.py)
    ├── chat() → runtime.chat()
    ├── execute_tool() → runtime.execute_tool()
    ├── registry_payload() → runtime.definitions()
    ├── memory_payload() → runtime.memory_store
    ├── append_history() → runtime.append_history()
    ├── tool_names() → runtime.tool_names
    ├── runtime_status() → runtime.is_ready
    └── spawn_subagent() → runtime.spawn_subagent()
```

---

## 5. Arquivos Envolvidos

### Serão modificados (4 arquivos)

| Arquivo | O que muda |
|---------|------------|
| `backend/nanobot_runtime.py` | Adicionar métodos: `execute_tool()`, `definitions()`, `tool_info()`, `append_history()`, `spawn_subagent()`, `invalidate()` |
| `backend/nanobot_integration.py` | Adicionar wrappers para tools, memory, subagents que usam o mesmo Singleton do `nanobot_runtime.py` |
| `backend/bmo_backend.py` | Redirecionar `nanobot_original_tool()`, `nanobot_original_registry()`, `nanobot_original_memory()`, `nanobot_original_append_history()`, `create_subagent_tool()` e `channels_list()` para `nanobot_integration` em vez de `nanobot_bridge` |

### Não serão modificados (apenas removidos do fluxo)

| Arquivo | Destino |
|---------|---------|
| `backend/nanobot_bridge.py` | Removido do fluxo ativo. Mantido como backup por 30 dias |

---

## 6. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Singleton não thread-safe | Baixa | Médio | Já usa `threading.Lock()` |
| `invalidate_runtime()` do bridge não propaga para integração | Média | Alto | Unificar `invalidate()` no runtime |
| `create_subagent_tool()` ainda existe como DEPRECATED e chama bridge | Média | Baixo | Redirecionar para integration |
| Channels usa `pkgutil.iter_modules` sem runtime — não depende | Nenhum | Nenhum | Manter em integration, sem runtime |
| `ensure_runtime_config()` gera config temporária a cada chamada | Média | Baixo | Manter em `bmo_backend.py`, não tem a ver com runtime |

---

## 7. Plano de Migração (6 etapas sequenciais)

### Etapa 1 — Adicionar métodos ao `nanobot_runtime.py`
Adicionar ao `NanobotRuntime`:
- `execute_tool(name, params)` — já existe na classe, mas é método privado. Tornar público.
- `append_history(text)` — delegar para `self.memory_store.append_history()`
- `spawn_subagent(task, label)` — delegar para `_BmoSubagentAdapter.spawn()`
- `channels_list()` — importar nanobot.channels (leve)
- `invalidate()` — fazer `reset()` + `initialize()`
- `tool_info(name)` — buscar em `self.definitions()`

**Duração estimada:** ~30 min
**Risco:** Baixo — só adiciona métodos novos

### Etapa 2 — Expandir `nanobot_integration.py`
Adicionar wrappers que usam **a mesma instância** do runtime (já é o caso hoje!):
- `execute_tool()` → `_runtime.execute_tool()`
- `append_history()` → `_runtime.append_history()`
- `spawn_subagent()` → `_runtime.spawn_subagent()`
- `channels_list()` → `_runtime.channels_list()`
- `tool_info()` → `_runtime.tool_info()`

**Duração estimada:** ~15 min
**Risco:** Baixo — só adiciona funções que delegam

### Etapa 3 — Redirecionar `bmo_backend.py` para `nanobot_integration`
Mudar as funções `nanobot_original_*` para chamar `nanobot_integration` em vez de `nanobot_bridge`:
- `nanobot_original_tool()` → `nanobot_integration.execute_tool()`
- `nanobot_original_registry()` → `nanobot_integration.definitions()`
- `nanobot_original_memory()` → `nanobot_integration.memory()`
- `nanobot_original_append_history()` → `nanobot_integration.append_history()`
- `create_subagent_tool()` → `nanobot_integration.spawn_subagent()` (em vez do bridge)
- `channels_list()` → `nanobot_integration.channels_list()`

**Duração estimada:** ~20 min
**Risco:** Médio — testar cada endpoint depois

### Etapa 4 — Testar integração
- Backend inicia sem erro (thread NanobotInit)
- Chat funciona (ask_nanobot → nanobot_integration.chat)
- Tools listam (/api/tools)
- Tools info funciona (/api/tools/info/read)
- Ferramentas executam (escrever arquivo)
- Memória carrega (/api/memory)
- Histórico salva
- Subagentes criam
- Canais listam
- Config salva e runtime recarrega

**Duração estimada:** ~30 min
**Risco:** Médio

### Etapa 5 — Remover `nanobot_bridge.py` do fluxo (NÃO deletar)
- Mover para `backend/_deprecated/nanobot_bridge.py` ou apenas marcar com comentário
- `bmo_backend.py` não importa mais `nanobot_bridge`

**Duração estimada:** ~5 min
**Risco:** Baixo — se algo quebrar, só restaurar o import

### Etapa 6 — Backup e limpeza
- Manter `nanobot_bridge.py` no lugar por 30 dias como fallback de emergência
- Remover depois da confirmação de que tudo funciona

---

## 8. Checklist de Migração

- [ ] Etapa 1: `nanobot_runtime.py` expandido
- [ ] Etapa 2: `nanobot_integration.py` expandido
- [ ] Etapa 3: `bmo_backend.py` redirecionado
- [ ] Etapa 4: Testes passam
- [ ] Etapa 5: `nanobot_bridge.py` aposentado
- [ ] Etapa 6: Backup mantido por 30 dias

---

## 9. Resumo

| Métrica | Atual | Proposto |
|---------|-------|----------|
| Instâncias do NanobotRuntime | 2 | 1 |
| Arquivos de ponte | 3 (`runtime` + `integration` + `bridge`) | 2 (`runtime` + `integration`) |
| Carregamentos de config | 2x (um por runtime) | 1x |
| Carregamentos de tools | 2x | 1x |
| Estado de memória | 2 instâncias (divergência possível) | 1 instância |
| Manutenção | Difícil (lógica espalhada) | Fácil (tudo via integration) |
| Risco da migração | — | Baixo-Médio (testável etapa por etapa) |
