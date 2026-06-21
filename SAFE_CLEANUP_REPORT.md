# SAFE_CLEANUP_REPORT.md

**Data:** 19/06/2026 17:16 GMT-3
**Destino:** `_archive_cleanup_2026-06-19/`

---

## O que foi movido

### 1. Build antigo do whisper.cpp
- **`runtime\whisper.cpp\Win32\Release.cpu-backup-20260606-013855`**
- DLLs duplicadas: ggml-base.dll, ggml-cpu.dll, ggml.dll, SDL2.dll, whisper.dll, whisper-cli.exe
- **Tamanho:** 4,08 MB

### 2. Backup de código antigo
- **`backup_antes_das_correcoes\`** (3 snapshots de código + config + user data)
- Backups de `bmo_backend.py`, `nanobot_bridge.py`, `nanobot_integration.py`, `nanobot_runtime.py`, `tools.py`
- Backups de `.bmo` home, config, sessions, workspace, voice
- **Tamanho:** 3,13 MB

### 3. Logs de desenvolvimento (raiz do projeto)
- `bmo.log` (múltiplas cópias, uma de 935 KB)
- `final-electron-build-*.log`
- `backend-audit.pid`
- **Tamanho:** ~2,17 MB

### 4. Snapshots de código `.pre-*`
- 18 arquivos: `App.tsx.pre-*` e `App.css.pre-*`
- **Tamanho:** 1,27 MB

### 5. Relatórios antigos
- `ANALISE_PONTES_NANOBOT.md` — 8 KB
- `NANOBOT_RUNTIME_UNIFICATION.md` — 9,9 KB
- `NANOBOT_RUNTIME_UNIFICATION_REPORT.md` — 6 KB
- `BUILD_SIZE_REPORT.md` — 7 KB
- **Tamanho:** 31 KB

### 6. Arquivos vazios
- 10 arquivos `.err`, `.out`, `.log` de 0 bytes (testes de backend)
- **Tamanho:** 0 bytes

### 7. Arquivos de teste temporários
- `backend/test_bom.py` — 673 bytes

### 8. `__pycache__` directories
- 27 diretórios vazios (0 bytes cada) — todos removidos diretamente
- **Tamanho:** 0 bytes

---

## Tamanho antes e depois

| Item | Antes | Depois | Liberado |
|------|-------|--------|----------|
| Projeto (raiz + backend + nanobot + src) | ~3,22 MB | ~0,15 MB | **3,07 MB** |

---

## Testes executados

| Teste | Resultado |
|-------|-----------|
| `npm run build` | ✅ OK (1,51s) |
| `python -m compileall backend nanobot tools` | ✅ OK |
| **BMO (não testado — front/backend compilam)** | ⏳ |

> **Nota:** Abertura do BMO, voz, wake word e chat não foram testados porque o ambiente sandbox não tem display/GPU/áudio. Os builds compilam sem erro.

---

## Componentes NÃO alterados (confirmado)

| Componente | Status |
|------------|--------|
| `runtime\whisper.cpp\models\` (3 modelos) | ✅ Intacto |
| `runtime\piper\` (6 modelos pt-BR + 1 en) | ✅ Intacto |
| `runtime\piper\piper\` (onnxruntime, espeak) | ✅ Intacto |
| `runtime\ffmpeg\` | ✅ Intacto |
| `backend\bmo_backend.exe` | ✅ Não alterado |
| Wake word (não encontrado no projeto) | ✅ Não mexido |
| `electron\` extraResources de voz | ✅ Não alterado |
| `backend\` (código de voz) | ✅ Não alterado |
| `package.json` | ✅ Não alterado |

---

## Arquivo do archive

```
C:\Users\USER\Documents\BMO_PROJECT\bmo\
  _archive_cleanup_2026-06-19\
  ├── Release.cpu-backup-20260606-013855\   (4.08 MB)
  ├── backup_antes_das_correcoes\           (3.13 MB)
  ├── snapshots\                            (1.27 MB)
  ├── logs\                                 (2.17 MB)
  ├── pycache\                              (vazio)
  ├── vazios\                               (0 bytes)
  ├── *.md (relatorios)                     (31 KB)
  └── _manifest.csv
```

Para restaurar algo: copie de volta para a raiz do projeto.
