"""Validação de pares e leitura da avaliação humana."""
from html import escape
from pathlib import Path
from string import Template

from .contratos import Avaliacao, Perfil, TIPOS


CRITERIOS = {"clareza": "Clareza", "adequacao_ao_nivel": "Adequação ao nível",
             "acionabilidade": "Acionabilidade"}
TITULOS = {"diagnostico": "Diagnóstico", "resolucao": "Resolução",
           "perguntas": "Perguntas de esclarecimento", "fluxo": "Fluxo de decisão"}
CAMPOS = {"hipoteses": "Hipóteses", "evidencias": "Evidências",
          "dados_faltantes": "Dados faltantes", "conclusao_provavel": "Conclusão provável",
          "passos": "Passos", "acao": "Ação", "como_verificar": "Como verificar",
          "quando_encaminhar": "Quando encaminhar", "perguntas_em_ordem": "Por prioridade",
          "pergunta": "Pergunta", "decisao_que_orienta": "Decisão que orienta",
          "condicao_observavel": "Condição", "se_sim": "Se sim", "se_nao": "Se não",
          "se_inconclusivo": "Se o teste for inconclusivo"}


def pares(documento):
    """Um cenário por documento e exatamente uma resposta de cada versão por tipo."""
    itens = documento.get("resultados") if isinstance(documento, dict) else None
    if not isinstance(itens, list) or not itens:
        raise ValueError("O arquivo precisa conter uma comparação com resultados.")
    grupos = {}
    ids = set()
    cenario = None
    for item in itens:
        if not isinstance(item, dict):
            raise ValueError("Registro de execução inválido.")
        tipo, versao = item.get("tipo"), item.get("versao")
        if tipo not in TIPOS or versao not in ("v1", "v2"):
            raise ValueError("Tipo ou versão de prompt desconhecidos.")
        Perfil.model_validate(item["perfil"])
        TIPOS[tipo].model_validate(item["saida"])
        if item["avaliacao"] is not None:
            Avaliacao.model_validate(item["avaliacao"])
        contexto = [item[k] for k in ("perfil", "ticket", "provedor", "configuracao")]
        if cenario is not None and contexto != cenario:
            raise ValueError("As entradas, o provedor ou a configuração diferem na comparação.")
        cenario = contexto
        grupo = grupos.setdefault(tipo, {})
        if item["id"] in ids or versao in grupo:
            raise ValueError("Execução ou versão duplicada no mesmo par.")
        ids.add(item["id"])
        grupo[versao] = item
    for grupo in grupos.values():
        if set(grupo) != {"v1", "v2"}:
            raise ValueError("Cada tipo precisa de uma resposta v1 e outra v2.")
        if grupo["v1"]["modelo_retornado"] != grupo["v2"]["modelo_retornado"]:
            raise ValueError("O provedor retornou modelos diferentes no mesmo par.")
    return grupos


def conteudo(valor):
    if isinstance(valor, dict):
        return "<dl>" + "".join(
            f"<dt>{escape(CAMPOS.get(k, k))}</dt><dd>{conteudo(v)}</dd>"
            for k, v in valor.items()) + "</dl>"
    if isinstance(valor, list):
        if not valor:
            return "<em>Nenhum item.</em>"
        return "<ol>" + "".join(f"<li>{conteudo(v)}</li>" for v in valor) + "</ol>"
    return escape(str(valor))


def relatorio(documento):
    grupos = pares(documento)
    secoes = []
    for tipo, grupo in grupos.items():
        a, b = grupo["v1"], grupo["v2"]
        if any(item["avaliacao"] is None for item in (a, b)):
            raise ValueError("Conclua a rubrica com o comando avaliar antes de revelar as versões.")
        linhas = []
        for chave, titulo in CRITERIOS.items():
            notas = [i["avaliacao"][chave] for i in (a, b)]
            celulas = "".join(f"<td><b>{n['nota']}/5</b> · {escape(n['justificativa'])}</td>" for n in notas)
            delta = notas[1]["nota"] - notas[0]["nota"]
            linhas.append(f"<tr><th scope='row'>{titulo}</th>{celulas}<td>{delta:+d}</td></tr>")
        cartoes = "".join(
            f"<article><h3>Prompt {v}</h3>{conteudo(grupo[v]['saida'])}"
            f"<small>Execução {escape(grupo[v]['id'])} · {escape(grupo[v]['origem'])}</small></article>"
            for v in ("v1", "v2"))
        secoes.append(f"<section><h2>{TITULOS[tipo]}</h2><div class='par'>{cartoes}</div>"
                      "<table><caption>Avaliação do candidato</caption><thead><tr><th>Critério</th>"
                      "<th>v1</th><th>v2</th><th>v2 − v1</th></tr></thead>"
                      f"<tbody>{''.join(linhas)}</tbody></table></section>")
    contexto = documento["resultados"][0]
    perfil = " · ".join(escape(contexto["perfil"][k]) for k in ("id", "nivel", "estilo", "canal"))
    modelo = escape(contexto["configuracao"]["model"])
    pagina = Path(__file__).with_name("relatorio.html").read_text(encoding="utf-8")
    return Template(pagina).substitute(perfil=perfil, modelo=modelo,
                                       ticket=escape(contexto["ticket"]), secoes="".join(secoes))
