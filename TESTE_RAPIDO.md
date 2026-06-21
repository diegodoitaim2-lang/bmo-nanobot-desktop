# 🧪 Teste Rápido das Correções

Execute este checklist para validar que tudo funciona:

---

## ✅ Teste 1: API Key Persiste

**Passo a passo:**

1. Abra o BMO
2. Clique em **"Provedores"**
3. Cole sua chave do OpenRouter
4. Clique **"Salvar"**
5. Aguarde a confirmação
6. **Feche completamente o BMO** (X na janela)
7. **Reabra o BMO**
8. Volte em **"Provedores"**

**Resultado esperado:**
- ✅ Chave ainda está lá (mascarada)
- ✅ Chat funciona sem erros 401

**Se der errado:**
```bash
# Verificar arquivo
cat ~/.bmo/config/secrets.env
# Deve conter: OPENROUTER_API_KEY=sua_chave_aqui
```

---

## ✅ Teste 2: Workspace Inicializado

**Passo a passo:**

```bash
# Abra PowerShell e rode:
ls -Recurse "$env:USERPROFILE\.bmo\workspace" -Include "*.md"
```

**Resultado esperado:**
```
~/.bmo/workspace/SOUL.md         ✅
~/.bmo/workspace/USER.md         ✅
~/.bmo/workspace/AGENTS.md       ✅
~/.bmo/workspace/IDENTITY.md     ✅
~/.bmo/workspace/HEARTBEAT.md    ✅
~/.bmo/workspace/memory/MEMORY.md ✅
```

**Se der errado:**
- Verifique se `~/.bmo/workspace/` existe
- Se não existir, abra o BMO para criar

---

## ✅ Teste 3: Subagentes Funcionam

**Passo a passo:**

1. No chat do BMO, digite:
   ```
   Pesquise informações sobre o modelo GPT-4 e resuma em 3 pontos
   ```

2. Clique em **"Subagentes"** no painel lateral

3. **Aguarde** a tarefa processar (pode levar 10-30 segundos)

4. Observe:
   - Status muda de "running" → "concluido"
   - Arquivo criado em `~/.bmo/workspace/subagents/`

**Resultado esperado:**
```
✅ ID do subagente aparece
✅ Status: "concluido"
✅ Resultado salvo em arquivo .md
✅ Notificação no sistema
```

**Se der errado:**
- Verifique se API key está salva (Teste 1)
- Veja logs em: `~/.bmo/logs/`
- Verifique se `~/.bmo/workspace/subagents/` foi criado

---

## 🔍 Validação Completa

Se todos os 3 testes passarem:

```
✅ API key salva e recarregada
✅ Workspace inicializado com arquivos necessários
✅ Subagentes executam via AgentLoop do nanobot
✅ Projeto 100% funcional!
```

---

## 📍 Locais Importantes

| Arquivo | Localização |
|---------|------------|
| Configurações | `~/.bmo/config/app_config.json` |
| Secrets | `~/.bmo/config/secrets.env` |
| Workspace | `~/.bmo/workspace/` |
| Logs | `~/.bmo/logs/` |
| Memória | `~/.bmo/memory/` |
| Subagentes | `~/.bmo/workspace/subagents/` |

**Nota:** `~/.bmo/` é o diretório home do BMO (usually `C:\Users\USER\.bmo\`)

---

## 🐛 Se Precisar Debugar

```bash
# Ver logs do backend
tail -f ~/.bmo/logs/backend.log

# Ver logs do Electron
tail -f ~/.bmo/logs/main.log

# Limpar cache (se tiver problemas)
rm -r ~/.bmo/config/nanobot_runtime_config.json
# (vai ser recriado na próxima execução)

# Ver estrutura do workspace
tree ~/.bmo/workspace/
```

---

**Testes completados com sucesso? 🎉**

Então o projeto está **100% pronto para usar!**
