# RELATORIO COMPLETO DE CONTINUIDADE - PROJETO BMO

Data do relatorio: 2026-06-06
Projeto principal atual: BMO / bmo
Caminho principal:
C:\Users\USER\Documents\Codex\bmo

Este arquivo foi criado para preservar o historico tecnico e de produto do projeto antes de formatar o PC.
Ele serve para retomar o desenvolvimento depois, sem depender da memoria do chat.

IMPORTANTE:
- Nao salvar API keys completas neste relatorio.
- Fazer backup desta pasta inteira antes de formatar:
  C:\Users\USER\Documents\Codex\bmo
- Fazer backup tambem dos dados locais do app:
  C:\Users\USER\AppData\Local\BMO
- Fazer backup dos assets soltos usados no projeto:
  C:\Users\USER\Documents\Codex
  C:\Users\USER\Pictures
  C:\Users\USER\Downloads\BMO

---

## 1. Visao geral do projeto

O objetivo final e transformar o BMO em um assistente desktop autonomo, com personalidade propria, visual profissional, voz, microfone, memoria, ferramentas, tarefas, lembretes, wake word e configuracoes visuais completas.

A ideia evoluiu em duas fases:

1. BMO Hermes:
   - Primeira versao baseada no projeto Be More Agent.
   - Tkinter.
   - Integracao com motor Hermes Agent.
   - Piper TTS.
   - Whisper.
   - Sprites/faces originais do BMO.
   - Empacotamento com PyInstaller.

2. BMO atual:
   - Migracao para Electron + React + Python backend.
   - Motor baseado no Nanobot.
   - Interface moderna e propria do BMO.
   - Sem depender do Hermes como motor.
   - Hermes/OpenClaw foram usados apenas como referencia visual/funcional.

O projeto atual que deve continuar e:
C:\Users\USER\Documents\Codex\bmo

---

## 2. Decisoes tecnicas importantes

### Framework desktop

Foi decidido migrar de Tauri para Electron porque:
- Tauri dependia de WebView2.
- Em VM limpa, o app falhava com erro:
  "Could not find the WebView2 Runtime."
- Mesmo com WebView2 Fixed Runtime, o Windows ainda procurava runtime no registro.
- Electron vem com Chromium embutido e resolve isso para instalador self-contained.

Status:
- Projeto atual e Electron + React + Python backend.
- Nao usar Tauri na continuacao, a menos que haja motivo muito forte.

### Backend

O backend atual e Python:
C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py

Ele gerencia:
- Chat.
- Nanobot/local API.
- OpenRouter.
- Piper TTS.
- Whisper STT.
- Wake word.
- Historico.
- Memoria.
- Tarefas.
- Lembretes.
- Subagentes.
- Arquivos.
- Configuracoes.
- Status do sistema.

### Frontend

Interface React:
C:\Users\USER\Documents\Codex\bmo\src\App.tsx

Ela contem:
- Sidebar.
- Chat.
- Personagem BMO.
- Temas.
- Configuracoes.
- Provedores.
- Modelos.
- Voz.
- Microfone/Whisper.
- Sistema.
- Historico.
- Memoria.
- Ferramentas.
- Canais.

### Dados do usuario

Pasta local do app:
C:\Users\USER\AppData\Local\BMO

Arquivos importantes:
- C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json
- C:\Users\USER\AppData\Local\BMO\memory\MEMORY.md
- C:\Users\USER\AppData\Local\BMO\memory\USER.md
- C:\Users\USER\AppData\Local\BMO\memory\SOUL.md
- C:\Users\USER\AppData\Local\BMO\history\history.json
- C:\Users\USER\AppData\Local\BMO\logs\
- C:\Users\USER\AppData\Local\BMO\workspace\

---

## 3. Personalidade do BMO

Direcao desejada:
- O BMO deve ser simplesmente "BMO".
- Nunca deve mencionar Nanobot, motor, API, OpenRouter, backend ou tecnologias internas para o usuario comum.
- Personalidade inspirada no BMO original de Hora de Aventura, misturada com um assistente tipo Jarvis:
  - fofo;
  - animado;
  - educado;
  - divertido;
  - levemente infantil no charme;
  - profissional quando executa tarefas;
  - honesto quando falha;
  - nunca finge que executou algo.

Prompt essencial pedido pelo usuario:
"Voce e o BMO. Um assistente autonomo com personalidade propria, divertido e amigavel. Voce nunca menciona Nanobot, motores, APIs ou qualquer tecnologia interna. Para voce e para o usuario, voce e simplesmente o BMO."

Arquivo relacionado:
C:\Users\USER\AppData\Local\BMO\memory\SOUL.md

Pendencia recorrente:
- Respostas ainda podem ficar genericas.
- O BMO as vezes perde contexto.
- Precisa manter o historico da sessao e memoria enviados corretamente ao modelo.

---

## 4. Identidade visual atual

O visual aprovado esta em direcao a:
- BMO OS.
- Verde escuro/neon.
- Cenario do quarto do BMO como fundo.
- Personagem BMO completo no centro.
- Cards glassmorphism.
- Sidebar esquerda.
- Chat inferior/central.
- Barra/status inferior.
- Painel direito com CPU, memoria e rede em estilo ECG.

Regras visuais importantes:
- Nao voltar para Tkinter.
- Nao usar rosto gigante solto.
- Nao cortar o BMO.
- O BMO deve aparecer inteiro.
- Chat nao pode sobrepor o corpo do BMO em escala 100%, 125% ou 150%.
- Em resolucoes menores, usar layout responsivo e scroll.
- Fundos devem ficar nitidos, nao com blur/overlay pesado.
- Glassmorphism apenas nos componentes, nunca no wallpaper inteiro.

Temas/fundos usados ou planejados:
- Tema padrao escuro BMO.
- Tema cartoon verde claro.
- Tema quarto BMO.
- Tema casa da arvore.
- Tema floresta noturna.

Arquivos de imagens citados pelo usuario:
- C:\Users\USER\Documents\Codex\BMO 3.png
- C:\Users\USER\Documents\Codex\BMO 4...
- C:\Users\USER\Pictures\BMO 5.jpg
- C:\Users\USER\Pictures\BMO 6.jpg
- C:\Users\USER\Pictures\BMO 7.jpg
- C:\Users\USER\Downloads\BMO\ChatGPT Image 26 de mai. de 2026, 18_56_52.png
- C:\Users\USER\Documents\Codex\BMO QUARTO

Importante:
- O tema Verde LED foi pedido algumas vezes, mas depois o usuario disse que nao era mais necessario porque os temas atuais ficaram bons.

---

## 5. Personagem BMO

Decisao visual:
- Usar BMO completo, nao apenas face gigante.
- O personagem fica no centro da interface.
- A face deve ficar dentro da tela do corpo do BMO.
- Nao redesenhar manualmente sprites/faces se ja houver sprites corretos.

Problemas ja tratados:
- Rosto fora da tela do personagem.
- BMO cortado no topo.
- Chat sobrepondo o BMO.
- Texto "Oi! Eu sou o BMO" duplicado.
- BMO pequeno demais.

Pendencias/atenção:
- Em escala 150%, verificar de novo:
  - BMO nao pode ser cortado.
  - Chat deve ficar mais baixo e centralizado.
  - Sidebar deve manter texto.
  - BMO deve ficar proporcional.

---

## 6. Voz Piper

Objetivo:
- Piper TTS local.
- Sem terminal visivel.
- Voz em background.
- Boca animada enquanto o audio toca.
- Suporte PT-BR e EN.
- Modelos .onnx detectados automaticamente.

Problemas corrigidos ao longo do projeto:
- Piper abria janela preta.
- Piper/modelo nao encontrado.
- Voz parou apos alteracoes.
- Faltavam modelos na lista.
- Boca nao animava.

Diretorios relacionados:
- C:\Users\USER\Documents\Codex\bmo\runtime\piper
- C:\Users\USER\Documents\Codex\bmo\runtime\sounds
- C:\Users\USER\Documents\Codex\pacote de voz em portugues br

Sons desejados:
- Som de inicializacao.
- Som de processamento.
- Frase PT-BR obrigatoria:
  "Quem quer jogar videogame?"
- Frase EN:
  "Who wants to play video games?"

Pendencia:
- Conferir apos reinstalacao se todos os modelos .onnx e .json de voz foram copiados para runtime/piper.
- A tela Voz deve listar automaticamente todos os .onnx.

---

## 7. Whisper / Microfone / GPU

Problemas antigos:
- Whisper usava modelo ggml-base.en.bin, que e ingles-only.
- Whisper falhava com codigo -1073741795.
- Microfone nao funcionava por falta de numpy/sounddevice no empacotamento.
- GPU nao era usada, apenas CPU.

Estado atual corrigido em 2026-06-06:
- Foi trocada a build do whisper.cpp por uma build compilada localmente com Vulkan.
- A GPU detectada no PC foi:
  Radeon RX 570 Series via Vulkan0.
- O backend confirmou:
  lastMode: gpu.
- Modelos existentes e testados:
  - ggml-tiny.bin
  - ggml-base.bin
  - ggml-small.bin

Runtime atual:
C:\Users\USER\Documents\Codex\bmo\runtime\whisper.cpp\Win32\Release

Backup da build antiga CPU-only:
C:\Users\USER\Documents\Codex\bmo\runtime\whisper.cpp\Win32\Release.cpu-backup-20260606-013855

Arquivos principais da build nova:
- whisper-cli.exe
- whisper.dll
- ggml.dll
- ggml-base.dll
- ggml-cpu.dll
- ggml-vulkan.dll

Config atual:
C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json

Configuracao Whisper:
- gpu_enabled: true
- gpu_index: 0
- model: base
- fallback_to_cpu: true

Resultados de teste:
- tiny: 1.32s, modo gpu
- base: 1.81s, modo gpu
- small: 6.31s, modo gpu

Relatorio salvo:
C:\Users\USER\Desktop\relatorio_gpu_whisper.txt

Observacao importante:
- Builds prontas com Vulkan foram testadas, mas falharam com -1073741795.
- Causa provavel: incompatibilidade com AVX2/FMA no processador Intel Core i5-2400.
- Por isso foi compilada uma build propria sem:
  - GGML_NATIVE
  - AVX2
  - FMA
  - F16C

Pendencia para empacotamento:
- Garantir que a build Vulkan e todos os .dll entrem no instalador.
- Garantir que numpy e sounddevice entrem no backend empacotado.

---

## 8. Provedores, API keys e modelos

Provider principal:
- OpenRouter.

Modelo principal usado em varios testes:
- openai/gpt-oss-120b:free

Problemas recorrentes:
- "No API key configured for provider None".
- "User not found", code 401.
- "Only configured model ... is available".
- API key nao persistia no nanobot_config.json.
- O BMO respondia "Conexao OK" mas depois nao conseguia conversar.

Regras importantes:
- Nunca salvar API keys completas em relatorios.
- UI de Provedores deve salvar a chave no arquivo real:
  C:\Users\USER\AppData\Local\BMO\config\nanobot_config.json
- Tambem deve atualizar secrets quando aplicavel.
- Deve haver fallback de multiplas chaves.
- Se uma chave falhar, tentar a proxima.
- Se um modelo falhar, tentar fallback model.
- Erros tecnicos devem ser traduzidos para mensagem amigavel.

Pendencia:
- Revisar persistencia apos formatacao/reinstalacao.
- Criar fluxo de primeiro uso sem API:
  - explicar OpenRouter em linguagem simples;
  - link direto;
  - campo para colar chave;
  - nao mostrar erro tecnico.

---

## 9. Historico e memoria

Historico:
- Deve salvar conversas.
- Deve permitir reabrir sessoes.
- Deve manter contexto na mesma sessao.

Memoria:
- Arquivos principais:
  - MEMORY.md
  - USER.md
  - SOUL.md

Problemas observados:
- BMO esquecia contexto imediatamente.
- Depois de reiniciar, nao lembrava de nada.
- Respostas ficavam sem relacao com pergunta anterior.
- Nanobot original mantinha melhor contexto.

Melhorias ja feitas ou iniciadas:
- Foi criada auditoria de arquitetura.
- Foram criados relatorios de teste/saude.
- Foram corrigidas falhas ligadas a historico/contexto em algumas rotas.

Pendencia critica:
- Comparar exatamente como o Nanobot original injeta memoria e historico no prompt.
- Garantir que o BMO envie:
  - mensagens recentes da sessao;
  - memoria resumida;
  - USER.md;
  - SOUL.md;
  sem duplicar contexto gigante.

---

## 10. Ferramentas, arquivos e subagentes

Ferramentas desejadas:
- Criar arquivos.
- Abrir arquivos criados.
- Criar relatorios.
- Organizar arquivos.
- Buscar na web.
- Executar tarefas.
- Criar subagentes reais.

Problemas corrigidos:
- BMO dizia "arquivo criado" sem criar.
- BMO nao lembrava do arquivo criado.
- BMO nao abria arquivo criado.
- BMO abria relatorio errado automaticamente.

Correcao mais recente:
Arquivo:
C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py

Funcao alterada:
- open_file_from_message
- find_file_to_open
- nova funcao is_file_open_request

Motivo:
- O BMO estava abrindo o relatorio_gpu_whisper.txt sem o usuario pedir.
- A logica anterior abria o arquivo mais recente da Area de Trabalho se a mensagem tivesse palavras como "resultado" ou "relatorio".

Resultado:
- Perguntas comuns nao abrem mais arquivo.
- So abre arquivo se o usuario pedir claramente:
  - "abra o relatorio"
  - "abrir o arquivo criado"
  - "abra nome.txt"
- Foi removido o fallback perigoso para "arquivo mais recente".

Pendencias:
- Subagentes ainda precisam de auditoria pesada.
- Eles devem:
  - ter ID;
  - progresso;
  - status;
  - arquivo de saida;
  - notificacao de conclusao;
  - abrir relatorio gerado.

---

## 11. Lembretes, alarmes e notificacoes

Objetivo:
- Criar lembretes tipo:
  "me lembre de tomar agua daqui 5 minutos"
- Disparar mesmo com app minimizado.
- Popup por cima de tudo.
- Som de alerta.
- Piper falando o lembrete.
- Botões:
  - Concluir
  - Adiar 5 min
  - Adiar 10 min
- Persistir depois de reiniciar o app.

Problemas observados:
- BMO confirmava lembrete mas nao disparava.
- Popup nao aparecia minimizado.
- Em alguns casos dizia que disparou sem mostrar nada.

Estado:
- Houve correcoes anteriores, mas precisa validar em bateria real apos reinstalacao.

Pendencia:
- Testar "lembrete em 10 segundos".
- Testar app minimizado.
- Testar reinicio do app antes do horario.

---

## 12. Wake word

Objetivo:
- "Hey BMO" acorda o BMO sem clique.
- Baseado no projeto original com OpenWakeWord e wakeword.onnx.

Problemas observados:
- Wake word ficou lento.
- Ficava ouvindo por muito tempo.
- As vezes nao respondia.

Estado:
- Foi corrigido em algum momento, mas voltou a ser citado como problema.

Pendencia:
- Teste isolado de wake word.
- Medir CPU.
- Garantir que nao cria loops/processos duplicados.

---

## 13. Bandeja, janela unica e instalador

Regras desejadas:
- Clicar no X minimiza para a bandeja, nao fecha.
- Menu da bandeja permite sair completamente.
- Se clicar no icone com BMO ja aberto, nao abrir segunda instancia.
- Deve focar/restaurar janela existente.
- Nao criar varios BMO em segundo plano.

Problema observado:
- Abria mais de uma janela/processo.

Pendencia:
- Garantir single instance lock no Electron.
- Se ja existe instancia, chamar focus/restore.

Instalador:
- Deve ser Electron Builder / NSIS.
- Deve ser self-contained.
- Nao depender de Python instalado.
- Nao depender de Node instalado.
- Incluir:
  - backend Python empacotado;
  - runtime Piper;
  - runtime Whisper;
  - modelos Whisper;
  - vozes Piper;
  - ffmpeg se necessario;
  - assets;
  - configs iniciais.

Importante:
- Nao gerar instalador ate o app estar testado e aprovado.

---

## 14. Problemas de desempenho

Sintomas observados:
- BMO ficou mais lento que Nanobot original.
- Algumas respostas demoravam 1 a 2 minutos.
- CPU alta.
- Digitar no chat ficava lento.
- Wake word consumia CPU.
- Layout/animacoes podem ter pesado.

Auditorias pedidas/criadas:
- AUDITORIA_BMO.md
- GARGALOS_IDENTIFICADOS.md
- PLANO_DE_CORRECAO.md
- TEST_REPORT.md
- BMO_HEALTH_REPORT.md

Pendencia:
- Revisar se estes arquivos estao na pasta do projeto.
- Reexecutar bateria de teste apos formatacao.
- Otimizar:
  - loops de status;
  - wake word;
  - render React;
  - animacoes ECG;
  - subagentes;
  - historico/memoria enviados ao modelo.

---

## 15. Bugs importantes ja relatados

Lista acumulada dos principais bugs citados:

1. App abre em VM mas janela nao aparece.
2. Processo fica no Gerenciador de Tarefas, mas sem janela.
3. BMO abre varias instancias.
4. BMO fica pensando e nao responde.
5. API key nao persiste.
6. Provider vira None.
7. User not found 401.
8. Modelo configurado nao bate com OpenRouter.
9. Microfone falha por falta de numpy/sounddevice.
10. Piper/modelo de voz nao encontrado.
11. Hey BMO nao funciona.
12. Perda de contexto na mesma sessao.
13. Respostas genericas.
14. Ferramentas fingem sucesso.
15. Arquivos criados nao abrem.
16. Relatorio abre sem pedir.
17. Lembretes nao disparam.
18. Popup nao aparece minimizado.
19. Chat lento ao digitar.
20. Layout quebra em escala 150%.
21. Tema nao persiste.
22. Fundos ficam escuros/embaçados demais.
23. BMO cortado ou grande demais em resolucao/escala.
24. Voz nao muda idioma junto com interface.
25. Interface nao traduz para ingles.

---

## 16. Correcoes recentes e estado atual conhecido

### Whisper GPU

Status: corrigido e testado.

Confirmado:
- GPU Vulkan ativa.
- Tiny/base/small funcionam.
- Backend mostra lastMode=gpu.

### Relatorio abrindo sozinho

Status: corrigido no backend.

Arquivo:
C:\Users\USER\Documents\Codex\bmo\backend\bmo_backend.py

Mudanca:
- Removido fallback para abrir o arquivo mais recente da Area de Trabalho.
- Adicionada validacao mais forte de intencao de abrir arquivo.

Precisa reiniciar o BMO para carregar esta correcao.

### Espaco em disco

Foi feita limpeza de temporarios da compilacao:
- C:\bmo_wsrc
- C:\bmo_wbuild
- C:\bmo_vk
- C:\bmo_spirv
- instalador Vulkan temporario
- build temporaria dentro do projeto

Espaco livre subiu de aproximadamente 1.5 GB para 5.7 GB.

---

## 17. O que fazer antes de formatar

Fazer backup destas pastas:

1. Projeto:
C:\Users\USER\Documents\Codex\bmo

2. Dados locais:
C:\Users\USER\AppData\Local\BMO

3. Assets e imagens soltas:
C:\Users\USER\Documents\Codex
C:\Users\USER\Pictures
C:\Users\USER\Downloads\BMO

4. Vozes extras:
C:\Users\USER\Documents\Codex\pacote de voz em portugues br

5. Instaladores/outputs se existirem:
C:\Users\USER\Documents\Codex\bmo\dist
C:\Users\USER\Documents\Codex\bmo\release

Nao confiar apenas na Area de Trabalho, pois ela sera perdida se nao for salva.

---

## 18. Como retomar depois da formatacao

1. Restaurar a pasta:
C:\Users\USER\Documents\Codex\bmo

2. Restaurar:
C:\Users\USER\AppData\Local\BMO

3. Instalar ambiente de desenvolvimento:
- Node.js LTS.
- Python 3.11 ou 3.12.
- Git.
- Visual Studio Build Tools se precisar recompilar backend/Whisper.

4. Instalar dependencias do frontend:
No projeto:
npm install

5. Instalar dependencias Python do backend:
Verificar requirements se existir.
Garantir principalmente:
- numpy
- sounddevice
- requests
- pillow
- pywin32 se usado
- psutil se usado

6. Rodar em desenvolvimento:
Verificar package.json para script exato.
Provavel:
npm run dev

7. Validar:
- Chat basico.
- API key.
- Piper.
- Whisper.
- Wake word.
- Historico.
- Memoria.
- Lembrete em 10 segundos.
- Abrir arquivo criado.
- Escala 150%.

---

## 19. Checklist de validacao antes de gerar executavel

Nao gerar instalador antes de passar:

- [ ] BMO abre janela normalmente.
- [ ] Nao abre segunda instancia.
- [ ] Chat responde em menos de 15s em pergunta simples.
- [ ] Contexto funciona na mesma conversa.
- [ ] API key persiste apos reiniciar.
- [ ] Provider nao vira None.
- [ ] Piper fala.
- [ ] Boca anima enquanto fala.
- [ ] Lista todas as vozes .onnx.
- [ ] Whisper captura microfone.
- [ ] Whisper usa GPU quando ligado.
- [ ] Whisper cai para CPU se GPU falhar.
- [ ] Hey BMO funciona.
- [ ] Lembrete em 10s dispara popup + voz.
- [ ] Popup aparece com app minimizado.
- [ ] Criar arquivo salva na Area de Trabalho.
- [ ] Abrir arquivo criado funciona.
- [ ] Nao abre relatorio sem pedir.
- [ ] Historico salva e reabre.
- [ ] Memoria persiste apos reiniciar.
- [ ] Layout funciona em 100%, 125%, 150%.
- [ ] Fundos ficam nitidos.
- [ ] Tema persiste.
- [ ] Chat nao fica lento ao digitar.
- [ ] CPU em idle aceitavel.
- [ ] RAM aceitavel.

---

## 20. Prioridades para a proxima fase

Ordem sugerida:

1. Estabilizar API key/provider/modelo.
2. Estabilizar contexto/memoria.
3. Estabilizar microfone/wake word.
4. Estabilizar Piper/vozes.
5. Estabilizar lembretes.
6. Estabilizar layout em 150%.
7. Otimizar consumo.
8. Rodar bateria de testes.
9. Gerar executavel.
10. Testar em VM limpa.
11. Criar instalador final.

---

## 21. Opiniao tecnica sincera

O BMO tem potencial muito forte porque combina:
- personagem carismatico;
- voz;
- microfone;
- interface bonita;
- agente local com ferramentas;
- memoria;
- tarefas;
- estilo unico.

Mas para ficar realmente profissional, o ponto principal nao e adicionar mais recursos.
O foco deve ser:
- confiabilidade;
- velocidade;
- contexto;
- instalador limpo;
- nao mentir sobre tarefas;
- nao abrir coisas sozinho;
- nao travar;
- nao perder configuracoes.

Quando esses pontos estiverem firmes, o BMO pode virar um produto muito divertido e serio ao mesmo tempo.

---

## 22. Ultima nota para retomada

Se este projeto for retomado em um novo chat, comece dizendo:

"Continuar projeto BMO a partir do arquivo RELATORIO_CONTINUIDADE_BMO.md. Primeiro leia esse arquivo, depois audite o estado atual do projeto antes de mexer em codigo."

Arquivo principal para ler:
C:\Users\USER\Documents\Codex\bmo\RELATORIO_CONTINUIDADE_BMO.md

Fim do relatorio.
