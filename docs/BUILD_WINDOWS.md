# Build do Instalador Windows

Guia para compilar o BMO em um instalador .exe para distribuição.

---

## Pré-requisitos

- **Node.js** 18 ou superior
- **Python** 3.11 ou superior
- **NPM** 9 ou superior
- **Windows 10/11** (x64)
- **NSIS** (opcional — para o instalador)

---

## Passo a Passo

### 1. Instalar Dependências

```bash
# Dependências Node.js (frontend + Electron)
npm install

# Dependências Python (backend)
pip install -r requirements.txt
```

### 2. Compilar o Frontend

```bash
npm run build
```

Isso gera os arquivos estáticos em `dist/`.

### 3. Gerar o Instalador

```bash
npm run electron:build
```

Isso:
1. Compila o backend Python com PyInstaller
2. Empacota com Electron Builder
3. Gera o instalador NSIS em `electron-release/BMO Setup.exe`

---

## Estrutura do Build

```
bmo/
├── dist/                    ← Frontend compilado (React)
├── build/
│   └── pyinstaller/         ← Backend empacotado (PyInstaller)
├── electron/
│   ├── main.cjs             ← Processo principal Electron
│   └── preload.cjs          ← Bridge seguro
├── electron-release/
│   ├── win-unpacked/        ← Versão portátil (não instalador)
│   └── BMO Setup.exe        ← Instalador NSIS
└── runtime/
    ├── piper/               ← Piper TTS + modelos de voz
    ├── whisper.cpp/         ← Whisper STT
    └── wakeword.onnx        ← Wake word
```

---

## Comandos Úteis

| Comando | Descrição |
|---|---|
| `npm run dev` | Inicia em modo desenvolvimento |
| `npm run build` | Compila frontend |
| `npm run electron:dev` | Inicia Electron + backend em modo dev |
| `npm run electron:build` | Gera instalador completo |
| `npm run python:build` | Apenas compila backend com PyInstaller |

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `NODE_OPTIONS` | Opções do Node.js | `--max-old-space-size=4096` |
| `ELECTRON_MIRROR` | Mirror para download do Electron | (opcional) |

---

## Estrutura de Diretórios na Instalação

```
C:\Program Files\BMO\
├── backend/
│   ├── bmo_backend.exe     ← Backend Python compilado
│   └── ...                  ← Dependências
├── runtime/
│   ├── piper/               ← Piper TTS
│   ├── whisper.cpp/         ← Whisper
│   └── wakeword.onnx        ← Wake word
├── resources/
│   └── app/
│       ├── dist/            ← Frontend React
│       └── electron/        ← Arquivos Electron
├── BMO.exe                  ← Atalho principal
└── uninstall.exe            ← Desinstalador
```

---

## Verificação do Build

Após o build, verifique:

```bash
# Testar o backend compilado
build\pyinstaller\bmo_backend\bmo_backend.exe --version

# Testar o instalador
electron-release\BMO Setup.exe --help
```

---

## Personalização

Para mudar o ícone do instalador:
- `build/icon.ico` — ícone do aplicativo
- `build/installer.nsh` — personalização NSIS

Para mudar o nome do instalador:
- Edite `electron-builder.yml` → `nsis.name`

---

## Dicas

- **PyInstaller** pode demorar vários minutos na primeira execução
- O instalador final tem aproximadamente **300-500 MB**
- Builds com modo `--debug` geram mais logs no console
- Certifique-se de ter espaço livre em disco suficiente (~5 GB durante o build)
