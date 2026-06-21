# Solução de Problemas — Troubleshooting

Problemas comuns e como resolver.

---

## 🔴 O BMO Não Abre

| Causa | Solução |
|---|---|
| Backend não iniciou | Abra o Terminal, execute: `C:\Program Files\BMO\backend\bmo_backend.exe` e veja o erro |
| Porta 8787 ocupada | Feche outros programas que usam esta porta |
| Python ausente | Instale Python 3.11+ e tente novamente |

---

## 🔴 "A internet parece ter piscado" / Erro de Conexão

O BMO não conseguiu falar com o provedor de IA.

### Causas Comuns

1. **Chave de API inválida ou ausente**
   - Vá em **Provedores** e verifique se a chave foi salva

2. **Sem internet**
   - Verifique sua conexão de rede

3. **Modelo indisponível**
   - Alguns modelos do OpenRouter podem estar offline
   - Tente outro modelo: `gpt-4o-mini`, `llama-3.1-8b`

4. **Saldo insuficiente** (OpenRouter pago)
   - Verifique seu saldo em [openrouter.ai](https://openrouter.ai)

### Testar Conexão

No painel **Provedores**, clique em **"Testar conexão"**. O BMO tentará se conectar ao provedor e mostrará o resultado.

---

## 🔴 Voz Não Funciona (Piper)

| Sintoma | Solução |
|---|---|
| Buzina ao falar | Escolha outra voz no painel **Voz** |
| Sem som | Verifique volume do Windows e saída de áudio |
| Voz robótica | Baixe voz de maior qualidade (Alzira para PT-BR) |
| "Piper offline" | Reinstale ou reinicie o BMO |

---

## 🔴 Microfone Não Funciona (Whisper)

| Sintoma | Solução |
|---|---|
| BMO não me escuta | Vá em **Voz** → clique em "Escolher microfone" |
| Áudio baixo | Aumente o volume do microfone nas configurações de som do Windows |
| Ruído demais | Use fone de ouvido com microfone ou ambiente silencioso |
| Whisper lento | Use modelo `tiny` mais rápido (menos preciso) |

---

## 🔴 Wake Word "Hey BMO" Não Funciona

| Sintoma | Solução |
|---|---|
| "Aguardando OpenWakeWord" | Aguarde até 30 segundos na primeira vez |
| Não me escuta | Fale mais alto ou aproxime-se do microfone |
| Ativa sozinho | Reduza a sensibilidade no painel Voz |
| Não funciona após hibernar | Reinicie o BMO |

---

## 🔴 Performance Lenta

| Causa | Solução |
|---|---|
| Modelo Whisper grande | Use `tiny` ou `base` |
| Muitos subagentes | Aguarde concluírem ou reinicie o BMO |
| Memória cheia | Limpe memória ou histórico |
| Pouca RAM | Feche outros programas |
| CPU fraca | Reduza modelos de voz/whisper |

---

## 🔴 Erro de Build / Instalação

| Problema | Solução |
|---|---|
| `npm install` falha | Limpe cache: `npm cache clean --force && npm install` |
| `pip install` falha | Use ambiente virtual: `python -m venv venv` |
| Electron não compila | Verifique Node.js 18+ e Python 3.11+ |
| NSIS não encontrado | Instale NSIS em https://nsis.sourceforge.io |

---

## 🔴 Logs de Erro

Os logs detalhados estão em:

```
%APPDATA%\bmo\logs\bmo.log
```

Para ver no BMO: vá no painel **Sistema** e role até a seção **Logs recentes**.

---

## 🔴 Ainda Com Problemas?

1. **Reinicie o BMO** — fecha e abre novamente
2. **Reinicie o computador**
3. **Verifique os logs** (%APPDATA%\bmo\logs\bmo.log)
4. **Reinstale** o BMO
5. **Abra uma issue** no repositório do projeto
