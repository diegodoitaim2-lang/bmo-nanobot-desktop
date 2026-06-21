# Configuração do BMO

Guia completo de configuração de provedores, modelos, canais e preferências.

---

## Provedores de IA

O BMO suporta múltiplos provedores de IA. Você configura no painel **Provedores**.

### Provedores Suportados

| Provedor | Como obter chave | Custo |
|---|---|---|
| **OpenRouter** | [openrouter.ai/keys](https://openrouter.ai/keys) | Gratuito + pago |
| **OpenAI** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Pago (centavos) |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com) | Pago |
| **Ollama** | Local (gratuito) | Gratuito |
| **Azure OpenAI** | Portal Azure | Pago |
| **GitHub Copilot** | Token GitHub | Gratuito |
| **LM Studio** | Local (gratuito) | Gratuito |

### Configuração Padrão (OpenRouter)

1. Vá em **Provedores**
2. Selecione `openrouter`
3. Cole sua chave de API
4. Em **Modelos**, escolha `openai/gpt-oss-120b:free`
5. Clique em **Salvar**

### Usando Modelos Locais (Ollama)

1. Instale o [Ollama](https://ollama.com)
2. Baixe um modelo: `ollama pull llama3.2`
3. No BMO, vá em **Provedores** → selecione `ollama`
4. Em **Modelos**, digite `llama3.2`
5. Salve

---

## Voz

### Ativar Fala

1. Vá em **Voz**
2. Ative "Falar respostas"
3. Escolha o idioma (Português ou English)
4. Selecione uma voz (Alzira, Márcia, ou outras vozes baixadas)

### Ativar Microfone

1. Vá em **Voz**
2. Na seção microfone, clique em "Escolher microfone"
3. Selecione seu dispositivo de áudio
4. Fale algo para testar

### Wake Word ("Hey BMO")

1. Vá em **Voz** → **Wake Word**
2. Ative "Escutar Hey BMO"
3. Diga "Hey BMO" para ativar o microfone

> ⚠️ A wake word usa o modelo OpenWakeWord local. Pode levar alguns segundos para carregar na primeira vez.

---

## Canais de Mensagem

O BMO pode se conectar a outros aplicativos de mensagem.

### Configurar Telegram

1. Vá em **Canais**
2. Clique em Telegram
3. Crie um bot no [@BotFather](https://t.me/botfather) do Telegram
4. Copie o token do bot
5. Cole no campo "Bot Token" no BMO
6. Salve

### Configurar Discord

1. Vá em **Canais** → Discord
2. Crie um bot no [Discord Developer Portal](https://discord.com/developers/applications)
3. Copie o token do bot
4. Cole no BMO e salve

---

## Preferências Visuais

No painel **Configurações**:

| Opção | Descrição |
|---|---|
| **Tema** | Escolha entre 7 temas visuais (Cartoon, LED, Floresta...) |
| **Idioma** | Português (BR) ou English |
| **Modelo padrão** | Modelo de IA usado nas conversas |
| **Temperatura** | Criatividade das respostas (0.0 = preciso, 1.0 = criativo) |
| **Janela sempre visível** | BMO fica sobre outras janelas |
| **Iniciar com Windows** | BMO abre automaticamente ao ligar o PC |

---

## Segurança

- As chaves de API ficam armazenadas em `%APPDATA%\bmo\config\secrets.env`
- Nenhum dado é enviado para servidores externos além das chamadas de API
- O BMO não coleta telemetria ou estatísticas de uso
