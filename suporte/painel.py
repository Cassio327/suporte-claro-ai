"""Laboratório local de atendimento. A consulta aos experimentos funciona offline."""
import json
import secrets
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from .comparacao import CRITERIOS, TITULOS, conteudo, pares
from .contratos import Perfil
from .motor import configuracao_ambiente, gerar, ler
from .prompts import mensagens


def opcoes(itens, atual):
    return "".join(f'<option value="{escape(k)}" {"selected" if k == atual else ""}>{escape(v)}</option>'
                   for k, v in itens.items())


def cartao(r):
    p = r["perfil"]
    identificacao = f"{p['id']} · {p['nivel']} · {p['estilo']} · {p['canal']}"
    notas = r.get("avaliacao")
    rubrica = ""
    if notas:
        cab = "".join(f"<dt>{rotulo}</dt><dd><strong>{notas[k]['nota']}/5</strong>"
                      f" · {escape(notas[k]['justificativa'])}</dd>" for k, rotulo in CRITERIOS.items())
        rubrica = f"<details><summary>Notas e justificativas</summary><dl>{cab}</dl></details>"
    registro = escape(json.dumps(r, ensure_ascii=False, indent=2))
    return (f"<article><header><h2>Prompt {escape(r['versao'])}</h2><p>{escape(identificacao)}</p></header>"
            f"{conteudo(r['saida'])}{rubrica}<details><summary>Registro JSON</summary><pre>{registro}</pre>"
            f"</details></article>")


class Laboratorio:
    def __init__(self, raiz, pasta):
        self.pasta = pasta
        self.chave = secrets.token_urlsafe(32)
        self.trava = Lock()
        self.provedor, self.modelo = configuracao_ambiente(raiz)
        self.perfis = {p["id"]: Perfil.model_validate(p) for p in ler(raiz / "data/perfis.json")}
        self.tickets = ler(raiz / "data/tickets.json")
        self.css = (raiz / "suporte/painel.css").read_text(encoding="utf-8")
        arq = raiz / "samples"
        login = pares(ler(arq / "login-ollama-avaliado.json"))
        self.casos = {k: (f"Login · {TITULOS[k]}", [v["v1"], v["v2"]]) for k, v in login.items()}
        audio = ler(arq / "audio-perfis-v2.json")["resultados"]
        avancado = next(r for r in audio if r["perfil"]["id"] == "P02")
        self.casos["perfis"] = ("Áudio · comparar níveis técnicos", audio)
        self.casos["audio"] = ("Áudio · revisar o prompt", [avancado, ler(arq / "audio-P02-v3.json")])
        upload = pares(ler(arq / "upload-v2-v3.json"))["resolucao"]
        self.casos["upload"] = ("Upload · revisar o prompt", [upload["v2"], upload["v3"]])

        comunicacao = ler(arq / "upload-comunicacao-v2.json")["resultados"]
        por_perfil = {item["perfil"]["id"]: item for item in comunicacao}
        self.casos["canal"] = ("Upload · telefone e e-mail", [por_perfil["P03"], por_perfil["P05"]])
        self.casos["estilo"] = ("Upload · e-mail direto e detalhado", [por_perfil["P05"], por_perfil["P04"]])

    navegacao = (("/", "Experimentos"), ("/atender", "Novo atendimento"))

    def pagina(self, titulo, corpo, ativa):
        links = "".join(f'<a href="{path}"' + (' aria-current="page"' if path == ativa else '')
                        + f'>{label}</a>' for path, label in self.navegacao)
        return (f'<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{titulo} | Suporte Claro</title>'
                f'<style>{self.css}</style><body><a class="skip" href="#principal">Ir para o conteúdo</a>'
                f'<header class="topo"><div><b>Suporte Claro</b><nav aria-label="Principal">{links}</nav></div></header>'
                f'<main id="principal"><h1>{titulo}</h1>{corpo}</main></body></html>')

    def filtro(self, nomes, caso):
        return f'<form class="filtro"><label>Experimento<select name="caso">{opcoes(nomes, caso)}</select></label><button>Ver comparação</button></form>'

    def comparar(self, caso):
        if caso not in self.casos:
            raise ValueError("Experimento desconhecido.")
        nome, registros = self.casos[caso]
        a, b = registros
        nomes = {k: v[0] for k, v in self.casos.items()}
        filtro = self.filtro(nomes, caso)
        modelo = escape(a["modelo_retornado"] or a["configuracao"]["model"])
        contexto = f'<section class="ticket"><b>Ticket do cliente</b><blockquote>{escape(a["ticket"])}</blockquote><small>{modelo} · Duas respostas registradas</small></section>'
        if a["avaliacao"] and b["avaliacao"]:
            linhas = "".join(f"<tr><th scope='row'>{rotulo}</th><td>{a['avaliacao'][k]['nota']}/5</td>"
                             f"<td>{b['avaliacao'][k]['nota']}/5</td></tr>" for k, rotulo in CRITERIOS.items())
            conclusao = (f"<table><caption>Rubrica registrada</caption><thead><tr><th>Critério</th>"
                         f"<th>{escape(a['versao'])}</th><th>{escape(b['versao'])}</th></tr></thead><tbody>{linhas}</tbody></table>")
        else:
            conclusao = "<p class='nota'>Esta rodada tem análise qualitativa. As respostas abaixo estão preservadas sem notas numéricas.</p>"
        if caso == "fluxo":
            conclusao += "<p class='aviso'>Na v1, a sugestão de desativar proteções foi identificada como inadequada na revisão.</p>"
        pares_html = "".join(cartao(r) for r in registros)
        return self.pagina("Comparar respostas", filtro + contexto + conclusao +
                           f'<section class="par" aria-label="{escape(nome)}">{pares_html}</section>', "/")

    def formulario(self, dados=None, resultado=""):
        d = dados or {}
        ps = {k: f"{k} · {p.nivel} · {p.estilo} · {p.canal}" for k, p in self.perfis.items()}
        formulario = f"""<form class="editor" method="post" action="/atender">
<input type="hidden" name="chave" value="{self.chave}">
<div class="campos"><label>Perfil<select name="perfil">{opcoes(ps, d.get("perfil","P01"))}</select></label>
<label>Conteúdo<select name="tipo">{opcoes(TITULOS, d.get("tipo","resolucao"))}</select></label>
<label>Versão<select name="versao">{opcoes({"v1":"v1","v2":"v2","v3":"v3 · resolução"},d.get("versao","v2"))}</select></label></div>
<label>Ticket do cliente<textarea name="ticket" required maxlength="8000" rows="4">{escape(d.get("ticket", self.tickets["login"]))}</textarea></label>
<p class="nota">A prévia mostra as instruções e o ticket. Gerar consulta o cache e, quando necessário, envia o ticket ao provedor {escape(self.provedor)}.</p>
<div class="acoes"><button name="acao" value="prompt">Ver prévia do prompt</button><button class="primario" name="acao" value="gerar">Gerar resposta</button></div>
</form>"""
        return self.pagina("Novo atendimento", formulario + resultado, "/atender")

    def atender(self, dados):
        perfil = self.perfis.get(dados.get("perfil"))
        ticket = dados.get("ticket", "").strip()
        tipo, versao = dados.get("tipo"), dados.get("versao")
        if not perfil or tipo not in TITULOS or versao not in ("v1", "v2", "v3"):
            raise ValueError("Confira o perfil, o conteúdo e a versão.")
        if not 1 <= len(ticket) <= 8000:
            raise ValueError("Informe um ticket entre 1 e 8000 caracteres.")
        if dados.get("acao") == "prompt":
            msgs = mensagens(perfil, ticket, tipo, versao)
            return self.formulario(dados, '<section class="resultado"><h2>Prévia do prompt</h2>' +
                                   "".join(f"<h3>{escape(m['role'])}</h3><pre>{escape(m['content'])}</pre>" for m in msgs) + "</section>")
        if dados.get("acao") != "gerar":
            raise ValueError("Ação desconhecida.")
        with self.trava:
            item = gerar(self.pasta, perfil, ticket, tipo, versao, self.modelo, provedor=self.provedor)
        caminho = self.pasta / "execucoes" / (item["id"] + ".json")
        return self.formulario(dados, f'<section class="resultado"><h2>Resposta gerada</h2><p>Origem: {escape(item["origem"])} · '
                               f'Salvo em <code>{escape(str(caminho))}</code></p>{cartao(item)}</section>')


def servidor(raiz, pasta, porta):
    if not 0 <= porta <= 65535:
        raise ValueError("Porta inválida.")
    lab = Laboratorio(raiz, pasta)

    class Handler(BaseHTTPRequestHandler):
        def enviar(self, html, status=200):
            dados = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(dados)

        def local(self):
            porta_real = self.server.server_port
            return self.headers.get("Host") in (f"127.0.0.1:{porta_real}", f"localhost:{porta_real}")

        def do_GET(self):
            if not self.local():
                return self.send_error(403)
            url = urlsplit(self.path)
            if url.path == "/atender":
                return self.enviar(lab.formulario())
            if url.path != "/":
                return self.send_error(404)
            try:
                caso = parse_qs(url.query, max_num_fields=3).get("caso", ["resolucao"])[0]
                self.enviar(lab.comparar(caso))
            except ValueError:
                self.send_error(400, "Experimento invalido")

        def do_POST(self):
            if not self.local():
                return self.send_error(403)
            if self.path != "/atender":
                return self.send_error(404)
            if self.headers.get_content_type() != "application/x-www-form-urlencoded":
                return self.send_error(415)
            try:
                tamanho = int(self.headers.get("Content-Length", "0"))
                if not 0 < tamanho <= 128_000:
                    return self.send_error(413)
                campos = parse_qs(self.rfile.read(tamanho).decode(), keep_blank_values=True, max_num_fields=8)
                d = {k: v[0] for k, v in campos.items() if len(v) == 1}
                if not secrets.compare_digest(d.pop("chave", "").encode(), lab.chave.encode()):
                    return self.send_error(403)
            except (UnicodeError, ValueError):
                return self.send_error(400)
            try:
                self.enviar(lab.atender(d))
            except (ValueError, OSError) as erro:
                self.enviar(lab.formulario(d, f'<p class="aviso" role="alert">{escape(str(erro))}</p>'), 400)

    return ThreadingHTTPServer(("127.0.0.1", porta), Handler)


def servir(raiz, pasta, porta):
    with servidor(raiz, pasta, porta) as http:
        print(f"Suporte Claro em http://127.0.0.1:{http.server_port} · Ctrl+C para encerrar.", flush=True)
        try:
            http.serve_forever()
        except KeyboardInterrupt:
            pass
