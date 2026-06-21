# Gargalos identificados no BMO

## G1 - Cascata de modelos indisponiveis

Severidade: critica

Evidencia:

- Logs mostraram tentativas em modelos pagos/indisponiveis antes do modelo gratis funcional.
- Cada troca de modelo reiniciava o NanoBot server.
- Tempo observado antes da estabilizacao: dezenas de segundos.

Causa:

- Configuracao em `nanobot_config.json` priorizava modelos sem permissao/credito.

Status:

- Corrigido.

Correcao:

- Modelo principal definido como `openai/gpt-oss-120b:free`.
- Fallbacks pagos removidos da ordem principal.

## G2 - Contexto enviado em formato incompativel

Severidade: critica

Evidencia:

- Erro do provedor: `Only a single user message is supported`.
- O BMO tentava modelo por modelo depois desse erro.

Causa:

- O backend passou historico como varias mensagens `system/user/assistant`.
- O caminho atual do NanoBot/OpenRouter neste projeto se comporta melhor com uma unica mensagem de usuario.

Status:

- Corrigido.

Correcao:

- O historico recente agora e condensado em texto dentro de uma unica mensagem.

## G3 - Historico salvo mas nao usado corretamente

Severidade: critica

Evidencia:

- Usuario perguntava "O que voce acha?" e o BMO respondia como se nao soubesse o assunto.
- `history.json` tinha mensagens anteriores, mas o prompt nao as usava adequadamente.

Causa:

- `save_chat_turn()` persistia a conversa.
- `ask_nanobot()` nao recebia a sessao de forma util.

Status:

- Corrigido.

Correcao:

- `sessionId` agora alimenta `recent_context_messages()`.
- O prompt final inclui contexto recente da sessao.

## G4 - Prompt grande demais

Severidade: alta

Evidencia:

- `SOUL.md`, `MEMORY.md` e historico podiam somar muitos caracteres.
- O contexto grande aumenta latencia e pode misturar assuntos.

Causa:

- Limites permissivos: 4000 caracteres de alma, 3000 de memoria e ate 14000 de historico.

Status:

- Corrigido parcialmente.

Correcao:

- Alma reduzida para 2200 caracteres.
- Memoria recente reduzida para 1200 caracteres.
- Historico reduzido para 10 mensagens / 6500 caracteres.
- Log registra `prompt_chars`.

## G5 - Wake word sem dependencia completa

Severidade: alta

Evidencia:

- `openwakeword` nao estava instalado.
- Apos instalar, faltavam modelos auxiliares internos do pacote.

Causa:

- Dependencias de wake word nao entravam no runtime/build.

Status:

- Corrigido no ambiente de desenvolvimento.
- Preparado para empacotamento futuro.

Correcao:

- Instalado `openwakeword`.
- Baixados modelos auxiliares.
- Validado `runtime/wakeword.onnx`.
- `build-electron.bat` atualizado para incluir `openwakeword`, `onnxruntime`, `scipy` e `sklearn`.

## G6 - Varredura repetida de vozes

Severidade: media

Evidencia:

- Log repetia continuamente: `voice ignored invalid_size`.
- A interface consulta status/vozes periodicamente.

Causa:

- `list_voice_models()` varria disco e logava arquivo invalido a cada chamada.

Status:

- Corrigido.

Correcao:

- Cache de vozes por 30 segundos.
- Arquivos invalidos so sao logados uma vez por execucao.

## G7 - Processos orfaos do NanoBot

Severidade: alta

Evidencia:

- Porta `8900` ocupada por `nanobot serve` antes do backend BMO responder.
- Havia mais de um processo relacionado ao NanoBot.

Causa:

- Encerramento anterior deixou servidor interno vivo.
- Tambem havia processos externos do NanoBot original rodando ao mesmo tempo.

Status:

- Parcialmente mitigado.

Mitigacao existente:

- Backend limpa servidor stale na porta `8900`.
- Electron tem single instance lock.

Recomendacao:

- Em fase posterior, registrar PID filho e encerrar arvore de processos com mais rigor no fechamento.

## G8 - Polling duplicado de lembretes/subagentes

Severidade: media

Evidencia:

- React e Electron consultam lembretes/subagentes em paralelo.

Causa:

- Uma rotina existe para UI visivel e outra para notificacoes em background.

Status:

- Nao alterado nesta fase para evitar regressao.

Recomendacao:

- Consolidar polling em um coordenador unico no Electron e enviar eventos ao React.

## G9 - Ferramentas dependentes de parser local

Severidade: media

Evidencia:

- Se o pedido nao bate no parser local, o LLM pode responder como se fosse executar algo.

Causa:

- Ferramentas ainda nao possuem um protocolo unico de execucao/confirmacao como no NanoBot original.

Status:

- Parcialmente mitigado por prompt e parsers existentes.

Recomendacao:

- Criar uma camada unica de tool-call local antes de permitir o modelo afirmar sucesso.

## G10 - Leitura de CPU pode oscilar

Severidade: baixa/media

Evidencia:

- `/api/system` retornou CPU alta quando processos BMO estavam ociosos.
- O computador tambem tinha processos externos ativos.

Causa provavel:

- Leitura representa CPU total do sistema, nao CPU exclusiva do BMO.
- A amostragem curta pode pegar picos do Windows/antivirus/outros processos.

Status:

- Documentado.

Recomendacao:

- Separar CPU total do sistema e CPU do processo BMO em metricas diferentes.
