# RELEASE_CANDIDATE_REPORT.md

## BMO — Release Candidate 1

**Data:** 20/06/2026  
**Commit:** `d77df91`  
**Branch:** `main`  
**Repositório:** `diegodoitaim2-lang/bmo-nanobot-desktop` (privado)

---

## Build Status

| Etapa | Status |
|-------|--------|
| `python -m compileall backend nanobot tools` | ✅ Todos os módulos compilados |
| `npm run build` (vite + tsc) | ✅ 1783 módulos, 1.62s |
| **Instalador Electron** (NSIS) | ✅ Gerado (electron-release/BMO-v1.0.0-x64-setup.exe) |
| PyInstaller backend | ✅ Módulos locais incluídos |

---

## Principais melhorias desde o último build

### 🔒 Segurança (Hardening)
- API protegida por **token aleatório** (`X-BMO-Token`)
- **Origin check** — apenas origens locais permitidas
- Electron captura e injeta o token automaticamente

### 🧹 Limpeza do repositório
- `_archive_cleanup*`, `BMO_RELATORIO/`, `__pycache__` removidos do git
- Orphans removidos: `bmo_backend_ORIGINAL.py`, `bmo_backend_BROKEN_CLEANUP.py`
- `.gitignore` atualizado com todos os padrões de exclusão
- Vazamentos de path (`C:\Users\DIEGO`) removidos

### 🏗️ Build
- `build_vm.bat` = único script oficial
- `build-electron.bat` = deprecated (redireciona)
- `.spec` do PyInstaller usa caminho relativo

---

## Pendências para RC final

| Item | Status | Observação |
|------|--------|------------|
| Teste em VM limpa | ⏳ Pendente | `VM_VALIDATION_REPORT.md` — requer execução manual |
| Smoke test completo | ⏳ Pendente | Chat + ferramentas + memória |
| Documentação do usuário | ✅ Parcial | README.md, MANUAL_USUARIO.md existem |
| Instalador funcional | ✅ Gerado | Requer validação na VM |

---

## Estrutura atual do repositório (após limpeza)

```
bmo-nanobot-desktop/
├── backend/           # Python FastAPI (PyInstaller)
├── src/               # React + Vite + TypeScript
├── electron/          # Electron main/preload
├── bridge/            # WhatsApp bridge (Node.js)
├── build-support/     # Electron builder config
├── build/pyinstaller/ # PyInstaller .spec
├── config/            # Config templates
├── data/              # Dados de runtime
├── docs/              # Documentação
├── nanobot/           # Nanobot runtime
├── runtime/           # Piper, Whisper, wake word
└── tools/             # Scripts de ferramentas
```

---

## Como construir o RC

```bash
build_vm.bat
```

O instalador será gerado em `electron-release/BMO-v1.0.0-x64-setup.exe`
