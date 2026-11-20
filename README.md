# Suporte Claro

Assistente de atendimento em português. Para um perfil e um ticket, a CLI gera diagnóstico, resolução, perguntas prioritárias ou fluxo de decisão. O comando de comparação executa as duas versões do prompt com a mesma entrada e grava as respostas para avaliação humana.

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

Os dois últimos comandos funcionam offline. Para gerar respostas, execute `cp .env.example .env` na primeira instalação. Abra o arquivo `.env` e preencha `GROQ_API_KEY` com sua chave. O modelo inicial é `openai/gpt-oss-20b`. Escolha outro modelo habilitado na sua conta se necessário. Consulte [os modelos da Groq](https://console.groq.com/docs/models).

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
cp -n samples/login-ollama.json historico/minha-avaliacao.json
python -m suporte avaliar historico/minha-avaliacao.json
python -m suporte relatorio historico/minha-avaliacao.json
```

O comando `avaliar` salva após cada resposta. Para retomar, execute-o novamente com a mesma cópia. Ao concluir, abra `historico/minha-avaliacao.html` e copie o JSON avaliado para `samples/login-ollama-avaliado.json` para incluir suas justificativas na entrega. As gerações são material para avaliação humana e incluem falhas de orientação.

```bash
python -m suporte comparar --perfil P01 --exemplo login --tipo todos
```

A CLI imprime o caminho da comparação. Execute `python -m suporte avaliar CAMINHO`, substituindo CAMINHO pelo arquivo mostrado. Para cada resposta, leia o ticket, o perfil e a saída. Atribua três notas de 1 a 5 e escreva sua justificativa para cada nota. O programa salva após cada resposta e retoma pela próxima pendente. A comparação contém as saídas originais, metadados e avaliações em um único JSON. Copie a comparação avaliada para `samples/` para incluí-la na entrega.

Com quatro conteúdos e duas versões, o cenário completo usa até oito chamadas em uma rodada sem cache. Se houver falha intermediária, ajuste a causa e repita o comando para aproveitar as gerações válidas já salvas. Para economizar quota, experimente primeiro `--tipo perguntas`, que compara apenas duas respostas.

Durante a avaliação, a CLI apresenta cada par como A e B em ordem sorteada pelos identificadores de execução. As letras valem para aquele tipo de conteúdo. A ordem permanece estável ao retomar. Para preservar a avaliação, abra o JSON com os identificadores de versão depois de concluir as notas.

Depois de avaliar, execute `python -m suporte relatorio CAMINHO`. Abra o HTML indicado no navegador para ler as respostas v1/v2 lado a lado e ver as justificativas. A última coluna calcula **nota da v2 menos nota da v1** em cada critério. Zero indica empate. O relatório abre offline, inclusive em outro computador. Para exportar de novo, use `--saida outro-nome.html`.

## Gerar uma comparação pelo GitHub

Também é possível fazer a rodada real pelo GitHub. Em **Settings → Secrets and variables → Actions**, cadastre o segredo de repositório `GROQ_API_KEY`. Em **Actions → Comparação real de prompts → Run workflow**, selecione `perguntas` para gerar o primeiro par do ticket de login com P01. Ao concluir, baixe e extraia o artefato `comparacao-login`. Na pasta do projeto, passe o caminho do JSON extraído ao comando `python -m suporte avaliar`. A leitura, a avaliação e a exportação do relatório funcionam offline. O workflow só inicia manualmente; uma nova execução faz novas chamadas.

## Organização

### Rodada com modelo local

Para gerar os quatro pares sem credencial de IA, abra **Actions → Experimento com modelo local → Run workflow**. O executor baixa o Qwen 2.5 de 3 bilhões de parâmetros, inicia o servidor Ollama no próprio executor e envia oito requisições à sua API. O artefato `rodada-local` contém a comparação e o identificador dos pesos usados. O processamento utiliza minutos de GitHub Actions. Esse experimento também executa ao abrir ou atualizar um PR do próprio repositório cuja branch começa com `experimento/`.

Em um computador com Ollama em execução, use:

```bash
ollama pull qwen2.5:3b
SUPORTE_PROVEDOR=ollama python -m suporte comparar --perfil P01 --exemplo login --tipo todos
```

Passe o arquivo de comparação ao comando `avaliar` para registrar a rubrica. Na apresentação, identifique qual provedor gerou cada par.

| Arquivo | Uso |
|---|---|
| `data/` | Cinco perfis fictícios e três tickets |
| `suporte/prompts.py` | Persona, instruções por tarefa, versão e adaptação ao perfil |
| `suporte/contratos.py` | Campos aceitos para cada saída e para as notas |
| `suporte/motor.py` | Requisição à Groq, validação, cache e gravação em JSON |
| `suporte/__main__.py` | Seleção de parâmetros, comparação e avaliação |
| `samples/exemplos_didaticos.json` | Quatro exemplos escritos à mão para explicar o formato e testar offline |
| `PROMPT_ENGINEERING_NOTES.md` | Desenho da comparação, hipóteses e limitações |

Arquivos locais ficam em `historico/execucoes/`, `historico/cache/` e `historico/comparacoes/`. Para outro destino, use `python -m suporte --pasta DESTINO comparar ...`. A aplicação se destina a um operador por pasta. Use tickets fictícios para as amostras do repositório.

## Verificação

```bash
python -m unittest discover -s tests -v
```

Os testes simulam a resposta HTTP para verificar cache, validação, comparação dos quatro conteúdos e persistência das notas. A qualidade das respostas do modelo precisa ser aferida com a rodada real e a rubrica do candidato.


## Resultado da rodada incluída

A avaliação humana da rodada com P01/login está concluída e preservada em [`samples/login-ollama-avaliado.json`](samples/login-ollama-avaliado.json). A v2 somou **27/60**, contra **24/60** da v1: melhora no fluxo (+5) e nas perguntas (+1), empate no diagnóstico e regressão na resolução (-3). Veja a interpretação, os controles e o próximo experimento em [`RESULTADOS_EXPERIMENTO.md`](RESULTADOS_EXPERIMENTO.md). O resultado é específico desta rodada; ele não é usado para alegar superioridade geral de uma versão.
