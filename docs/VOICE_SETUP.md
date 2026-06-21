# Configuração de Voz — Piper TTS e Whisper

Guia completo para configurar som, microfone e wake word no BMO.

---

## Texto para Fala (Piper TTS)

O BMO usa o **Piper** para transformar texto em voz. Ele roda localmente, sem internet.

### Ativar

1. Abra o painel **Voz**
2. Ative **"Falar respostas"**
3. Escolha o **idioma**: Português (BR) ou English
4. Selecione uma **voz**

### Vozes Disponíveis

| Voz | Idioma | Qualidade |
|---|---|---|
| Alzira | PT-BR | Alta (feminina) |
| Márcia | PT-BR | Média (feminina) |
| Outras vozes | — | Baixe via botão "Baixar voz" |

### Velocidade da Fala

No painel Voz, ajuste o controle de **velocidade** (1.0 = normal, 1.5 = rápido).

> 💡 Se a voz parecer robótica, tente outra voz ou aumente a velocidade para 1.2.

---

## Reconhecimento de Fala (Whisper)

O BMO usa o **Whisper** para transformar sua fala em texto. Também roda localmente.

### Configurar Microfone

1. No painel **Voz**, seção Microfone
2. Clique em **"Escolher microfone"**
3. Selecione seu dispositivo de entrada de áudio
4. Fale algo para testar

### Modelos Whisper

| Modelo | Precisão | Velocidade | RAM |
|---|---|---|---|
| `tiny` | Básica | Muito rápido | ~1 GB |
| `base` | Boa | Rápido | ~1.5 GB |
| `small` | Excelente | Médio | ~2.5 GB |

> Recomendado: `base` (equilíbrio entre precisão e velocidade).

### Dicas para Melhor Captura

- Use um fone de ouvido com microfone
- Fale perto do microfone
- Ambientes silenciosos funcionam melhor
- Evite eco (use fones)

---

## Wake Word ("Hey BMO")

Com a wake word ativada, você pode chamar o BMO apenas dizendo **"Hey BMO"** sem precisar clicar em nada.

### Configurar

1. Vá em **Voz** → **Wake Word**
2. Ative **"Escutar Hey BMO"**
3. Aparecerá "Aguardando OpenWakeWord" enquanto carrega
4. Quando "Hey BMO ativo" aparecer, diga "Hey BMO"
5. O BMO acenderá o microfone automaticamente

### Como Usar

1. Diga **"Hey BMO"**
2. O BMO responde com um som e ativa o microfone
3. Faça sua pergunta ou dê um comando
4. Aguarde a resposta falada

### Solução de Problemas

| Problema | Solução |
|---|---|
| "Aguardando OpenWakeWord" | Pode levar até 30s para carregar na primeira vez |
| Não me escuta | Aumente o volume do microfone no Windows |
| Muitos falsos positivos | Reduza a sensibilidade no painel Voz |
| Não funciona após hibernar | Reinicie o BMO |

---

## Teste de Áudio

No painel **Voz**:

- **"Testar voz"** → BMO fala uma frase de teste
- **"Testar microfone"** → Grave e ouça sua gravação
- **"Escolher microfone"** → Selecione o dispositivo correto

---

## Requisitos de Hardware

| Componente | Mínimo | Recomendado |
|---|---|---|
| Piper TTS | Qualquer CPU | 2+ cores |
| Whisper (tiny/base) | 4 GB RAM | 8 GB RAM |
| Whisper (small) | 8 GB RAM | 16 GB RAM |
| Wake Word | 4 GB RAM | 8 GB RAM |
| Placa de som | Qualquer | Qualquer |
| Microfone | Embutido ou USB | Fone com microfone |
