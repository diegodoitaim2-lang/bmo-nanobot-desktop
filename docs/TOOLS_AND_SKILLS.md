# Ferramentas e Skills do BMO

Guia completo de ferramentas disponíveis e como instalar skills.

---

## Ferramentas

As ferramentas são capacidades que o BMO pode usar automaticamente durante uma conversa. Você não precisa ativar nada — o BMO decide quando usá-las.

### Lista Completa

| Ferramenta | Categoria | O que faz |
|---|---|---|
| **Web Search** | 🌐 Web | Pesquisa na internet e retorna resultados |
| **Web Fetch** | 🌐 Web | Lê o conteúdo de uma página web |
| **Read File** | 📁 Arquivos | Lê arquivos no workspace |
| **Write File** | 📁 Arquivos | Cria ou sobrescreve arquivos |
| **Edit File** | 📁 Arquivos | Edita partes específicas de arquivos |
| **Apply Patch** | 📁 Arquivos | Aplica patches em código |
| **Find Files** | 📁 Arquivos | Busca arquivos por nome/padrão |
| **Grep** | 📁 Arquivos | Busca texto dentro de arquivos |
| **List Dir** | 📁 Arquivos | Lista o conteúdo de pastas |
| **Exec** | ⚡ Execução | Executa comandos no terminal |
| **Shell** | ⚡ Execução | Executa scripts shell |
| **Run CLI App** | ⚡ Execução | Executa aplicações de linha de comando |
| **Cron** | ⏰ Tarefas | Agenda tarefas para execução futura |
| **Long Task** | ⏰ Tarefas | Executa tarefas longas em background |
| **Message** | 🤖 Agente | Envia mensagens via canais configurados |
| **Spawn** | 🤖 Agente | Cria subagentes para tarefas paralelas |
| **Complete Goal** | 🎯 Meta | Marca objetivos como concluídos |
| **My** | 🤖 Agente | Informações sobre o próprio BMO |

### Como Usar

Basta **pedir** ao BMO no chat. Exemplos:

> "Pesquise sobre inteligência artificial na web"
> "Crie um arquivo chamado relatorio.txt com o resumo"
> "Execute esse código Python: print('Olá')"
> "Agende uma tarefa para amanhã às 9h me lembrar de reunião"

---

## Skills

Skills são instruções especiais que ensinam o BMO a fazer algo específico. Diferente das ferramentas, skills são instaladas manualmente.

### Skills Instaladas por Padrão

O BMO vem com uma skill pré-instalada que define sua personalidade e regras de comportamento.

### Instalar uma Nova Skill

Pelo painel **Skills**:

1. Vá em **Skills** na barra lateral
2. Preencha **Nome da skill**
3. Preencha **Descrição** (quando e como usar)
4. Clique em **Adicionar skill**

Exemplo:
- **Nome**: `pesquisa_tecnica`
- **Descrição**: `Use esta skill quando o usuário pedir pesquisa técnica aprofundada. Busque fontes confiáveis, compare resultados e apresente um resumo estruturado.`

### Status das Skills

| Status | Significado |
|---|---|
| ✅ **Carregada** | Skill ativa e pronta para uso |
| ❌ **Erro** | Skill com problema — verifique o arquivo SKILL.md |
| ⚪ **Desativada** | Skill instalada mas não carregada |

---

## Subagentes

Subagentes são "mini-BMOs" que executam tarefas em background enquanto você conversa.

### Como Usar

Peça ao BMO:

> "Crie um subagente para pesquisar sobre Python e salvar em pesquisa.txt"
> "Use um subagente para analisar esse arquivo e me dar um resumo"

### Progresso

O progresso de cada subagente aparece no painel **Ferramentas**:

- Barra de progresso (0% → 100%)
- Status (executando, concluído, erro)
- Caminho do arquivo de resultado

---

## Tarefas

Tarefas são objetivos criados pelo BMO durante a conversa.

### Gerenciar Tarefas

No painel **Ferramentas** → **Tarefas**:

- **Pendentes**: Tarefas aguardando conclusão
- **Concluídas**: Histórico de tarefas finalizadas
- **Concluir**: Marcar tarefa como feita
