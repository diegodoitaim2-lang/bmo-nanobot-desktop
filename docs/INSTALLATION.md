# Instalação do BMO Desktop

Guia passo a passo para instalar o BMO no Windows.

---

## Pré-requisitos

- **Windows 10** ou superior (64 bits)
- **4 GB de RAM** (8 GB recomendado)
- **2 GB** de espaço livre em disco
- Conexão com internet para baixar o instalador

---

## Instalação via Instalador (Recomendado)

### Passo 1: Baixar

Acesse a página de releases e baixe `BMO Setup.exe`.

### Passo 2: Executar

1. Dê dois cliques no `BMO Setup.exe`
2. Se o Windows SmartScreen alertar, clique em **"Executar assim mesmo"**
3. Escolha o idioma da instalação
4. Aceite os termos
5. Escolha a pasta de instalação (padrão: `C:\Program Files\BMO`)
6. Clique em **Instalar**

### Passo 3: Iniciar

- Um atalho do BMO será criado na Área de Trabalho
- Dê dois cliques para abrir
- O BMO iniciará automaticamente o backend Python e abrirá a interface

### Passo 4: Configurar

Ao abrir pela primeira vez:

1. Vá em **Provedores** na barra lateral
2. Escolha seu provedor (OpenRouter recomendado)
3. Insira sua chave de API
4. Clique em **Salvar**
5. Vá em **Voz** para configurar microfone e voz

---

## Instalação a Partir do Código Fonte

Para desenvolvedores ou usuários avançados:

```bash
# Clone o repositório
git clone https://github.com/seu/bmo.git
cd bmo

# Instale as dependências do Node.js
npm install

# Instale as dependências Python
pip install -r requirements.txt

# Compile o frontend
npm run build

# Inicie em modo desenvolvimento
npm run electron:dev
```

---

## Primeira Inicialização

### Sem chave de API

O BMO pode funcionar sem chave de API usando:
- **Ollama** (modelos locais) — instale o Ollama e configure no painel Provedores
- Modelos gratuitos do OpenRouter (ex: `gpt-oss-120b:free`)

### Testando a instalação

1. Digite algo no chat, por exemplo: "Olá BMO!"
2. Aguarde a resposta
3. Se funcionar, a instalação está completa

---

## Solução de Problemas na Instalação

| Problema | Solução |
|---|---|
| SmartScreen bloqueia | Clique em "Mais informações" → "Executar assim mesmo" |
| Antivírus alerta | Adicione exceção para a pasta do BMO |
| Backend não inicia | Verifique se o Python está na lista de aplicativos permitidos |
| Porta 8787 ocupada | Feche outros aplicativos que usam esta porta |
| Áudio não funciona | Verifique drivers de áudio e configure microfone no Windows |

---

## Desinstalação

1. Abra **Configurações do Windows** → **Aplicativos**
2. Busque por "BMO"
3. Clique em **Desinstalar**

> ⚠️ A desinstalação remove apenas os arquivos do programa. Dados do usuário (config, memória) permanecem em `%APPDATA%\bmo`.
