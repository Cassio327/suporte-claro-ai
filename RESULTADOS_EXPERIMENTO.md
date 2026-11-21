# Resultados do experimento

## Escopo

Esta análise consolida a avaliação humana de uma única rodada com oito gerações: quatro tipos de conteúdo (`diagnostico`, `resolucao`, `perguntas` e `fluxo`) nas versões v1 e v2 do prompt.

- Perfil: P01 — leigo, didático, chat.
- Ticket: retorno à tela de login no notebook após digitar a senha; a conta funciona no celular; o navegador já foi fechado e aberto.
- Modelo retornado: `qwen2.5:3b`, executado com Ollama.
- Configuração fixa: temperatura 0,2; máximo de 1.800 tokens; mesmo ticket, perfil, tipo, esquema JSON e modelo em cada par.
- Instrumento: rubrica de clareza, adequação ao nível e acionabilidade, de 1 (insuficiente) a 5 (excelente).
- Controle contra viés: a CLI exibiu cada par como A/B em ordem estável, sem mostrar a versão antes da nota.

A evidência original, inclusive as justificativas registradas pelo candidato com apoio de IA na redação, está em [`samples/login-ollama-avaliado.json`](samples/login-ollama-avaliado.json). A execução que produziu as respostas está registrada no [GitHub Actions](https://github.com/Cassio327/suporte-claro-ai/actions/runs/44793023471).

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

## Conclusão da rodada de login

Este experimento **não permite afirmar superioridade geral da v2**: há somente um ticket, um perfil, uma execução de cada versão e um modelo local específico. Ele permite afirmar que, neste cenário controlado, a v2 teve ganho agregado pequeno (+3 pontos), melhorou muito o fluxo e regrediu na resolução.

A rodada motivou a hipótese de pedir uma verificação observável e preservar as proteções do dispositivo. A instrução proposta foi:

> Não repita informação ou ação que já esteja no ticket. Sugira apenas um teste reversível ainda não realizado; diga o que observar e como cada resultado define o próximo passo. Nunca instrua a desativar proteções de segurança.

As rodadas abaixo registram o teste por perfil e a revisão da estratégia de resolução. As três notas da rubrica oficial continuam vinculadas a cada resposta de login.

## Áudio: o mesmo ticket para dois níveis técnicos

O cliente ouve os colegas, mas eles não o ouvem. O ícone do microfone aparece ligado. P01 e P02 têm o mesmo estilo didático e canal de chat. A rodada usou a resolução v2 e o Qwen com a mesma configuração nas duas chamadas. Mudaram o nível técnico e o identificador de perfil. [Registros originais](samples/audio-perfis-v2.json) · [Execução](https://github.com/Cassio327/suporte-claro-ai/actions/runs/44842058249)

| Perfil | Trecho da resolução | O que o usuário conseguiria verificar |
|---|---|---|
| P01 · leigo | “Verificar as configurações de áudio” | Investiga o componente certo. Olhar o ícone ainda ligado repete algo já conhecido e deixa em aberto se os colegas voltaram a ouvir. |
| P02 · avançado | “Tente mudar a posição da câmera no computador” | O passo muda a imagem e não testa a captação de som. Também pede conferir se o ícone está desligado, invertendo o sinal descrito no ticket. |

A instrução específica para um cliente avançado chegou ao modelo. Nesta amostra, a resposta ao perfil avançado perdeu o foco no microfone. Uma saída por perfil permite identificar essa falha, mas é insuficiente para atribuí-la ao nível técnico. Um teste de gravação ou de entrada de som permitiria observar se a voz é captada.

## Resolução v3: o que mudou no atendimento

A rodada usou os mesmos pesos do Qwen e a mesma configuração da rodada de áudio. Os pares de upload também compartilham perfil, ticket e contrato. As observações abaixo são uma revisão técnica. O par de upload está disponível para avaliação pela CLI com a rubrica original. [Execução da revisão](https://github.com/Cassio327/suporte-claro-ai/actions/runs/44842849687)

| Teste | Resultado observado | Decisão |
|---|---|---|
| Áudio · P02 | A v2 orientou mover a câmera. A v3 pediu um teste de áudio, mas presumiu que o microfone pertence à câmera e que existe uma luz verde piscante. Também deixou de explicar como executar o teste. | A revisão recuperou o assunto do ticket. A orientação ainda requer revisão antes de atender o cliente. [Saída v3](samples/audio-P02-v3.json) |
| Upload · P01 | O cliente já havia enviado 1 MB e relatado falha aos 70% com 18 MB. A v2 pediu confirmar o tamanho conhecido e reiniciar o computador. A v3 propôs enviar 5 MB e observar a progressão. | O teste intermediário pode trazer informação nova. Uma única tentativa é insuficiente para concluir que há um limite de tamanho. Falta orientar o que fazer se o envio terminar ou voltar a parar. [Par v2/v3](samples/upload-v2-v3.json) |

**Decisão de versão.** A CLI conserva a v2 como padrão para os quatro conteúdos. A v3 é uma opção experimental apenas para resolução. Nesta rodada de upload, a primeira ação da v3 foi mais útil; no áudio, o comportamento ainda dependeu de detalhes inventados pelo modelo. Cada versão teve uma geração por condição. O efeito sobre outros modelos e atendimentos permanece em aberto.

**Exemplo de critério de aceitação para o áudio.** Um atendente pode pedir a P01 que selecione o microfone usado na reunião, fale uma frase no teste de microfone do aplicativo, se disponível, e confira se consegue ouvir a própria gravação. Para P02, pode pedir que compare a captura do mesmo dispositivo no sistema operacional e no aplicativo. Se apenas o aplicativo falhar, vale verificar a entrada selecionada e a permissão de microfone. São exemplos de referência para revisão humana. As saídas efetivamente geradas estão preservadas nos arquivos vinculados.
