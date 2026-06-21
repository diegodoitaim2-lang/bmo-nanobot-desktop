# BUILD_SIZE_REPORT.md

**Data:** 19/06/2026 17:08 GMT-3
**Build:** `electron-release/win-unpacked`
**Tamanho total:** 1.733,96 MB (1.818.186.375 bytes)
**Arquivos:** ~1.329 (estimado)

---

## Top 50 Maiores Arquivos

| # | Tamanho | % do Build | Arquivo |
|---|---------|-----------|---------|
| 1 | 465,01 MB | 26,82% | `resources\whisper.cpp\models\ggml-small.bin` |
| 2 | 216,36 MB | 12,48% | `BMO.exe` |
| 3 | 141,10 MB | 8,14% | `resources\whisper.cpp\models\ggml-base.bin` |
| 4 | 74,09 MB | 4,27% | `resources\whisper.cpp\models\ggml-tiny.bin` |
| 5 | 73,18 MB | 4,22% | `resources\piper\en_GB-semaine-medium.onnx` |
| 6 | 61,47 MB | 3,55% | `resources\ffmpeg\ffmpeg.exe` |
| 7 | 60,57 MB | 3,49% | `resources\piper\pt-BR-razo-medium.onnx` |
| 8 | 60,57 MB | 3,49% | `resources\piper\miro_pt-BR.onnx` |
| 9 | 60,57 MB | 3,49% | `resources\piper\dii_pt-BR.onnx` |
| 10 | 60,57 MB | 3,49% | `resources\piper\pt_BR-sage_13364-medium.onnx` |
| 11 | 60,57 MB | 3,49% | `resources\piper\bmo.onnx` |
| 12 | 60,27 MB | 3,48% | `resources\piper\pt_BR-faber-medium.onnx` |
| 13 | 55,26 MB | 3,19% | `resources\whisper.cpp\Win32\Release\ggml-vulkan.dll` |
| 14 | 37,89 MB | 2,19% | `resources\app.asar` |
| 15 | 24,53 MB | 1,42% | `dxcompiler.dll` |
| 16 | 24,45 MB | 1,41% | `resources\vc_redist.x64.exe` |
| 17 | 19,42 MB | 1,12% | `LICENSES.chromium.html` |
| 18 | 10,37 MB | 0,60% | `icudtl.dat` |
| 19 | 9,79 MB | 0,56% | `resources\piper\piper\libtashkeel_model.ort` |
| 20 | 8,84 MB | 0,51% | `resources\piper\piper\onnxruntime.dll` |
| 21 | 8,14 MB | 0,47% | `resources\piper\piper\espeak-ng-data\ru_dict` |
| 22 | 7,74 MB | 0,45% | `libGLESv2.dll` |
| 23 | 6,76 MB | 0,39% | `resources\bmo_backend\bmo_backend.exe` |
| 24 | 6,56 MB | 0,38% | `resources.pak` |
| 25 | 5,53 MB | 0,32% | `resources\bmo_backend\_internal\python311.dll` |
| 26 | 5,35 MB | 0,31% | `vk_swiftshader.dll` |
| 27 | 5,00 MB | 0,29% | `_pydantic_core.cp311-win_amd64.pyd` |
| 28 | 4,95 MB | 0,29% | `libcrypto-3.dll` |
| 29 | 4,52 MB | 0,26% | `d3dcompiler_47.dll` |
| 30 | 2,90 MB | 0,17% | `ffmpeg.dll` |
| 31 | 2,19 MB | 0,13% | `_tiktoken.cp311-win_amd64.pyd` |
| 32 | 2,17 MB | 0,13% | `resources\whisper.cpp\Win32\Release\SDL2.dll` |
| 33 | 2,17 MB | 0,13% | `Release.cpu-backup-20260606-013855\SDL2.dll` |
| 34-50 | < 2 MB | < 0,13% | Locales (ml, ta, kn, te, hi, bn, gu, mr, th, el, uk, ru) |

## Top 20 Maiores Pastas

| # | Pasta | Tamanho | % do Build |
|---|------|---------|-----------|
| 1 | `resources\whisper.cpp\models` | 680,20 MB | 39,23% |
| 2 | `resources\piper` | 436,35 MB | 25,17% |
| 3 | `resources` (outros) | 62,68 MB | 3,62% |
| 4 | `resources\ffmpeg` | 61,47 MB | 3,55% |
| 5 | `resources\whisper.cpp\Win32\Release` | 60,62 MB | 3,50% |
| 6 | `locales` | 47,18 MB | 2,72% |
| 7 | `resources\piper\piper` | 19,89 MB | 1,15% |
| 8 | `resources\bmo_backend\_internal` | 18,87 MB | 1,09% |
| 9 | `resources\piper\piper\espeak-ng-data` | 17,10 MB | 0,99% |
| 10 | `resources\bmo_backend` (sem _internal) | 6,84 MB | 0,39% |
| 11 | `_pydantic_core` | 5,00 MB | 0,29% |
| 12 | `Release.cpu-backup-20260606-013855` | 4,08 MB | 0,24% |
| 13 | `tiktoken` | 2,22 MB | 0,13% |

---

## Perguntas da Auditoria

### 1. O runtime está sendo copiado para dentro do build?

**SIM.** O diretório `resources\nanobot` existe com **3,95 MB** de arquivos-fonte Python:
- `nanobot.py`, `__init__.py`, `agent/`, `channels/`, `providers/`, `webui/`, `config/`, `utils/`, etc.
- Contém **ambos** arquivos `.py` fonte (código) e `.pyc` (bytecode compilado)
- Também contém `nobot\skills\` com 14 SKILL.md e `templates\` com templates de sistema

**Impacto:** ~4 MB de código fonte desnecessário (o backend roda via `bmo_backend.exe` que tem seu próprio Python empacotado). O `nanobot` dentro do build é **redundante** com o `bmo_backend.exe/_internal`.

---

### 2. Whisper está sendo empacotado?

**SIM.** Com **680 MB totais** em modelos:
- `ggml-small.bin` — 465 MB
- `ggml-base.bin` — 141 MB  
- `ggml-tiny.bin` — 74 MB
- `ggml-vulkan.dll` — 55 MB (Vulkan GPU backend)
- `whisper.dll` — 1,3 MB
- `SDL2.dll` — 2,2 MB
- `ggml-base.dll`, `ggml-cpu.dll`, `ggml.dll`

**Nota:** O build contém **3 modelos de whisper** (tiny, base, small) totalizando **680 MB**. Tiny (74 MB) é suficiente para português.

---

### 3. Piper está sendo empacotado?

**SIM.** Com **436 MB totais**:
- **6 modelos de voz ONNX pt-BR:** razo, miro, dii, sage, bmo, faber — cada um ~60 MB = ~363 MB
- **1 modelo inglês:** en_GB-semaine-medium.onnx — 73 MB
- **Runtime:** onnxruntime.dll (8,8 MB) + libtashkeel_model.ort (9,8 MB)
- **espeak-ng-data:** 17 MB (dados de fonemas para múltiplos idiomas)
- **total sem modelos:** ~36 MB

**Nota:** Modelos `razo-piper-voice.onnx` existe mas tem **0 bytes** (arquivo vazio).

---

### 4. Existem node_modules duplicados?

**NÃO.** Nenhum diretório `node_modules` encontrado dentro do build. O app Electron empacota dependências no `app.asar` (37,89 MB).

---

### 5. Existem builds antigos dentro do build?

**SIM.** Diretório de backup de build presente:

```
resources\whisper.cpp\Win32\Release.cpu-backup-20260606-013855
```
- Tamanho: **4,08 MB** (0,24% do build)
- Contém: C++ DLLs compiladas (SDL2.dll de 2,17 MB e outras)
- **Causa:** A build script copiou recursivamente o diretório `whisper.cpp\Win32\` inteiro, incluindo o backup

---

### 6. Existem assets ou backups empacotados acidentalmente?

**SIM.** Múltiplos problemas:

1. **22 diretórios `__pycache__`** — bytecode compilado redundante (os .py originais também estão presentes)
2. **`pydantic\deprecated`** — 0 MB (pasta vazia, mas desnecessária)
3. **Arquivos .py fonte + .pyc lado a lado** — o runtime carrega bytecode, mas os fontes .py também estão lá
4. **`locales\` com 47 MB** — Electron empacota **localizações** para dezenas de idiomas (ml, ta, kn, te, bn, gu, mr, th, el, uk, ru, etc). Apenas `pt-BR`, `en` e `es` seriam suficientes
5. **`LICENSES.chromium.html`** — 19 MB de licenças de código aberto
6. **`bmo_backend\` tem arquivos .py fonte** — `nanobot_bridge.py`, `nanobot_integration.py`, `nanobot_runtime.py`, `rate_limit.py`, `tools.py` (73 KB) são executados a partir de `bmo_backend.exe` — mas os .py crus estão presentes (redundante)

---

## Resumo de Oportunidades de Redução

| Item | Tamanho | Oportunidade |
|------|---------|-------------|
| Modelos Whisper (3) | 680 MB | Manter apenas ggml-tiny.bin (74 MB), remover base e small |
| Modelos voz pt-BR (6) | ~363 MB | Selecionar 2-3 modelos em vez de 6 |
| Modelo voz en (1) | 73 MB | Manter ou remover se só usa pt-BR |
| locales/ | 47 MB | Filtrar para pt-BR + en + es apenas |
| __pycache__ (22 dirs) | ~1 MB | Limpeza fácil |
| LICENSES.chromium.html | 19 MB | Remover do build de release |
| nanobot/ código fonte .py | ~4 MB | Empacotar apenas bytecode .pyc |
| backup build antigo | 4 MB | Excluir `Release.cpu-backup-*` |
| ffmpeg.exe | 61 MB | Verificar se é necessário em runtime ou só em dev |
| vc_redist.x64.exe | 24 MB | Não precisa dentro do build (já incluso no Electron) |

**Potencial de redução total estimado:** ~700 MB a 1 GB sem perder funcionalidade core
