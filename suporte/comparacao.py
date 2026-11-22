"""Validação de pares e leitura da avaliação humana."""
from html import escape
from pathlib import Path
from string import Template
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from .contratos import Avaliacao, Perfil, Texto, TIPOS


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


class RegistroComparado(BaseModel):
    """Campos necessários à avaliação de históricos, inclusive os de rodadas antigas."""
    model_config = ConfigDict(strict=True)

    id: Texto
    perfil: Perfil
    ticket: Texto
    tipo: Literal["diagnostico", "resolucao", "perguntas", "fluxo"]
    versao: Literal["v1", "v2", "v3"]
    provedor: Texto
    configuracao: dict[str, Any]
    modelo_retornado: Texto | None
    origem: Literal["api", "cache"]
    saida: dict[str, Any]
    avaliacao: Avaliacao | None


def pares(documento):
    """Um cenário por documento e exatamente uma resposta de cada versão por tipo."""
    itens = documento.get("resultados") if isinstance(documento, dict) else None
    if not isinstance(itens, list) or not itens:
        raise ValueError("O arquivo precisa conter uma comparação com resultados.")
    versoes = documento.get("versoes", ["v1", "v2"])
    if (not isinstance(versoes, list) or len(versoes) != 2
            or any(v not in ("v1", "v2", "v3") for v in versoes) or versoes[0] == versoes[1]):
        raise ValueError("A comparação precisa indicar duas versões distintas.")
    grupos = {}
    ids = set()
    cenario = None
    for item in itens:
        if not isinstance(item, dict):
            raise ValueError("Registro de execução inválido.")
        try:
            registro = RegistroComparado.model_validate(item)
        except ValidationError as erro:
            campo = ".".join(str(parte) for parte in erro.errors()[0]["loc"])
            raise ValueError(f"Registro de execução com campo ausente ou inválido: {campo}.") from None
        modelo = registro.configuracao.get("model")
        if not isinstance(modelo, str) or not modelo.strip():
            raise ValueError("O registro precisa indicar o modelo solicitado na configuração.")
        tipo, versao = registro.tipo, registro.versao
        if versao not in versoes or (versao == "v3" and tipo != "resolucao"):
            raise ValueError("Tipo ou versão de prompt desconhecidos.")
        TIPOS[tipo].model_validate(item["saida"])
        contexto = [item[k] for k in ("perfil", "ticket", "provedor", "modelo_retornado")]
        contexto.append({k: v for k, v in item["configuracao"].items() if k != "response_format"})
        if cenario is not None and contexto != cenario:
            raise ValueError("As entradas, o provedor, o modelo retornado ou a configuração diferem na comparação.")
        cenario = contexto
        grupo = grupos.setdefault(tipo, {})
        if item["id"] in ids or versao in grupo:
            raise ValueError("Execução ou versão duplicada no mesmo par.")
        ids.add(item["id"])
        grupo[versao] = item
    for grupo in grupos.values():
        if set(grupo) != set(versoes):
            raise ValueError("Cada tipo precisa de uma resposta de cada versão selecionada.")
        a, b = (grupo[v] for v in versoes)
        if a["configuracao"] != b["configuracao"]:
            raise ValueError("As configurações diferem entre as versões deste tipo.")
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
    base, candidata = documento.get("versoes", ["v1", "v2"])
    secoes = []
    for tipo, grupo in grupos.items():
        a, b = grupo[base], grupo[candidata]
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
            for v in (base, candidata))
        secoes.append(f"<section><h2>{TITULOS[tipo]}</h2><div class='par'>{cartoes}</div>"
                      "<table><caption>Avaliação do candidato</caption><thead><tr><th>Critério</th>"
                      f"<th>{base}</th><th>{candidata}</th><th>{candidata} − {base}</th></tr></thead>"
                      f"<tbody>{''.join(linhas)}</tbody></table></section>")
    contexto = documento["resultados"][0]
    perfil = " · ".join(escape(contexto["perfil"][k]) for k in ("id", "nivel", "estilo", "canal"))
    modelo = escape(contexto["configuracao"]["model"])
    pagina = Path(__file__).with_name("relatorio.html").read_text(encoding="utf-8")
    return Template(pagina).substitute(perfil=perfil, modelo=modelo,
                                       ticket=escape(contexto["ticket"]), secoes="".join(secoes))
