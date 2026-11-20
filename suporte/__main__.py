import argparse
import json
import os
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv
from .contratos import Avaliacao, Perfil, TIPOS
from .motor import agora, gerar, ler, salvar
from .prompts import mensagens

RAIZ = Path(__file__).resolve().parents[1]


def argumentos():
    parser = argparse.ArgumentParser(description="Suporte Claro | laboratório de prompts")
    parser.add_argument("--pasta", type=Path, default=Path("historico"), help="Destino dos registros")
    sub = parser.add_subparsers(dest="acao", required=True)
    sub.add_parser("listar", help="Ver perfis e tickets disponíveis")
    for acao in ("prompt", "gerar", "comparar"):
        cmd = sub.add_parser(acao)
        cmd.add_argument("--perfil", required=True)
        grupo = cmd.add_mutually_exclusive_group(required=True)
        grupo.add_argument("--ticket")
        grupo.add_argument("--exemplo")
        cmd.add_argument("--tipo", choices=[*TIPOS, "todos"], default="diagnostico")
        if acao != "comparar":
            cmd.add_argument("--versao", choices=["v1", "v2"], default="v2")
        if acao != "prompt":
            cmd.add_argument("--novo", action="store_true", help="Ignorar o cache nesta execução")
    cmd = sub.add_parser("avaliar", help="Registrar notas e justificativas do candidato")
    cmd.add_argument("comparacao", type=Path)
    return parser.parse_args()


def mostrar(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def avaliar(caminho):
    documento = ler(caminho)
    for item in documento["resultados"]:
        if item["avaliacao"] is not None:
            continue
        print(f"\n{item['tipo']} / {item['versao']} | {item['perfil']}\n{item['ticket']}")
        mostrar(item["saida"])
        notas = {}
        for criterio in Avaliacao.model_fields:
            while True:
                valor = input(f"{criterio} (1–5): ").strip()
                motivo = input("Sua justificativa: ").strip()
                if valor in ("1", "2", "3", "4", "5") and motivo:
                    break
                print("Informe uma nota inteira de 1 a 5 e uma justificativa.")
            notas[criterio] = {"nota": int(valor), "justificativa": motivo}
        item["avaliacao"] = Avaliacao.model_validate(notas).model_dump()
        item["avaliado_em"] = agora()
        salvar(caminho, documento)
    print(f"Avaliação salva em {caminho}")


def principal():
    args = argumentos()
    if args.acao == "avaliar":
        avaliar(args.comparacao)
        return
    perfis = [Perfil.model_validate(p) for p in ler(RAIZ / "data/perfis.json")]
    tickets = ler(RAIZ / "data/tickets.json")
    if args.acao == "listar":
        mostrar({"perfis": [p.model_dump() for p in perfis], "tickets": tickets})
        return
    perfil = next((p for p in perfis if p.id == args.perfil), None)
    if not perfil:
        raise ValueError("Perfil desconhecido. Consulte o comando listar.")
    ticket = args.ticket if args.ticket is not None else tickets.get(args.exemplo)
    if not ticket or not 1 <= len(ticket.strip()) <= 8000:
        raise ValueError("Informe um ticket válido ou um exemplo exibido por listar.")
    load_dotenv(RAIZ / ".env")
    modelo = os.getenv("GROQ_MODEL", "").strip()
    resultados = []
    for tipo in TIPOS if args.tipo == "todos" else [args.tipo]:
        for versao in (["v1", "v2"] if args.acao == "comparar" else [args.versao]):
            if args.acao == "prompt":
                mostrar(mensagens(perfil, ticket.strip(), tipo, versao))
                continue
            item = gerar(args.pasta, perfil, ticket, tipo, versao, modelo, args.novo)
            resultados.append(item)
            print(f"{tipo} / {versao} ({item['origem']})")
            mostrar(item["saida"])
            print("Salvo em", args.pasta / "execucoes" / (item["id"] + ".json"))
    if args.acao == "comparar":
        caminho = args.pasta / "comparacoes" / (uuid4().hex + ".json")
        salvar(caminho, {"timestamp": agora(), "resultados": resultados})
        print(f"Comparação salva em {caminho}")


if __name__ == "__main__":
    try:
        principal()
    except (ValueError, OSError, EOFError, KeyError) as erro:
        raise SystemExit(f"Erro: {erro}") from None

