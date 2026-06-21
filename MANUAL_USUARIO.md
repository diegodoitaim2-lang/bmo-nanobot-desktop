# Manual do Usuario - BMO v1

## O que e o BMO

BMO e um assistente de IA desktop com chat, voz, memoria, ferramentas e configuracoes visuais.

## Como conversar

- Digite no chat e aperte Enter.
- Use o microfone para falar com o BMO.
- Quando o recurso Wake Word estiver instalado, diga "Hey BMO" para chamar o BMO sem clicar.
- Use os botoes rapidos para pesquisar, criar tarefas, analisar textos ou pedir ajuda com codigo.

## Voz

Na aba Voz voce pode:

- escolher uma voz Piper;
- testar a voz;
- abrir a pasta de vozes;
- adicionar novos modelos `.onnx` em `runtime/piper`.

Depois de adicionar uma voz, clique em **Atualizar vozes**.

## Provedores e modelos

Na aba Provedores voce configura sua chave API.
Na aba Modelos voce escolhe o modelo ativo ou digita um modelo custom.

## Memoria

BMO salva lembrancas importantes automaticamente em `MEMORY.md` dentro da pasta de dados do app.
Voce tambem pode adicionar ou limpar memorias manualmente na aba Memoria.

## Skills

Na aba Skills voce ve as skills instaladas e pode criar uma skill simples sem editar codigo.

## Arquivos

O botao de anexo no chat permite inserir o conteudo de arquivos texto/codigo no campo de mensagem.
Arquivos binarios e imagens sao anexados como referencia, sem travar o chat.

## Lembretes

O BMO pode mostrar lembretes em popup com botoes **Adiar** e **Concluir**.
Quando o lembrete aparece, ele tambem fala em voz alta.

## Temas

Na aba Sistema/Configuracoes voce pode escolher o tema visual. O tema escolhido fica salvo para a proxima abertura.

## Pastas importantes

Na aba Sistema ou Configuracoes voce pode abrir:

- pasta de dados;
- pasta de configuracoes;
- pasta de vozes;
- pasta de memoria.

## Observacoes

Algumas capacidades avancadas, como agendamento em background e subagentes persistentes, ainda precisam de configuracao segura para desktop. O BMO nao deve fingir que concluiu uma acao se ela ainda nao esta ativa.
