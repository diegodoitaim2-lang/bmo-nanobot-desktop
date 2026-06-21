# 🚀 Como Abrir o BMO Corrigido

## ⚠️ Janela Preta? Problema Resolvido!

O problema era que o Electron estava tentando conectar ao Vite dev server que não estava rodando.

**Solução aplicada:** Agora o Electron carrega direto do `dist/` compilado.

---

## 📋 Instruções

### **Opção 1: Simples (Recomendado)**

```bash
cd "C:\Users\USER\Documents\PROJETO EASYCLAW\bmo"
npm run electron
```

✅ Pronto! BMO abre com a interface compilada.

---

### **Opção 2: Dev Mode (com hot reload)**

Se você quer fazer alterações no código e ver em tempo real:

```bash
# Terminal 1
npm run dev

# Terminal 2
set BMO_USE_DEV_SERVER=1
npm run electron
```

---

## 🔧 O que foi corrigido

**Arquivo:** `electron/main.cjs`  
**Mudança:** Agora verifica `process.env.BMO_USE_DEV_SERVER` antes de usar dev server

```javascript
// ANTES
const useDevServer = isDev && process.env.BMO_ELECTRON_LOAD_DIST !== '1';

// DEPOIS
const useDevServer = isDev && process.env.BMO_ELECTRON_LOAD_DIST !== '1' && process.env.BMO_USE_DEV_SERVER === '1';
```

---

## ✅ O que você deve ver

```
┌─────────────────────────────────────┐
│ BMO                                 │
├─────────────────────────────────────┤
│                                     │
│    [Logo/Interface do BMO]          │
│                                     │
│    Painel lateral com:              │
│    - Chat                           │
│    - Memória                        │
│    - Histórico                      │
│    - Modelos                        │
│    - Provedores ← Cole chave aqui!  │
│    - Voz                            │
│    - Ferramentas                    │
│    - Subagentes                     │
│                                     │
└─────────────────────────────────────┘
```

---

## 🐛 Se ainda der problema

### Problema: Janela continua preta

**Solução:**
```bash
# Limpa build e reconstrói
rm -r dist/
npm run build

# Depois abre novamente
npm run electron
```

### Problema: Erro "Cannot find module"

**Solução:**
```bash
# Reinstala dependências
rm -r node_modules package-lock.json
npm install

# Reconstrói
npm run build
npm run electron
```

### Problema: "Backend não encontrado"

**Solução:** O backend Python não está configurado. Pode criar manualmente ou use o chat apenas sem backend por enquanto.

---

## 📁 Estrutura de Diretórios

```
bmo/
├── dist/                    ← Frontend compilado (usado agora)
├── src/                     ← Source TypeScript/React
├── backend/                 ← Backend Python
├── electron/                ← Electron main.cjs (MODIFICADO)
├── package.json
└── tsconfig.json
```

---

## ✨ Pronto!

Agora o BMO deve abrir normalmente com toda a interface visível! 🎉

Se tiver problemas, verifique os logs em:
```
~/.bmo/logs/main.log
```

---

**Status:** ✅ BMO corrigido e pronto para usar!
