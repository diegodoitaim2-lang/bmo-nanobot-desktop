# Teste em Máquina Virtual Limpa

Guia de teste do BMO em VM Windows limpa, simulando a instalação por um usuário real.

---

## Preparação

### Requisitos da VM

- **SO**: Windows 10 ou 11 (x64)
- **RAM**: 4 GB (8 GB recomendado)
- **Disco**: 30 GB livres
- **Rede**: Acesso à internet

### Ferramentas Recomendadas

- **VirtualBox** (gratuito)
- **VMware Workstation Player** (gratuito)
- **Hyper-V** (Windows Pro)

---

## Checklist de Teste

### 1. Instalação

| Item | Resultado |
|---|---|
| Instalador abre sem erros | ✅ / ❌ |
| SmartScreen não bloqueia | ✅ / ❌ |
| Atalho criado na Área de Trabalho | ✅ / ❌ |
| Atalho no Menu Iniciar | ✅ / ❌ |
| Desinstalador funciona | ✅ / ❌ |

### 2. Primeira Inicialização

| Item | Resultado |
|---|---|
| Backend inicia automaticamente | ✅ / ❌ |
| Interface React abre | ✅ / ❌ |
| BMO mostra "Olá!" | ✅ / ❌ |
| Painéis carregam sem erro | ✅ / ❌ |
| Logs sem erros críticos | ✅ / ❌ |

### 3. Configuração

| Item | Resultado |
|---|---|
| Provedor OpenRouter configurável | ✅ / ❌ |
| Salvar chave de API funciona | ✅ / ❌ |
| Teste de conexão passa | ✅ / ❌ |
| Modelo pode ser selecionado | ✅ / ❌ |

### 4. Chat

| Item | Resultado |
|---|---|
| Mensagem enviada com sucesso | ✅ / ❌ |
| Resposta recebida em < 30s | ✅ / ❌ |
| Histórico aparece no painel | ✅ / ❌ |
| Botão "Nova conversa" funciona | ✅ / ❌ |

### 5. Voz

| Item | Resultado |
|---|---|
| Piper TTS ativo | ✅ / ❌ |
| BMO fala resposta | ✅ / ❌ |
| Microfone detectado | ✅ / ❌ |
| Whisper transcreve áudio | ✅ / ❌ |
| Wake Word "Hey BMO" ativa | ✅ / ❌ |

### 6. Memória

| Item | Resultado |
|---|---|
| Adicionar memória funciona | ✅ / ❌ |
| Memória aparece no painel | ✅ / ❌ |
| Após reiniciar, memória persiste | ✅ / ❌ |
| Limpar memória funciona | ✅ / ❌ |

### 7. Ferramentas

| Item | Resultado |
|---|---|
| Ferramentas listadas (19) | ✅ / ❌ |
| Subagentes criados | ✅ / ❌ |
| Tarefas aparecem | ✅ / ❌ |

### 8. Skills

| Item | Resultado |
|---|---|
| Skills listadas no painel | ✅ / ❌ |
| Criar skill funciona | ✅ / ❌ |

### 9. Reinicialização

| Item | Resultado |
|---|---|
| Fechar e reabrir mantém memória | ✅ / ❌ |
| Configurações persistem | ✅ / ❌ |
| Histórico preservado | ✅ / ❌ |
| Wake Word funciona após reinício | ✅ / ❌ |

---

## Gerando o Relatório

Após testar todos os itens, copie o modelo acima para um arquivo `VM_TEST_REPORT.md` e marque cada item com ✅ ou ❌.

Inclua:
- Versão do Windows
- RAM e CPU da VM
- Versão do BMO testada
- Data do teste
- Screenshots de problemas encontrados

---

## Problemas Comuns em VM

| Problema | Causa | Solução |
|---|---|---|
| Áudio não funciona | VM sem driver de áudio | Instale Guest Additions |
| Microfone não detectado | VM sem microfone virtual | Ative passagem de áudio na VM |
| Performance lenta | VM com pouca RAM | Aumente para 8 GB |
| Placa de vídeo genérica | VM sem aceleração 3D | Ative aceleração 3D na VM |
| Wake Word não carrega | CPU sem suporte AVX | Desative wake word |
