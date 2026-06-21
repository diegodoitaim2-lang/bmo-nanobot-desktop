# Changelog — Histórico de Versões

---

## v1.0.0 (Em preparação)

### Novidades
- 🧠 **Runtime unificado**: NanobotRuntime como singleton único
- 🩺 **Painel de Diagnóstico**: Status visual de todos os componentes
- 💾 **Central de Memória**: Memória categorizada (fatos, preferências, projetos)
- 🛠️ **Painel de Ferramentas**: Grid categorizado com status
- 📦 **Painel de Skills**: Skills com status e descrição
- 📂 **Workspace Visual**: Explorador de arquivos do workspace
- 🔧 **Sanitização**: Script para remover referências pessoais do projeto
- 📚 **Documentação profissional**: 11 documentos em `docs/`

### Melhorias
- Interface de memória expandida com seções e detalhes expansíveis
- Ferramentas categorizadas automaticamente (Web, Arquivos, Execução...)
- Skills com leitura real de SKILL.md para descrição
- Navegação na sidebar inclui Workspace

### Correções
- Build de frontend otimizado (~276 KB JS, gzip ~86 KB)
- Sanitização de 87 arquivos com referências pessoais
- Limpeza de ~10 MB de lixo de build e logs

### Dependências
- Node.js 18+
- Python 3.11+
- Electron (empacotamento)
- Nanobot runtime (biblioteca interna)
- Piper TTS (voz)
- Whisper.cpp (reconhecimento de fala)
- OpenWakeWord (wake word)

---

## Histórico Anterior

Versões anteriores (0.x) não documentadas formalmente.

---

## Notas de Release

### Compatibilidade
- Windows 10/11 x64
- Requer 4 GB RAM mínimo (8 GB recomendado)
- Requer 2 GB de espaço em disco

### Atualização
Para atualizar da versão anterior:
1. Desinstale a versão antiga (dados do usuário são preservados)
2. Instale a nova versão
3. Abra o BMO — configurações e memória persistem
