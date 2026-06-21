# BMO_HEALTH_REPORT

Gerado em: 2026-06-05T18:13:13
Nota geral: **Excelente**

## Resumo

- PASSOU: 20
- FALHOU: 0
- AVISO: 1

## Bugs Restantes Priorizados

1. AVISO - 18. Uso continuo por 30 minutos
   - Modulo: Estabilidade
   - Observacao: Teste de 30 minutos nao executado nesta rodada. Use --long-minutes 30.
   - Acao sugerida: Rodar python tools/validate_bmo.py --long-minutes 30 antes do build final.

## Leitura Rapida

- Excelente: nenhum teste falhou e poucos avisos.
- Bom: falhas ausentes ou isoladas, com avisos controlados.
- Regular: ha falhas funcionais ou muitos avisos.
- Critico: falha em item essencial como chat, contexto, voz, wake word ou alarmes.
