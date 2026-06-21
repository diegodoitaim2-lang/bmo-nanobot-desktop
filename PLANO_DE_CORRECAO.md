# Plano de correcao do BMO

## Objetivo

Restaurar desempenho, estabilidade, precisao e confiabilidade do BMO sem adicionar novas funcionalidades e sem alterar a interface.

## Correcoes ja aplicadas nesta auditoria

### C1 - Contexto compativel com NanoBot

Arquivo:

- `backend/bmo_backend.py`

Antes:

- O historico era enviado em multiplas mensagens.
- O provedor rejeitava com `Only a single user message is supported`.

Depois:

- O contexto recente e condensado em uma unica mensagem.
- O BMO mantem continuidade em perguntas de acompanhamento.

Validacao:

- Teste: falar sobre "OVNI do Parana" e depois perguntar "O que voce acha disso?".
- Resultado: a segunda resposta manteve o assunto.

### C2 - Reducao de prompt

Arquivo:

- `backend/bmo_backend.py`

Antes:

- Alma + memoria + historico podiam ficar grandes demais.

Depois:

- Alma: 2200 caracteres.
- Memoria: 1200 caracteres.
- Historico: 10 mensagens / 6500 caracteres.

Resultado esperado:

- Menor latencia.
- Menos mistura de assuntos.
- Menor custo em tokens.

### C3 - Ordem de modelos corrigida

Arquivos:

- `config/nanobot_config.json`
- `%LOCALAPPDATA%\BMO\config\nanobot_config.json`

Antes:

- O BMO tentava modelos pagos/sem permissao antes do modelo gratis.

Depois:

- Principal: `openai/gpt-oss-120b:free`.
- Reservas: modelos gratis.

Resultado esperado:

- Evita cascata de reinicios.
- Reduz o tempo de resposta.

### C4 - Wake word preparado

Arquivos:

- `build-electron.bat`

Ambiente:

- `openwakeword` instalado.
- Recursos auxiliares baixados.
- `runtime/wakeword.onnx` validado.

Resultado:

- Wake word aparece como disponivel e rodando no backend de desenvolvimento.

### C5 - Cache de vozes

Arquivo:

- `backend/bmo_backend.py`

Antes:

- Pasta de vozes era varrida repetidamente.
- Log de voz invalida era escrito sem parar.

Depois:

- Cache de 30 segundos.
- Arquivo invalido logado apenas uma vez por execucao.

## Resultados medidos depois das correcoes

| Teste | Tempo |
|---|---:|
| Primeira chamada de chat | 19,79 s |
| Segunda chamada contextual | 6,41 s |
| Piper TTS curto | 4,92 s |
| Teste de escuta sem fala | 2,83 s ate erro amigavel de silencio |

Meta:

- Conversas comuns devem ficar proximas ou abaixo de 10 a 15 segundos apos aquecimento.
- Chamadas com voz sempre somam tempo de Piper e playback.

## Pendencias recomendadas antes do executavel

### P1 - Validar wake word com voz real

Necessario:

- Abrir o BMO.
- Dizer "Hey BMO".
- Verificar se `wakeword.eventId` muda.
- Confirmar que a interface inicia captura.

Motivo:

- O modelo carrega, mas a deteccao real depende do microfone, volume e ambiente.

### P2 - Medir CPU com interface aberta

Necessario:

- Medir CPU do processo Electron/BMO com a janela aberta.
- Medir CPU com janela minimizada.
- Medir CPU durante fala, wake word e chat.

Motivo:

- A auditoria de backend mostrou CPU baixa em repouso, mas screenshots anteriores indicaram picos no app completo.

### P3 - Unificar polling de lembretes/subagentes

Motivo:

- React e Electron consultam dados semelhantes.
- Nao e critico, mas reduz chamadas periodicas.

### P4 - Encerrar arvore de processos no fechamento

Motivo:

- Servidores `nanobot serve` orfaos causam porta ocupada e confusao de estado.

Acao futura:

- Registrar PID do processo filho.
- Encerrar arvore completa no `before-quit`.
- Em inicializacao, limpar somente processos antigos do proprio BMO.

### P5 - Separar CPU total e CPU do BMO

Motivo:

- CPU total do Windows pode mostrar picos externos como se fossem do BMO.

Acao futura:

- Expor `systemCpuPercent` e `bmoCpuPercent`.

## Como testar agora

1. Fechar completamente qualquer BMO instalado.
2. Encerrar processos antigos `bmo_backend` e `nanobot serve` se ficarem presos.
3. Rodar o BMO em modo desenvolvimento.
4. Testar:
   - "Oi BMO"
   - "Vamos falar sobre o OVNI do Parana"
   - "O que voce acha disso?"
5. Verificar se a segunda resposta entende o contexto.
6. Testar uma chamada de voz.
7. Testar "Hey BMO" em ambiente silencioso.

## Criterio de aceite

O BMO so deve ser empacotado novamente quando:

- Chat comum responder sem cascata de modelos.
- Perguntas de acompanhamento mantiverem contexto.
- Wake word funcionar em teste real.
- Piper continuar funcionando.
- Nao houver processos duplicados apos fechar.
- CPU ficar baixa em repouso.
