# 🔧 Correções Aplicadas ao Projeto BMO

**Data:** 15 de junho de 2026  
**Status:** ✅ 3 problemas críticos corrigidos

---

## 1️⃣ API Key não era salva persistentemente

### ❌ Problema
- O `secrets.env` não era criado antes da primeira escrita
- Valores vazios poluíam o arquivo
- A API key desaparecia após reiniciar

### ✅ Solução
- **Arquivo:** `backend/bmo_backend.py`
- **Mudanças:**
  - `ensure_bmo_home_layout()` agora cria `~/.bmo/config/secrets.env` com template se não existir
  - `save_env_file()` filtra valores vazios e registra o evento
  - `update_settings()` propaga a chave salva diretamente para `os.environ`
  - Adicionado `nanobot_bridge.invalidate_runtime()` para recarregar config com nova chave

### 📝 Código-chave
```python
# Arquivo criado automaticamente na primeira execução
secrets_path = CONFIG_DIR / "secrets.env"
if not secrets_path.exists():
    secrets_path.write_text("OPENROUTER_API_KEY=\nOPENAI_API_KEY=\n", encoding="utf-8")

# Salva apenas valores não vazios
lines = [f"{key}={value}" for key, value in values.items() if str(value).strip()]
```

---

## 2️⃣ Workspace não gerava SOUL.md, USER.md, AGENTS.md, IDENTITY.md

### ❌ Problema
- O BMO rodava sem contexto de personalidade
- Não havia HEARTBEAT.md para reminders
- O nanobot não encontrava `AGENTS.md` para instrções específicas
- Não havia `IDENTITY.md` para personalidade

### ✅ Solução
- **Arquivo:** `backend/bmo_backend.py`
- **Função nova:** `_ensure_nanobot_workspace_files()`
- **Chamada em:** `ensure_bmo_home_layout()` / inicialização

### 📝 Arquivos criados automaticamente

| Arquivo | Conteúdo |
|---------|----------|
| `AGENTS.md` | Instruções do workspace, regras de comportamento |
| `HEARTBEAT.md` | Vazio por padrão (evita chamadas API desnecessárias) |
| `IDENTITY.md` | Nome, criatura, vibe, emoji do BMO |
| `SOUL.md` | Personalidade, jeito de falar, regras de resposta |
| `USER.md` | Perfil do usuário |
| `memory/MEMORY.md` | Memória persistente |

---

## 3️⃣ Subagentes não executavam de verdade

### ❌ Problema
- `create_subagent_tool()` apenas enfileirava na fila
- Nunca chamava o `AgentLoop` do nanobot
- Subagentes viavam tarefas nunca rodavam

### ✅ Solução
- **Arquivo:** `backend/nanobot_bridge.py`
- **Função nova:** `spawn_subagent()`
- **Como funciona:**
  1. Cria item na fila com status `running`
  2. Inicia thread separada que chama `NanobotRuntime.chat()`
  3. O nanobot executa a tarefa com acesso a todas as tools
  4. Salva resultado em `~/.bmo/workspace/subagents/<id>.md`
  5. Marca como `concluido` e notifica

### 📝 Código-chave
```python
def spawn_subagent(...) -> dict[str, Any]:
    # Registra na fila
    item = {"id": item_id, "status": "running", ...}
    
    def _runner():
        rt = runtime(...)  # Carrega AgentLoop
        result = rt.chat(content=task, ...)  # Executa de verdade!
        # Salva arquivo .md com resultado
        _update_item("concluido", result=result_text, ...)
    
    thread = Thread(target=_runner, daemon=True)
    thread.start()
    return {"ok": True, "id": item_id, ...}
```

### 🔄 Fluxo de execução
```
Frontend ("Crie subagente")
    ↓
create_subagent_tool() [backend]
    ↓
spawn_subagent() [nanobot_bridge]
    ├→ Thread: rt.chat() [AgentLoop real]
    │   ├→ Processa tools nativas (read_file, web_search, etc)
    │   ├→ Usa API key salva em secrets.env
    │   └→ Retorna resultado
    ├→ Salva em ~/.bmo/workspace/subagents/<id>.md
    └→ Frontend notificado ✅
```

---

## 📋 Checklist de Testes

Após abrir o projeto, teste:

- [ ] **API Key**
  - [ ] Cole chave do OpenRouter em "Provedores"
  - [ ] Feche e reabra o BMO
  - [ ] Chave ainda está lá?
  - [ ] Chat funciona sem erros 401?

- [ ] **Workspace**
  - [ ] Verifique `~/.bmo/workspace/`
  - [ ] Existe `SOUL.md`, `USER.md`, `AGENTS.md`, `IDENTITY.md`?
  - [ ] `memory/MEMORY.md` criado?
  - [ ] `HEARTBEAT.md` vazio?

- [ ] **Subagentes**
  - [ ] Chat: "Pesquise sobre IA em 2026"
  - [ ] Painel "Subagentes" mostra task?
  - [ ] Status muda de "running" → "concluido"?
  - [ ] Arquivo `.md` criado em `~/.bmo/workspace/subagents/`?
  - [ ] Resultado aparece na notificação?

---

## 🚀 Como Usar Agora

### 1. Primeira execução
```bash
# BMO cria automaticamente:
# - ~/.bmo/config/secrets.env
# - ~/.bmo/workspace/ com SOUL.md, USER.md, etc
# - ~/.bmo/memory/ com histórico
```

### 2. Configurar API Key
1. Abra BMO
2. Painel "Provedores"
3. Cole chave do OpenRouter
4. Clique "Salvar"
5. Chave persiste mesmo após reiniciar ✅

### 3. Criar Subagente
1. Chat: _"Pesquise sobre X"_
2. Veja em "Subagentes" rodando em tempo real
3. Resultado salvo automaticamente
4. Notificação quando terminar

---

## 📁 Arquivos Modificados

| Arquivo | Linhas | Mudanças |
|---------|--------|----------|
| `backend/bmo_backend.py` | ~70 | Salvamento de API key, workspace init, spawn subagente |
| `backend/nanobot_bridge.py` | ~150 | Nova função `spawn_subagent()`, `invalidate_runtime()` |

---

## ⚠️ Notas Importantes

1. **Thread-safe:** Subagentes rodam em threads separadas sem bloquear chat
2. **Fallback:** Se nanobot_bridge falhar, volta para runner nativo de pesquisa
3. **Persistent:** Workspace é criado uma vez e reutilizado
4. **Memory:** Cada subagente tem sua própria session_key para contexto isolado

---

## 🐛 Possíveis Próximos Passos

- [ ] Adicionar progresso (0-100%) para subagentes longos
- [ ] Persistir histórico de subagentes concluídos
- [ ] UI para visualizar resultado do subagente
- [ ] Permitir editar SOUL.md/USER.md/IDENTITY.md no painel

---

**Pronto para testar! 🚀**
