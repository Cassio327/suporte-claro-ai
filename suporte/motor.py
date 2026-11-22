import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError
from .contratos import TIPOS
from .prompts import mensagens

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
LOCAL = "http://127.0.0.1:11434/v1/chat/completions"


def configuracao_ambiente(raiz):
    load_dotenv(raiz / ".env")
    provedor = os.getenv("SUPORTE_PROVEDOR", "groq").strip().lower()
    modelo = (os.getenv("OLLAMA_MODEL", "qwen2.5:3b") if provedor == "ollama"
              else os.getenv("GROQ_MODEL", "")).strip()
    return provedor, modelo


def agora():
    return datetime.now(timezone.utc).isoformat()


def resumo(objeto):
    dados = json.dumps(objeto, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(dados.encode()).hexdigest()


def salvar(caminho, objeto):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", dir=caminho.parent, delete=False, encoding="utf-8") as arquivo:
        temporario = Path(arquivo.name)
        try:
            json.dump(objeto, arquivo, ensure_ascii=False, indent=2, allow_nan=False)
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        except BaseException:
            temporario.unlink(missing_ok=True)
            raise
    try:
        temporario.replace(caminho)
    finally:
        temporario.unlink(missing_ok=True)


def ler(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


def validar_modelo_retornado(valor):
    if valor is not None and (not isinstance(valor, str) or not valor.strip()):
        raise ValueError("Identificador de modelo inválido na resposta do provedor.")
    return valor


def consultar(payload, provedor="groq"):
    local = provedor == "ollama"
    headers = {}
    if not local:
        chave = os.getenv("GROQ_API_KEY", "").strip()
        if not chave:
            raise ValueError("Configure GROQ_API_KEY no .env para gerar uma resposta.")
        headers["Authorization"] = f"Bearer {chave}"
    try:
        resposta = httpx.post(LOCAL if local else ENDPOINT, json=payload,
                              timeout=180 if local else 40, headers=headers)
        resposta.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        dicas = {401: "Confira sua chave.", 429: "Aguarde o limite de uso ser liberado.",
                 400: "Confira o modelo escolhido e o suporte a JSON Object.", 403: "Confira as permissões do projeto."}
        raise ValueError(f"{provedor} retornou HTTP {status}. {dicas.get(status, 'Confira a disponibilidade da API.')}") from None
    except httpx.RequestError:
        raise ValueError("A API não respondeu. Verifique a conexão e tente novamente.") from None
    try:
        corpo = resposta.json()
        escolha = corpo["choices"][0]
        truncada = escolha.get("finish_reason") == "length"
        texto = escolha["message"]["content"]
    except (ValueError, TypeError, IndexError, KeyError, AttributeError):
        raise ValueError("Resposta da API sem conteúdo JSON utilizável.") from None
    if truncada:
        raise ValueError("Resposta truncada pelo limite de tokens. Revise o limite e repita as duas versões com a mesma configuração.")
    try:
        if not isinstance(texto, str):
            raise TypeError
        return json.loads(texto), corpo.get("model")
    except (ValueError, TypeError):
        raise ValueError("Resposta da API sem conteúdo JSON utilizável.") from None


def gerar(pasta, perfil, ticket, tipo, versao, modelo, novo=False, chamar=None, provedor="groq"):
    ticket = ticket.strip()
    if not 1 <= len(ticket) <= 8000:
        raise ValueError("Informe um ticket entre 1 e 8000 caracteres.")
    if provedor not in ("groq", "ollama"):
        raise ValueError("Escolha groq ou ollama em SUPORTE_PROVEDOR.")
    if not modelo.strip():
        raise ValueError("Configure um modelo ativo para o provedor selecionado.")
    msgs = mensagens(perfil, ticket, tipo, versao)
    config = {"model": modelo, "temperature": 0.2, "max_completion_tokens": 1800,
              "response_format": {"type": "json_object"}}
    if provedor == "ollama":
        config = {"model": modelo, "temperature": 0.2, "max_tokens": 1800,
                  "response_format": {"type": "json_schema", "json_schema": {
                      "name": tipo, "schema": TIPOS[tipo].model_json_schema()}}}
    payload = {**config, "messages": msgs}
    chave = resumo([LOCAL if provedor == "ollama" else ENDPOINT, tipo, versao, payload])
    contexto = {"perfil": perfil.model_dump(), "ticket": ticket, "tipo": tipo, "versao": versao,
                "provedor": provedor, "configuracao": config, "hash_prompt": resumo(msgs[0]["content"]),
                "chave_cache": chave}
    cache = pasta / "cache" / (chave + ".json")
    origem = None
    if cache.exists() and not novo:
        try:
            anterior = ler(cache)
            if any(anterior[campo] != valor for campo, valor in contexto.items()):
                raise ValueError("Contexto do cache incompatível com a requisição.")
            if anterior["origem"] != "api" or not isinstance(anterior["id"], str) or not anterior["id"].strip():
                raise ValueError("Identidade do registro incompatível.")
            saida = TIPOS[tipo].model_validate(anterior["saida"]).model_dump()
            modelo_retornado = validar_modelo_retornado(anterior["modelo_retornado"])
            origem = anterior["id"]
        except (ValueError, TypeError, KeyError):
            raise ValueError("Cache inválido. Use --novo para gerar novamente.") from None
    else:
        bruto, modelo_retornado = chamar(payload) if chamar else consultar(payload, provedor)
        validar_modelo_retornado(modelo_retornado)
        try:
            saida = TIPOS[tipo].model_validate(bruto).model_dump()
        except ValidationError as erro:
            campo = ".".join(map(str, erro.errors()[0]["loc"])) or "raiz"
            raise ValueError(f"Saída incompatível com o contrato de {tipo} no campo {campo}.") from None
    registro = {**contexto, "id": uuid4().hex, "timestamp": agora(), "modelo_retornado": modelo_retornado,
                "origem": "cache" if origem else "api", "execucao_original": origem,
                "saida": saida, "avaliacao": None}
    salvar(pasta / "execucoes" / (registro["id"] + ".json"), registro)
    if not origem:
        salvar(cache, registro)
    return registro

