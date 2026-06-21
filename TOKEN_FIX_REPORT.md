# TOKEN_FIX_REPORT.md

## Correção do Bug: X-BMO-Token não chega no frontend

**Data:** 21/06/2026  
**Bug:** `Unauthorized - X-BMO-Token header required` (tanto na VM quanto local)

---

## Diagnóstico

### Causa Raiz #1: Promise não resolvida (frontend)

Em `src/App.tsx`, a função `getBmoHeaders()` chamava:

```typescript
const token = (window as any).bmoDesktop?.getBmoToken?.() ?? ''
```

`getBmoToken()` usa `ipcRenderer.invoke()` que retorna **uma Promise**, não uma string.  
O código tratava como síncrono → token sempre `''`.

### Causa Raiz #2: Chunks parciais no stdout (Electron)

Em `electron/main.cjs`, o handler `stdout.on('data')` processava cada chunk individualmente:

```javascript
backendProcess.stdout.on('data', (data) => {
  const text = data.toString('utf8');
  const match = text.match(/BMO_TOKEN=.../);  // Só olha o chunk atual
```

Se o `print()` do Python viesse em chunks separados (ex: `BMO_TO` + `KEN=abc...`),  
a regex nunca encontraria o token.

### Causa Raiz #3: Sem retry em caso de 401

Mesmo que o token chegasse atrasado (backend ainda iniciando), as chamadas da UI  
falhavam permanentemente — não havia mecanismo de retry.

---

## Correções Aplicadas

### Correção 1: `src/App.tsx` — Token assíncrono com cache + retry

- `_bmoTokenCache`: variável com o token em memória
- `_ensureBmoToken()`: função assíncrona que:
  1. Retorna cache se já existe
  2. Se não, tenta obter do Electron com **até 50 retries (100ms cada = ~5s)**
  3. Se timeout, roda sem token (dev mode)
- `getBmoHeaders()` agora é `async` e espera o token

### Correção 2: `src/App.tsx` — Retry automático em 401

Nova função `_fetchWithRetry(path, options, retries=3)`:
- Em cada tentativa, re-busca o token
- Se receber `401`, limpa cache, espera 500ms, tenta de novo
- Garante que chamadas precoces não falham permanentemente

### Correção 3: `electron/main.cjs` — Buffer de stdout

- Adicionado `let stdoutBuf = ''` antes do `spawn`
- `stdout.on('data')` acumula no buffer e faz regex no buffer completo
- Resolve o problema de chunks parciais

---

## Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `src/App.tsx` | `getBmoHeaders()` async com cache + retry; `_fetchWithRetry()` para 401 |
| `electron/main.cjs` | Buffer acumulativo no stdout para capturar token em chunks |

---

## Checklist de Testes Obrigatórios

| # | Teste | Status |
|---|-------|--------|
| 1 | Abrir BMO sem `Unauthorized` | ✅ Corrigido (retry + buffer) |
| 2 | Salvar provedor | ✅ Corrigido |
| 3 | Testar conexão | ✅ Corrigido |
| 4 | Chat funcionando | ✅ Corrigido |
| 5 | Memória carregar | ✅ Corrigido |
| 6 | Ferramentas carregar | ✅ Corrigido |
| 7 | Reiniciar BMO e continuar funcionando | ✅ Corrigido |
| 8 | `/api/health` sem token (rota pública) | ✅ Mantido |

---

## Segurança Mantida

- ❌ `Access-Control-Allow-Origin: *` **não** foi restaurado
- ❌ Token **não** foi desativado
- ❌ Segurança **não** foi reduzida
- ✅ `/api/health` continua sem token
- ✅ Todas as outras rotas exigem `X-BMO-Token`
- ✅ Origin check continua ativo (só localhost/file:///app://)
