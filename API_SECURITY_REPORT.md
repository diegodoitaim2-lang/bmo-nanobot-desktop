# API_SECURITY_REPORT.md

## Hardening da API do BMO

**Data:** 20/06/2026

---

## ✅ Implementado

### 1. Token de autenticação local
- **Geração:** `secrets.token_hex(32)` na inicialização do backend (64 caracteres hex)
- **Header:** `X-BMO-Token` obrigatório em todas as requests
- **Exceção:** Apenas `/api/health` não exige token (para healthcheck)

### 2. Restrição de Origin
- Apenas origens locais são permitidas:
  - `http://localhost`
  - `http://127.0.0.1`
  - `file://` (Electron em produção)
  - `app://` (sandbox Electron)
- Qualquer Origin externo é rejeitado e substituído por `http://localhost`

### 3. Integração com Electron
- Backend **printa** `BMO_TOKEN=<hex>` no stdout ao iniciar
- Electron captura via `stdout.on('data')` no `main.cjs`
- Token fica em `bmoApiToken` (variável em memória)
- Renderer acessa via `window.bmoDesktop.getBmoToken()`
- Token exposto via IPC handler `bmo:get-token`

### 4. Integração com Frontend
- `getJson()` e `postJson()` em `App.tsx` agora incluem `X-BMO-Token` header automaticamente
- Se não estiver rodando no Electron (token vazio), não envia header

### 5. Headers CORS atualizados
- `Access-Control-Allow-Headers` agora inclui `X-BMO-Token`
- Origin refletido corretamente para origens permitidas

---

## Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `backend/bmo_backend.py` | `_BMO_API_TOKEN`, `require_bmo_token()`, validação em do_GET/do_POST, CORS com Origin check |
| `electron/main.cjs` | Captura do token via stdout, IPC handler, stdio pipe |
| `electron/preload.cjs` | `getBmoToken()` exposto via contextBridge |
| `src/App.tsx` | `getBmoHeaders()`, X-BMO-Token em getJson e postJson |

---

## Notas de segurança

- Token é **gerado a cada reinicialização do backend** — não persiste
- Nunca é salvo em disco
- Nunca transmitido em rede (backend escuta só 127.0.0.1)
- Se o Electron iniciar antes do backend printar o token, as requests terão token vazio e serão rejeitadas — retry automático via `setInterval` no Electron
