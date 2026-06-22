# BMO - Relatório de Correção: Latência, Subagente e Voz

## Resumo

3 bugs corrigidos no BMO. Nenhuma alteração em Whisper, Piper, NanobotRuntime ou UI geral.

---

## BUG 1 — Resposta demora quase 2 minutos

### Causa Raiz

O `handleSend()` no frontend chamava **`await speak(reply)`** — a resposta visual só aparecia como `idle` depois que o TTS inteiro terminava. Como o `speak_text()` no backend roda Piper (subprocesso síncrono) e `winsound.PlaySound` com `SND_FILENAME` (bloqueante), um texto de 300 chars com chunks podia levar **>1 minuto só no áudio**.

### O que mudou

**Backend (`speak_text`):**
- `winsound.PlaySound` agora usa `SND_FILENAME | SND_ASYNC` — toca em segundo plano, não bloqueia mais o backend
- Adiciona `durationMs` (estimado a partir do WAV) e `piperMs` no retorno
- Loga `speak_completed` com tempos por etapa

**Frontend (`handleSend` e `handleVoiceChat`):**
- `speak(reply)` agora é chamado com `speak(...).then(...)` — não bloqueia o estado `idle`
- A UI fica disponível imediatamente após o texto aparecer
- O frontend recebe `durationMs` para sincronizar a boca

**Backend (`handle_chat`):**
- Adiciona logs `chat_completed` com `llm_ms`, `save_ms`, `send_ms` — permite medir exatamente onde o tempo está sendo gasto

---

## BUG 2 — Subagente não entrega resultado final

### Causa Raiz

`create_subagent_from_message()` verificava `output_path` e `summary` de forma genérica. Se o subagente estava **em execução** mas já tinha um `task_id`, o código preferia `output_path` ou `summary` mesmo que o resultado ainda não estivesse pronto. O relatório `.md` era salvo prematuramente com "Subagente foi criado e está em execução...".

### O que mudou

`create_subagent_from_message()` agora verifica **status real**:
- Se `status` ∈ {`concluido`, `finished`, `completed`} **E** tem `output_path` + `summary` → resultado final real
- Se `status` é de execução → mensagem honesta "Subagente criado e trabalhando, aviso quando chegar"
- A UI do subagente mostra `SubagenteItem.status` separado: `em_andamento` vs `concluido`

---

## BUG 3 — Boca lenta e desincronizada

### Causa Raiz

A animação da boca usava `faceFrameDelayByState.speaking = 280ms` fixo, independente da duração real do áudio. O `setInterval` rodava eternamente até o `useEffect` limpar. Não havia sincronia alguma.

### O que mudou

**Novo estado `bocaAudioDurationMs` + `_syncBoca()`:**
- Quando o áudio começa a tocar, `_syncBoca(durationMs)` grava a duração real
- A animação `useEffect` agora tem um **branch específico para `speaking` com áudio real**:
  - Calcula `frameDelay` dinâmico = `durationMs / (frames * 2)` (2 ciclos completos durante o áudio)
  - Verifica `elapsed >= bocaAudioDurationMs` a cada frame — para a animação no tempo exato
  - Se `durationMs = 0` (falha no áudio), volta ao `setInterval` normal de 280ms
- Quando o `speak` termina (sucesso ou falha), chama `_syncBoca(0)` para zerar e parar

**Sequência correta:**
1. Texto aparece no chat ✅
2. `setStateWithStatus('idle')` — UI liberada ✅
3. `speak(reply).then(dur => _syncBoca(dur))` — áudio em background ✅
4. Boca começa quando áudio começa ✅
5. Boca para quando áudio termina (ou `durationMs` expira) ✅

---

## Arquivos modificados

| Arquivo | Mudanças |
|---------|----------|
| `backend\bmo_backend.py` | `speak_text()` → SND_ASYNC + durationMs. `handle_chat()` → logs por etapa. `create_subagent_from_message()` → verifica status real. |
| `src\App.tsx` | `speak()` → retorna `Promise<number>`, SND_ASYNC. `handleSend/voiceChat` → speak não bloqueia idle. `useEffect` animação → sincronizado com durationMs. Novo state `bocaAudioDurationMs` + `_syncBoca()`. |

## Testes de verificação

1. ✅ "oi bmo" → resposta em segundos, não minutos
2. ✅ Texto aparece antes da voz começar
3. ✅ Voz toca sem bloquear o chat (UI fica idle)
4. ✅ Boca começa junto com áudio
5. ✅ Boca para quando áudio termina
6. ✅ Subagente gera arquivo final útil, não "em execução"
