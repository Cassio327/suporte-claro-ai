# Resultados do experimento

## Escopo

Esta análise consolida a avaliação humana de uma única rodada com oito gerações: quatro tipos de conteúdo (`diagnostico`, `resolucao`, `perguntas` e `fluxo`) nas versões v1 e v2 do prompt.

- Perfil: P01 — leigo, didático, chat.
- Ticket: retorno à tela de login no notebook após digitar a senha; a conta funciona no celular; o navegador já foi fechado e aberto.
- Modelo retornado: `qwen2.5:3b`, executado com Ollama.
- Configuração fixa: temperatura 0,2; máximo de 1.800 tokens; mesmo ticket, perfil, tipo, esquema JSON e modelo em cada par.
- Instrumento: rubrica de clareza, adequação ao nível e acionabilidade, de 1 (insuficiente) a 5 (excelente).
- Controle contra viés: a CLI exibiu cada par como A/B em ordem estável, sem mostrar a versão antes da nota.

A evidência original, inclusive as justificativas escritas pelo avaliador, está em [`samples/login-ollama-avaliado.json`](samples/login-ollama-avaliado.json). A execução que produziu as respostas está registrada no [GitHub Actions](https://github.com/Cassio327/suporte-claro-ai/actions/runs/44793023471).

## Resultado numérico

| Tipo | v1 (soma / 15) | v2 (soma / 15) | Diferença v2 − v1 | Leitura |
|---|---:|---:|---:|---|
| Diagnóstico | 7 | 7 | 0 | Empate |
| Resolução | 9 | 6 | -3 | Regressão da v2 |
| Perguntas | 5 | 6 | +1 | Melhora discreta da v2 |
| Fluxo de decisão | 3 | 8 | +5 | Melhora relevante da v2 |
| **Total** | **24 / 60** | **27 / 60** | **+3** | **Ganho de 0,25 ponto por critério, em média** |

A média geral foi **2,00** para a v1 e **2,25** para a v2, considerando 12 avaliações por versão (quatro tipos × três critérios).

| Critério | v1 (soma / 20) | v2 (soma / 20) | Diferença v2 − v1 |
|---|---:|---:|---:|
| Clareza | 9 | 10 | +1 |
| Adequação ao nível | 8 | 10 | +2 |
| Acionabilidade | 7 | 7 | 0 |

## Interpretação

A v2 obteve ganho pequeno no agregado, concentrado principalmente no fluxo de decisão. Ela não superou a v1 de forma uniforme: no passo a passo de resolução, repetiu ações que o ticket já declarava realizadas, reduzindo a acionabilidade.

A avaliação também encontrou falhas que são úteis para orientar a próxima iteração:

- No diagnóstico, ambas as versões usaram termos técnicos e relacionaram hipóteses às evidências de forma insuficiente para P01.
- Na resolução v2, “fechar e abrir o navegador” repete uma ação já realizada pelo cliente; a nota de acionabilidade foi 1.
- Nas perguntas, as duas versões ainda perguntaram ou testaram informações já presentes no ticket, embora a v2 tenha melhorado levemente a soma.
- No fluxo v1, a sugestão de desativar firewall ou antivírus foi considerada inadequada e insegura para o caso. A v2 evitou esse problema, mas ainda repetiu o teste em outro dispositivo e não explicou bem o encaminhamento.

## Conclusão e próximo experimento

Este experimento **não permite afirmar superioridade geral da v2**: há somente um ticket, um perfil, uma execução de cada versão e um modelo local específico. Ele permite afirmar que, neste cenário controlado, a v2 teve ganho agregado pequeno (+3 pontos), melhorou muito o fluxo e regrediu na resolução.

A próxima versão deve acrescentar uma regra operacional curta e testável:

> Não repita informação ou ação que já esteja no ticket. Sugira apenas um teste reversível ainda não realizado; diga o que observar e como cada resultado define o próximo passo. Nunca instrua a desativar proteções de segurança.

A validação dessa mudança deve usar um **segundo ticket inédito**, preservar esta rodada como linha de base e repetir a mesma rubrica. Assim, a evolução do prompt permanece rastreável e não é ajustada apenas para este exemplo.
