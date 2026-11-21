# Suporte Claro

Assistente de atendimento em português. Para um perfil e um ticket, a CLI gera diagnóstico, resolução, perguntas prioritárias ou fluxo de decisão. O comando de comparação executa as duas versões do prompt com a mesma entrada e grava as respostas para avaliação humana.

## Comece pela comparação avaliada

Após o setup abaixo, execute `python -m suporte painel` e abra **http://127.0.0.1:8765**. O painel inicia na resolução do ticket de login. Compare as duas respostas e abra **Notas e justificativas** para ver por que repetir a abertura do navegador reduziu a acionabilidade. O seletor também permite comparar os dois níveis técnicos no caso de áudio ou examinar a revisão experimental no upload.

Em **Novo atendimento**, escolha um dos cinco perfis, o conteúdo e a versão e escreva seu ticket. **Ver prévia do prompt** mostra as instruções exatas que o gerador montou. As comparações gravadas e a prévia funcionam offline. **Gerar resposta** usa a configuração de Groq ou Ollama descrita abaixo e mostra a origem (API ou cache), a saída e o caminho do JSON salvo. Prefira tickets fictícios para a demonstração. Encerre com Ctrl+C. Para outra porta, use `python -m suporte painel --porta 8766`.

[Resultados do experimento](RESULTADOS_EXPERIMENTO.md) reúne as conclusões. O [JSON avaliado](samples/login-ollama-avaliado.json) conserva as oito respostas do Qwen e as 24 notas com justificativas. No ticket de login, a resolução v2 repetiu a tentativa de reabrir o navegador. Nesse par, sua acionabilidade caiu de 3 para 1. O fluxo de decisão melhorou de 3/15 para 8/15.

No [teste de personalização e revisão](RESULTADOS_EXPERIMENTO.md#resolução-v3-o-que-mudou-no-atendimento), o mesmo modelo respondeu ao ticket de áudio para um cliente leigo e outro avançado. Uma revisão do prompt foi testada também no upload de arquivos.

## Executar no Linux

Com Git e Python 3.12 instalados:

```bash
git clone https://github.com/Cassio327/suporte-claro-ai.git
cd suporte-claro-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m suporte listar
python -m suporte prompt --perfil P01 --exemplo login --tipo diagnostico --versao v2
```

Após instalar as dependências, você pode abrir a comparação completa no navegador. Na raiz do projeto, execute uma vez:

```bash
mkdir -p historico
python -m suporte relatorio samples/login-ollama-avaliado.json --saida historico/relatorio-login.html
xdg-open historico/relatorio-login.html
```

A leitura do relatório, a listagem dos perfis e a inspeção dos prompts funcionam offline. O relatório preserva as respostas originais, inclusive a orientação inadequada sobre desativar proteções no fluxo v1. Para gerar respostas com a Groq, execute `cp .env.example .env` na primeira instalação. Abra o arquivo `.env` e preencha `GROQ_API_KEY` com sua chave. O modelo inicial é `openai/gpt-oss-20b`. Escolha outro modelo habilitado na sua conta se necessário. Consulte [os modelos da Groq](https://console.groq.com/docs/models).

```bash
python -m suporte gerar --perfil P01 --exemplo login --tipo diagnostico --versao v1
python -m suporte gerar --perfil P01 --exemplo login --tipo diagnostico --versao v1
python -m suporte gerar --perfil P03 --ticket "Meus colegas não me ouvem." --tipo fluxo
```

A segunda execução equivalente exibe `cache` e aponta para um novo registro com o ID da geração original. Para solicitar outra geração, acrescente `--novo`.

## Comparar e avaliar

**Avaliar uma rodada real já incluída.** A comparação com Qwen 2.5 contém oito respostas do mesmo ticket, geradas pela API durante a [execução no GitHub](https://github.com/Cassio327/suporte-claro-ai/actions/runs/44793023471). Para começar sem configurar uma chave ou baixar o modelo, ative o ambiente Python e execute:

```bash
mkdir -p historico
test -e historico/minha-avaliacao.json || cp samples/login-ollama.json historico/minha-avaliacao.json
python -m suporte avaliar historico/minha-avaliacao.json
python -m suporte relatorio historico/minha-avaliacao.json
```

O comando `avaliar` salva após cada resposta. Para retomar, execute-o novamente com a mesma cópia. Ao concluir, abra `historico/minha-avaliacao.html` para conferir as notas que você registrou. As gerações são material para avaliação humana e incluem falhas de orientação.

```bash
python -m suporte comparar --perfil P01 --exemplo login --tipo todos
```

A CLI imprime o caminho da comparação. Execute `python -m suporte avaliar CAMINHO`, substituindo CAMINHO pelo arquivo mostrado. Para cada resposta, leia o ticket, o perfil e a saída. Atribua três notas de 1 a 5 e escreva sua justificativa para cada nota. O programa salva após cada resposta e retoma pela próxima pendente. A comparação contém as saídas originais, metadados e avaliações em um único JSON.

Com quatro conteúdos e duas versões, o cenário completo usa até oito chamadas em uma rodada sem cache. Se houver falha intermediária, ajuste a causa e repita o comando para aproveitar as gerações válidas já salvas. Para economizar quota, experimente primeiro `--tipo perguntas`, que compara apenas duas respostas.

Durante a avaliação, a CLI apresenta cada par como A e B em ordem sorteada pelos identificadores de execução. As letras valem para aquele tipo de conteúdo. A ordem permanece estável ao retomar. Para preservar a avaliação, abra o JSON com os identificadores de versão depois de concluir as notas.

Depois de avaliar, execute `python -m suporte relatorio CAMINHO`. Abra o HTML indicado no navegador para ler as duas respostas lado a lado e ver as justificativas. A última coluna mostra a diferença entre a candidata e a base na ordem da comparação (por padrão, v2 menos v1). Zero indica empate. O relatório abre offline, inclusive em outro computador. Para exportar de novo, use `--saida outro-nome.html`.

A versão experimental v3 se aplica ao passo a passo de resolução. Para comparar os dois prompts nessa tarefa, execute:

```bash
SUPORTE_PROVEDOR=ollama python -m suporte comparar --perfil P01 --exemplo upload --tipo resolucao --versoes v2 v3
```

## Gerar uma comparação pelo GitHub

Também é possível fazer a rodada real pelo GitHub. Em **Settings → Secrets and variables → Actions**, cadastre o segredo de repositório `GROQ_API_KEY`. Em **Actions → Comparação real de prompts → Run workflow**, selecione `perguntas` para gerar o primeiro par do ticket de login com P01. Ao concluir, baixe e extraia o artefato `comparacao-login`. Na pasta do projeto, passe o caminho do JSON extraído ao comando `python -m suporte avaliar`. A leitura, a avaliação e a exportação do relatório funcionam offline. O workflow só inicia manualmente; uma nova execução faz novas chamadas.

## Rodada com modelo local

Em **Actions → Experimento com modelo local → Run workflow**, escolha o cenário `login` para comparar versões, `audio` para gerar duas resoluções v2 (P01 e P02) ou `revisao` para testar a v3 de resolução em áudio e upload. O executor baixa o Qwen 2.5 de 3 bilhões de parâmetros, inicia o servidor Ollama no próprio executor e envia oito requisições para o cenário de login, duas para áudio ou três para a revisão. O artefato `rodada-local` contém os registros do cenário e o identificador dos pesos usados. O processamento utiliza minutos de GitHub Actions. Esse experimento também executa ao abrir ou atualizar um PR do próprio repositório cuja branch começa com `experimento/`.

Em um computador com Ollama em execução, use:

```bash
ollama pull qwen2.5:3b
SUPORTE_PROVEDOR=ollama python -m suporte comparar --perfil P01 --exemplo login --tipo todos
```

Passe o arquivo de comparação ao comando `avaliar` para registrar a rubrica. Na apresentação, identifique qual provedor gerou cada par.

## Arquitetura

A CLI carrega o perfil e o ticket e monta as mensagens da versão escolhida. O motor consulta o cache, chama o provedor quando necessário, valida o contrato da saída e grava o registro. A avaliação e o relatório leem esses registros localmente.

| Arquivo | Uso |
|---|---|
| `data/` | Cinco perfis fictícios e três tickets |
| `suporte/prompts.py` | Persona, instruções por tarefa, versão e adaptação ao perfil |
| `suporte/contratos.py` | Campos aceitos para cada saída e para as notas |
| `suporte/motor.py` | Requisição à Groq ou ao Ollama, validação, cache e gravação em JSON |
| `suporte/__main__.py` | Seleção de parâmetros, comparação e avaliação |
| `samples/exemplos_didaticos.json` | Quatro exemplos escritos à mão para explicar o formato e testar offline |
| `PROMPT_ENGINEERING_NOTES.md` | Desenho da comparação, hipóteses e limitações |

Arquivos locais ficam em `historico/execucoes/`, `historico/cache/` e `historico/comparacoes/`. Para outro destino, use `python -m suporte --pasta DESTINO comparar ...`. A aplicação se destina a um operador por pasta. Use tickets fictícios para as amostras do repositório.

## Verificação

```bash
python -m unittest discover -s tests -v
```

Os testes simulam a resposta HTTP para verificar cache, validação, comparação dos quatro conteúdos e persistência das notas. A qualidade das respostas do modelo precisa ser aferida com a rodada real e a rubrica do candidato.
