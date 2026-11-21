# Engenharia dos prompts

## Decisões

Cada tipo usa uma estratégia de geração com uma instrução e um contrato próprios. A persona define o papel do atendente e os limites de acesso ao sistema do cliente. Uma mensagem de usuário contém o ticket e o perfil serializados. O diagnóstico expõe a conclusão e os sinais verificáveis que a sustentam. A resolução inclui uma verificação por passo. As perguntas são ordenadas pela decisão que ajudam a tomar. O fluxo representa uma decisão com três destinos, inclusive quando o cliente não consegue concluir o teste.

A v1 descreve a tarefa, apresenta o perfil e pede adaptação. Na v2, cada atributo passa a orientar uma escolha de redação. Por exemplo, P03 pede frases que o atendente possa falar ao telefone. A v2 também instrui o gerador de perguntas a verificar o que já está respondido no ticket. Ambas recebem o mesmo esquema JSON. O programa valida tipos e campos localmente. A fidelidade factual exige leitura da resposta.

## Experimento proposto

Para o ticket de login, o cliente já reiniciou o navegador e informou que a conta funciona no celular. Antes de executar, registramos duas previsões. A v2 deve aproveitar esses dois sinais para escolher a próxima pergunta e deve reduzir a repetição de passos. Um resultado desfavorável possível é explicar demais uma ação simples no chat.

1. Compare P01 e login nas duas versões, começando por perguntas. Veja os textos completos com o comando `prompt`.
2. Examine cada resposta pelo mesmo critério. Em clareza, identifique a frase mais fácil ou mais difícil de interpretar. Em adequação ao nível, observe se um leigo entenderia o vocabulário usado. Em acionabilidade, identifique qual decisão ou ação o leitor poderia tomar depois da resposta.
3. Use a escala 1 insuficiente, 2 fraco, 3 adequado, 4 bom e 5 excelente. Fundamente cada nota com uma passagem ou omissão específica. Registre empates ou piora quando ocorrerem.
4. Repita para os quatro tipos com `--tipo todos`. Compare P01 e P02 separadamente para observar a adaptação do nível com canal e estilo constantes. Para investigar o canal, use P03 e P05 com o mesmo ticket.
5. Vincule nas notas o JSON final avaliado e descreva um achado com os IDs das duas execuções, o trecho observado e a consequência para o cliente.

## Controle e limites

A comparação fixa o texto do ticket, o perfil, o tipo, o modelo solicitado, a temperatura, o limite de saída e o formato. O histórico inclui o modelo retornado, a origem da resposta e o hash do texto de instruções. Antes de interpretar um par, confira os identificadores de modelo retornados. O identificador do cache incorpora o conteúdo efetivo das mensagens e os parâmetros. Use `--novo` para repetições independentes da aplicação.

As alterações da v2 são avaliadas em conjunto. Uma comparação pequena permite discutir o comportamento naquele caso. A temperatura baixa ainda permite variação. Durante a atribuição de notas, a CLI oculta a versão e ordena o par pelos identificadores aleatórios das execuções. O candidato pode reconhecer uma estratégia pelo texto. Essa limitação permanece mesmo com os rótulos ocultos. O relatório revela as versões após a avaliação e expõe empates e regressões por critério. A CLI rejeita pares com diferenças no cenário ou na configuração e modelos retornados divergentes. Se a API omitir o identificador de modelo em ambas as respostas, só é possível confirmar o modelo solicitado.

### O que procurar ao ler as respostas

Os exemplos abaixo orientam a leitura. Uma resposta diferente pode merecer a mesma nota quando atende ao cliente e o avaliador consegue explicar por quê.

| Cenário | Sinal disponível | Pergunta para o avaliador |
|---|---|---|
| Login, diagnóstico | A conta continua acessível no celular | A resposta trata o acesso no celular como um sinal parcial ou afirma que a senha foi testada de novo? |
| Login, resolução | O cliente já fechou e abriu o navegador | O próximo teste separa causas possíveis e explica o que observar em seguida? |
| Microfone, perguntas | O cliente ouve os colegas e o ícone aparece ligado | A primeira pergunta investiga uma incerteza que muda a orientação, como qual entrada de áudio está selecionada? |
| Upload, fluxo | O arquivo menor foi enviado na mesma rede | O fluxo propõe um teste que o cliente consegue executar e evita presumir um limite de tamanho desconhecido? |

Para verificar personalização, mantenha ticket, versão e tipo fixos. Compare P01 e P02 quanto ao vocabulário, P03 e P05 quanto à viabilidade de ler a orientação em voz alta e P04 e P05 quanto ao detalhe da mensagem. Execute a comparação de versões separadamente para cada perfil.

## Estado das evidências

A [rodada de login](samples/login-ollama.json) contém oito respostas geradas pela API local do Ollama com `qwen2.5:3b`. Foram usados P01 (leigo, didático, chat), o ticket `login`, temperatura 0,2 e limite de 1.800 tokens. Cada par recebeu o mesmo esquema de saída. O [manifesto do modelo](samples/login-ollama-modelo.json) registra o identificador dos pesos. A [execução do experimento](https://github.com/Cassio327/suporte-claro-ai/actions/runs/44793023471) terminou com sucesso. Os oito registros têm origem `api`. As notas e justificativas foram concluídas e estão preservadas em [`samples/login-ollama-avaliado.json`](samples/login-ollama-avaliado.json). A consolidação numérica, a interpretação e os limites estão em [`RESULTADOS_EXPERIMENTO.md`](RESULTADOS_EXPERIMENTO.md).

<details>
<summary>Observações da revisão técnica — abrir depois da avaliação com versões ocultas</summary>

No passo a passo da v2, o segundo passo pede “Feche e abra o navegador novamente”. O ticket informa literalmente que o cliente já fez isso. O critério de verificação pergunta se a tela de login aparece, comportamento esperado tanto no caso normal quanto no relatado. Apesar da instrução para aproveitar os testes realizados, a resposta oferece pouca informação para decidir o próximo passo.

Nas perguntas, a primeira da v2 pede confirmação sobre mensagens de erro. O ticket já informa que o retorno à tela de login ocorre sem mensagem. Na v1, a terceira pergunta pede teste em outro dispositivo, embora o acesso no celular já seja conhecido. Em ambos os casos, caberia perguntar sobre uma condição ainda desconhecida que mude a orientação.

O fluxo da v1 sugere desligar temporariamente proteções do notebook. Essa orientação é inadequada para este cenário e deve ser descartada na revisão do atendimento. O exemplo é preservado como evidência do comportamento original do modelo.

O próximo experimento pode testar uma instrução curta que peça um teste reversível ainda não realizado, com dois resultados observáveis e encaminhamentos diferentes, e que proíba desativar proteções. Manter as respostas desta rodada e validar qualquer mudança em um segundo ticket inédito. Essas observações técnicas não atribuem notas ao candidato nem permitem generalizar a superioridade de uma versão.

</details>

## Revisão do passo a passo (v3)

No teste de áudio com P02, a resolução v2 passou do microfone para a câmera. A v3 restringe o primeiro teste à função que falhou e pede uma verificação que a pessoa consiga perceber ao usar essa função. Conserva o contrato JSON e as instruções de nível, estilo e canal. Essa versão só se aplica à resolução. O histórico mantém os prompts v1 e v2 reproduzíveis.

Antes da segunda rodada, definimos duas verificações: no áudio, observar se o teste volta a tratar da entrada de som; no upload, conferir se o resultado do teste distingue o envio bem-sucedido de uma nova interrupção. O ticket de upload permite observar a mesma instrução em um problema diferente. A leitura técnica está em [Resultados do experimento](RESULTADOS_EXPERIMENTO.md).

## Como isolar canal e estilo

Para o mesmo ticket de upload, P03 e P05 compartilham nível intermediário e estilo direto. Entre os atributos de comunicação, muda o canal. P05 e P04 compartilham nível e canal de e-mail. Muda o estilo. Cada perfil tem também um identificador diferente na entrada. Nos três casos foi usada a resolução v2. Antes da geração, registramos o que observar no [protocolo da rodada](https://github.com/Cassio327/suporte-claro-ai/pull/6).

Para telefone, procure uma pergunta que o atendente consiga dizer e que o cliente possa responder enquanto executa o teste. Para e-mail, verifique se é possível executar o teste e interpretar o resultado sem pedir outra instrução. Para o estilo detalhado, procure uma explicação útil do que o teste permite distinguir. Uma resposta mais longa, por si só, não demonstra melhor adaptação. A análise e os trechos gerados estão em [Resultados do experimento](RESULTADOS_EXPERIMENTO.md#canal-e-estilo-no-mesmo-ticket-de-upload).
