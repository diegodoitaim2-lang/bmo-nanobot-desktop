# Workspace do BMO

O workspace é a pasta onde o BMO guarda arquivos criados durante as conversas: pesquisas, relatórios, resultados de subagentes, códigos e downloads.

---

## Onde Fica

O workspace está em:

```
%APPDATA%\bmo\workspace\
```

Para abrir rapidamente: vá no painel **Workspace** e clique em **"Abrir pasta"**.

---

## O que Você Encontra no Workspace

| Tipo | Exemplos |
|---|---|
| 📁 **Pesquisas** | `pesquisa_python.txt`, `relatorio_ia.md` |
| 📁 **Relatórios** | `resumo_reuniao.md`, `analise_dados.json` |
| 📁 **Código** | `script.py`, `app.js`, `index.html` |
| 📁 **Subagentes** | Resultados de tarefas em background |
| 📁 **Downloads** | Arquivos baixados pelo BMO |
| 📁 **Documentos** | `notas.md`, `lista_compras.txt` |

---

## Como Usar

### Pelo Chat

Peça ao BMO diretamente:

> "Crie um arquivo chamado pesquisa_ia.txt com um resumo sobre inteligência artificial"
> "Salve o resultado da pesquisa em relatorio.md"
> "Crie um subagente para pesquisar e salvar em resultado.txt"

### Pelo Painel Workspace

1. Vá em **Workspace** na barra lateral
2. Veja todos os arquivos organizados por categoria
3. Clique no caminho para abrir a pasta no Windows

---

## Estrutura Completa

```
%APPDATA%\bmo\
├── workspace\          ← Arquivos criados pelo BMO
│   ├── memory\        ← Memória do Nanobot (MEMORY.md, history.jsonl)
│   ├── SOUL.md        ← Personalidade do BMO
│   ├── USER.md        ← Informações sobre você
│   ├── AGENTS.md      ← Configuração de agentes
│   └── HEARTBEAT.md   ← Heartbeat polling
├── config\            ← Configurações
├── memory\            ← Memória backup
├── history\           ← Histórico de conversas
├── voices\            ← Vozes Piper
├── logs\              ← Logs do sistema
└── ...
```

---

## Limpeza e Backup

### Backup

Para exportar a memória do BMO (incluindo notas e preferências):

1. Vá em **Memória**
2. Clique em **Exportar backup**
3. Escolha onde salvar

### Limpeza

- **Memória**: Use o botão "Limpar memória" no painel Memória
- **Arquivos**: Exclua manualmente os arquivos pelo Windows Explorer
- **Subagentes**: Use "Limpar finalizados" no painel Ferramentas

> ⚠️ Arquivos no workspace são criados pelo BMO durante as conversas. Excluir um arquivo não afeta o funcionamento do BMO.
