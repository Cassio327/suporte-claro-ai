import argparse
import json
from pathlib import Path
from uuid import uuid4
from .comparacao import CRITERIOS, pares, relatorio
from .contratos import Avaliacao, Perfil, TIPOS
from .motor import agora, configuracao_ambiente, gerar, ler, salvar
from .prompts import mensagens

RAIZ = Path(__file__).resolve().parents[1]


def argumentos():
    parser = argparse.ArgumentParser(description="Suporte Claro | laboratório de prompts")
    parser.add_argument("--pasta", type=Path, default=Path("historico"), help="Destino dos registros")
    sub = parser.add_subparsers(dest="acao", required=True)
    sub.add_parser("listar", help="Ver perfis e tickets disponíveis")
    painel = sub.add_parser("painel", help="Abrir o laboratório web local")
    painel.add_argument("--porta", type=int, default=8765)
    for acao in ("prompt", "gerar", "comparar"):
        cmd = sub.add_parser(acao)
        cmd.add_argument("--perfil", required=True)
        grupo = cmd.add_mutually_exclusive_group(required=True)
        grupo.add_argument("--ticket")
        grupo.add_argument("--exemplo")
        cmd.add_argument("--tipo", choices=[*TIPOS, "todos"], default="diagnostico")
        if acao != "comparar":
            cmd.add_argument("--versao", choices=["v1", "v2", "v3"], default="v2")
        else:
            cmd.add_argument("--versoes", nargs=2, choices=["v1", "v2", "v3"], default=["v1", "v2"],
                             metavar=("BASE", "CANDIDATA"), help="Versões distintas na ordem da comparação")
        if acao != "prompt":
            cmd.add_argument("--novo", action="store_true", help="Ignorar o cache nesta execução")
    cmd = sub.add_parser("avaliar", help="Registrar notas e justificativas do candidato")
    cmd.add_argument("comparacao", type=Path)
    cmd = sub.add_parser("relatorio", help="Exportar respostas e notas lado a lado em HTML")
    cmd.add_argument("comparacao", type=Path)
    cmd.add_argument("--saida", type=Path, help="Novo arquivo .html (padrão: ao lado do JSON)")
    return parser.parse_args()


def mostrar(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def avaliar(caminho):
    documento = ler(caminho)
    grupos = pares(documento)
    # IDs aleatórios da geração dão uma ordem estável para retomar a avaliação.
    ordem = [item for grupo in grupos.values() for item in sorted(grupo.values(), key=lambda i: i["id"])]
    for indice, item in enumerate(ordem):
        if item["avaliacao"] is not None:
            continue
        rotulo = "AB"[indice % 2]
        print(f"\n{item['tipo']} · resposta {rotulo} | {item['perfil']}\n{item['ticket']}")
        mostrar(item["saida"])
        notas = {}
        for criterio in Avaliacao.model_fields:
            while True:
                valor = input(f"{CRITERIOS[criterio]} (1–5): ").strip()
                if valor in ("1", "2", "3", "4", "5"):
                    break
                print("Informe uma nota inteira de 1 a 5.")
            while True:
                motivo = input("Sua justificativa: ").strip()
                if motivo:
                    break
                print("Explique sua nota com um trecho da resposta ou uma omissão.")
            notas[criterio] = {"nota": int(valor), "justificativa": motivo}
        item["avaliacao"] = Avaliacao.model_validate(notas).model_dump()
        item["avaliado_em"] = agora()
        salvar(caminho, documento)
    print(f"Avaliação salva em {caminho}")


def principal():
    args = argumentos()
    if args.acao == "painel":
        from .painel import servir
        servir(RAIZ, args.pasta, args.porta)
        return
    if args.acao == "relatorio":
        destino = args.saida or args.comparacao.with_suffix(".html")
        if destino.suffix.lower() != ".html":
            raise ValueError("Escolha um novo arquivo com extensão .html.")
        pagina = relatorio(ler(args.comparacao))
        with destino.open("x", encoding="utf-8") as arquivo:
            arquivo.write(pagina)
        print(f"Relatório salvo em {destino}")
        return
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
    provedor, modelo = configuracao_ambiente(RAIZ)
    versoes = args.versoes if args.acao == "comparar" else [args.versao]
    if len(set(versoes)) != len(versoes):
        raise ValueError("Escolha duas versões distintas para a comparação.")
    if "v3" in versoes and args.tipo != "resolucao":
        raise ValueError("Use --tipo resolucao para a versão experimental v3.")
    resultados = []
    for tipo in TIPOS if args.tipo == "todos" else [args.tipo]:
        if args.acao == "comparar":
            print(f"Comparando o par de {tipo}…", flush=True)
        for versao in versoes:
            if args.acao == "prompt":
                mostrar(mensagens(perfil, ticket.strip(), tipo, versao))
                continue
            item = gerar(args.pasta, perfil, ticket, tipo, versao, modelo, args.novo, provedor=provedor)
            resultados.append(item)
            if args.acao == "gerar":
                print(f"{tipo} / {versao} ({item['origem']})")
                mostrar(item["saida"])
                print("Salvo em", args.pasta / "execucoes" / (item["id"] + ".json"))
        if args.acao == "comparar":
            print(f"Duas respostas de {tipo} registradas.", flush=True)
    if args.acao == "comparar":
        caminho = args.pasta / "comparacoes" / (uuid4().hex + ".json")
        documento = {"timestamp": agora(), "versoes": versoes, "resultados": resultados}
        pares(documento)
        salvar(caminho, documento)
        print(f"Comparação salva em {caminho}")


if __name__ == "__main__":
    try:
        principal()
    except (ValueError, OSError, EOFError, KeyError) as erro:
        raise SystemExit(f"Erro: {erro}") from None

