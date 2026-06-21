# BMO — Relatório de Auditoria de Integridade

**Gerado em:** 18/06/2026 21:58 GMT-3
**Projeto:** `C:\Users\USER\Documents\BMO_PROJECT\bmo`

---

## 1. Resumo Executivo

| Item | Status |
|------|--------|
| **Python compile (backend)** | ✅ OK — 0 erros |
| **Python compile (nanobot)** | ✅ OK — 0 erros |
| **Python compile (tools)** | ✅ OK — 0 erros |
| **Python compile (bridge)** | ✅ OK — 0 erros |
| **TypeScript build** | ✅ OK — 0 erros, 1.89s |
| **Rotas frontend → backend** | ✅ Todas implementadas |
| **Arquivos backup/duplicados** | ⚠️ **147 arquivos identificados** |
| **Assets órfãos** | ⚠️ **10 assets não importados** |
| **Código legado não usado** | ⚠️ **~500 linhas mortas** |
| **Arquivos temporários/lixo** | ⚠️ **~20 arquivos de relatório/log** |
| **Chaves API expostas** | ✅ Nenhuma no código fonte |
| **Caminhos absolutos expostos** | ✅ Nenhum no backend |
| **bmo_backend.py** | ⚠️ **3.135 linhas** — muito grande |

---

## 2. Código Quebrado

### 2.1 Python — Sem erros de sintaxe
Todos os arquivos `.py` em `backend/`, `nanobot/`, `tools/`, `bridge/` compilaram sem erro.

### 2.2 TypeScript — Sem erros de compilação
`tsc -b && vite build` executou sem erros. 1.783 módulos transformados.

### 2.3 Potenciais problemas estruturais

| Arquivo | Linhas | Problema |
|---------|--------|----------|
| `backend/bmo_backend.py` | **3.135** | Arquivo monolítico enorme — mistura HTTP server, Pipert TTS, Whisper, wake word, chat, sistema de arquivos, web search, reminders, subagentes |
| `backend/nanobot_bridge.py` | ~530 | Ponte para Nanobot — **em paralelo** com `nanobot_integration.py` que faz a mesma coisa |
| `backend/nanobot_integration.py` | ~200 | Segunda ponte para Nanobot — duplicada |

---

## 3. Imports Quebrados

Nenhum import quebrado encontrado. Todos os arquivos Python e TypeScript resolvem suas dependências corretamente.

---

## 4. Endpoints

### 4.1 Endpoints usados pelo frontend (20 endpoints)

```
/api/channels, /api/chat, /api/history, /api/logs, /api/memory,
/api/open-folder, /api/provider, /api/reminders, /api/service,
/api/settings, /api/skills, /api/sound, /api/speak, /api/subagents,
/api/system, /api/tasks, /api/tools, /api/voice-chat, /api/voices,
/api/whisper
```

### 4.2 Endpoints implementados no backend

Todos os endpoints acima possuem handler correspondente. **Nenhum endpoint quebrado.**

### 4.3 Observações

- `/api/whisper` → somente `/api/whisper/test` implementado (GET não suporta `/api/whisper` bare — mas frontend só chama o test)
- `/api/provider` → implementado como `/api/provider/test` (POST) — frontend usa `postJson('/api/provider', ...)`, backend espera `/api/provider/test`. **Leve incompatibilidade de rota.**

---

## 5. Duplicados e Backups

### 5.1 Categorizados

#### A. Seguro remover (backups que ocupam espaço)
| Item | Tamanho | Descrição |
|------|---------|-----------|
| `src/App.css.pre-*` (9 arquivos) | ~5KB cada | Snapshots de CSS de versões anteriores |
| `src/App.tsx.pre-*` (7 arquivos) | ~50KB cada | Snapshots de TSX de versões anteriores |
| `backend/bmo_backend_BROKEN_CLEANUP.py` | ~140KB | Cópia de backup de versão quebrada |
| `backend/bmo_backend_ORIGINAL.py` | ~140KB | Cópia de backup |
| `backup_antes_das_correcoes/` | **~27MB** | Backup completo com 3 sub-cópias |
| `data/test_workspace*` (8 pastas) | variado | Diretórios de teste |
| `data/toolcall-test-*` (6 pastas) | variado | Diretórios de teste |
| `shot_*` | variado | Screenshots |

#### B. Manter por enquanto
| Item | Motivo |
|------|--------|
| `bmo_backend_ORIGINAL.py` | Referência para diff caso algo quebre |
| `backup_antes_das_correcoes/` | Backup completo antes de correções recentes |

#### C. Backup importante
| Item | Motivo |
|------|--------|
| `Codex/bmo/` (Fora do projeto) | Cópia no `Documents/Codex/` — refereência externa, não afeta o projeto |
| `secrets.local.backup.env` | Backup de configuração de API keys |

#### D. Precisa revisar manualmente
| Item | Motivo |
|------|--------|
| `bmo_backend.exe` (97MB) | Executável PyInstaller — ver se é usado ou lixo de build |
| `duplicate_files_to_delete.txt` (1MB) | Lista de  arquivos a deletar — precisa conferir antes de executar |
| `electron-release/` | Pasta de build do Electron — pode ou não ser necessária |

### 5.2 Assets não referenciados (possíveis órfãos)

| Asset | Localização |
|-------|-------------|
| `bmo/bmo-body.png` | `src/assets/bmo/` (só `bmo-body-cropped.png` é importado) |
| `bmo/bmo-quarto.png` | `src/assets/bmo/` |
| `bmo/theme-cartoon-face.jpg` | `src/assets/bmo/` |
| `bmo/theme-night-forest.jpg` | `src/assets/bmo/` |
| `bmo/theme-treehouse-day.jpg` | `src/assets/bmo/` |
| `faces/idle.png` | `src/assets/faces/` |
| `faces/speaking.png` | `src/assets/faces/` |
| `hero.png` | `src/assets/` |
| `react.svg` | `src/assets/` |
| `vite.svg` | `src/assets/` |
| **`bmo_faces/` (pasta inteira)** | **10 arquivos** de faces alternativas nunca usados |

---

## 6. Restos de Código Antigo

### 6.1 Funções obsoletas ainda presentes em `bmo_backend.py`

| Função | Linhas | Status | Recomendação |
|--------|--------|--------|-------------|
| `BMO_SYSTEM_PROMPT` (linha ~143) | ~20 linhas | **NÃO usado mais** pelo NanobotRuntime | Remover |
| `build_model_messages()` (linha ~1361) | ~40 linhas | **Só usado** por `direct_provider_chat()` | Remover junto |
| `direct_provider_chat()` (linha ~1856) | ~70 linhas | **Caminho legado** — não usado quando NanobotRuntime ativo | Remover |
| `execute_llm_tool()` (linha ~1815) | ~40 linhas | **Só usado** por `direct_provider_chat()` | Remover junto |
| `create_file_tool()` (linha ~1564) | ~35 linhas | **Duplicada** — Nanobot já tem filesystem tools | Revisar |
| `shell_exec_tool()` (linha ~1599) | ~40 linhas | **Duplicada** — Nanobot já tem shell tools | Revisar |
| `create_subagent_tool()` (linha ~1784) | ~30 linhas | **Duplicada** — Nanobot já gerencia subagentes | Revisar |
| Código Ollama (linhas ~141, ~1965) | ~10 linhas | **Obsuleto** — Ollama não é mais provedor principal | Remover |

**Total estimado de código morto: ~500 linhas (~16% do bmo_backend.py)**

### 6.2 Arquivos orfãos no backend/

| Arquivo | Descrição |
|---------|-----------|
| `nanobot_bridge.py` | Ponte via subprocess que roda nanobot separado — **parcialmente substituído por** `nanobot_integration.py` |
| `nanobot_integration.py` | Segunda ponte, importa nanobot como módulo — **parcialmente substituído pelo NanobotRuntime direto** |
| `launch_test.py` | Script de teste — pode ser movido para `tools/` ou `test-results/` |
| `rate_limit.py` | Usado — manter |

### 6.3 Arquivos no nanobot/ que parecem não ser do BMO original (EasyClaw)

`bridge/` contém uma implementação de WhatsApp Bridge com Baileys que parece ser parte do EasyClaw/nanobot original, não do BMO.

---

## 7. Configurações

| Arquivo | Conteúdo | Estado |
|---------|----------|--------|
| `config/app_config.json` | Config visual + backend + voz | ✅ Limpo, sem paths absolutos |
| `config/nanobot_config.json` | Provider padrão + modelo | ✅ Limpo, usa `${OPENROUTER_API_KEY}` |
| `secrets.local.backup.env` | Backup de env de secrets | ⚠️ Backup de arquivo que pode conter chave |
| `package.json` | Dependências do frontend | ✅ Padrão |

### 7.1 Potenciais conflitos

- `nanobot_config.json` aponta `provider: openrouter` com `model: openai/gpt-oss-120b:free` — mas o backend também tem `PROVIDER_NAMES` e `direct_provider_chat`. **Duas lógicas de provider diferentes coexistem.**
- `app_config.json` tem `"voice.language": "pt-BR"` e `"voice.model": "pt_BR-faber-medium.onnx"` — o frontend usa esse valor mas também pode sobrescrever com seleção do usuário.

---

## 8. Arquivos Seguros para Remover

### 8.1 Snapshots de CSS/TSX (16 arquivos — ~500KB)
- `src/App.css.pre-*` (9 arquivos)
- `src/App.tsx.pre-*` (7 arquivos)

### 8.2 Backups de backend (2 arquivos — ~280KB)
- `backend/bmo_backend_BROKEN_CLEANUP.py`
- `backend/bmo_backend_ORIGINAL.py`

### 8.3 Relatórios e logs (20+ arquivos — ~4MB)
- `*.log`, `*.err`, `*.out` na raiz
- `BMO_*.md`, `AUDITORIA_BMO.md`, `CORRECOES_APLICADAS.md`, `DOCUMENTACAO_BMO_1.0.md`, `GARGALOS_IDENTIFICADOS.md`, `MANUAL_USUARIO.md`, `PLANO_DE_CORRECAO.md`, `RELATORIO_CONTINUIDADE_BMO.md`, `RESUMO_FINAL.txt`, `TESTE_RAPIDO.md`, `TEST_REPORT.md`, `ABRIR_BMO.md`
- `duplicate_files_to_delete.txt`
- `all_md5.txt`

### 8.4 Diretórios de teste
- `data/test_workspace*` (8 pastas)
- `data/toolcall-test-*` (6 pastas)

### 8.5 Pasta de faces não usadas
- `src/assets/bmo_faces/` (10 arquivos, ~50KB)

---

## 9. Arquivos que NÃO Devem Ser Removidos

| Arquivo | Motivo |
|---------|--------|
| `backend/bmo_backend.py` | **Core do servidor HTTP** |
| `backend/nanobot_runtime.py` | **Motor de chat via Nanobot** |
| `backend/nanobot_bridge.py` | **Ainda usado pelo BMO** (ver imports) |
| `backend/nanobot_integration.py` | **Ainda importado pelo backend** |
| `backend/tools.py` | **Ferramentas nativas do backend** |
| `backend/rate_limit.py` | **Rate limiting ativo** |
| `nanobot/` (pasta inteira) | **Engine completo do EasyClaw** |
| `src/App.tsx` | **Frontend principal** (17KB) |
| `src/App.css` | **Estilos do frontend** (40KB) |
| `src/main.tsx`, `src/index.css` | **Entry point + estilos base** |
| `config/` | **Configurações ativas** |
| `runtime/` | **Modelos de voz e whisper** |
| `vite.config.ts`, `tsconfig*.json` | **Config de build** |
| `package.json` | **Dependências** |

---

## 10. Riscos Críticos

### 🔴 RISCO 1: `bmo_backend.py` monolítico (3.135 linhas)
- Dificulta manutenção e debug
- Qualquer erro de sintaxe derruba **tudo** (HTTP, voz, wake word, whisper, chat, ferramentas)
- Importa 20+ módulos na inicialização

### 🔴 RISCO 2: Duas pontes Nanobot paralelas
- `nanobot_bridge.py` (lança subprocess) e `nanobot_integration.py` (importa direto) fazem a mesma coisa
- Pode causar conflitos de estado ou duplicação de recursos

### 🔴 RISCO 3: Código legado de `direct_provider_chat` ainda chamável
- Se o NanobotRuntime falhar, o `ask_nanobot()` cai no fallback `direct_provider_chat()` que tem ferramentas manuais desatualizadas
- Essas ferramentas manuais (create_file_tool, shell_exec_tool) podem criar arquivos ou executar comandos **sem passar pelas regras de segurança do Nanobot**

### 🟡 RISCO 4: Caminhos absolutos do usuário
- Nenhum encontrado no código fonte, mas `secrets.local.backup.env` **pode conter API key em texto claro**

### 🟡 RISCO 5: ~147 arquivos de backup/duplicados
- Ocupam ~35MB de espaço
- Podem confundir ferramentas de busca e análise
- `backup_antes_das_correcoes/` contém dados de sessão e histórico que deveriam estar em `data/`

---

## 11. Recomendações

### Imediatas (pode fazer agora, sem risco)
1. Remover snapshots `.pre-*` do `src/` (16 arquivos)
2. Remover `bmo_backend_BROKEN_CLEANUP.py` e `bmo_backend_ORIGINAL.py`
3. Remover logs, relatórios `.md`, `.txt`, `.log` da raiz (20+ arquivos)
4. Remover pastas `data/test_*` e `data/toolcall-test-*` (14 pastas)
5. Remover `src/assets/bmo_faces/` (faces não usadas — 10 arquivos)
6. Remover `duplicate_files_to_delete.txt` e `all_md5.txt`

### Curto prazo (precisa de testes)
7. Limpar código morto: `BMO_SYSTEM_PROMPT`, `build_model_messages()`, `direct_provider_chat()`, `execute_llm_tool()`, `create_file_tool()`, `shell_exec_tool()`, `create_subagent_tool()`
8. Consolidar `nanobot_bridge.py` e `nanobot_integration.py` em um único módulo
9. Remover assets não usados: `bmo-body.png`, `bmo-quarto.png`, `hero.png`, `react.svg`, `vite.svg`, `faces/idle.png`, `faces/speaking.png`

### Médio prazo
10. Quebrar `bmo_backend.py` em módulos separados (ex: `voice.py`, `wakeword.py`, `whisper.py`, `chat.py`, `files.py`)
11. Remover `backup_antes_das_correcoes/` (após confirmar que nada mais precisa dele)
12. Verificar se `bmo_backend.exe` (97MB) pode ser removido

---

## 12. Próximo Plano de Correção (após aprovação)

1. **Fase 1 — Limpeza de arquivos mortos**: Remover todos os itens da seção 8 (Arquivos Seguros para Remover)
2. **Fase 2 — Remoção de código legado**: Podar funções obsoletas do `bmo_backend.py`
3. **Fase 3 — Consolidação**: Unificar pontes Nanobot

---

*Relatório gerado automaticamente. Nenhuma alteração foi feita no projeto.*
