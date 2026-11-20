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

As alterações da v2 são avaliadas em conjunto. Uma comparação pequena permite discutir o comportamento naquele caso. A temperatura baixa ainda permite variação e a avaliação por uma pessoa que conhece a versão tem viés. Um passo posterior é avaliar pares com rótulos ocultos e repetir em tickets inéditos.

## Estado das evidências

A primeira versão inclui exemplos didáticos e testes offline. A rodada real com a API e as justificativas do candidato estão pendentes. O arquivo final da comparação deve guardar as saídas integrais e as notas registradas com o comando avaliar.

