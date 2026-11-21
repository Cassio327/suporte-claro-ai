"""Exporta o painel de experimentos fictícios para hospedagem estática."""
import argparse
import json
from html import escape
from pathlib import Path

from .__main__ import RAIZ
from .comparacao import CRITERIOS, TITULOS, conteudo, relatorio
from .motor import ler
from .painel import Laboratorio, opcoes
from .prompts import mensagens

REPOSITORIO = "https://github.com/Cassio327/suporte-claro-ai"


class Demonstracao(Laboratorio):
    navegacao = (("index.html", "Experimentos"), ("prompt.html", "Testar prompt"),
                 ("avaliar-upload.html", "Avaliar upload"), ("relatorio.html", "Relatório"), (REPOSITORIO, "GitHub"))

    def pagina(self, titulo, corpo, ativa):
        pagina_ativa = "index.html" if ativa == "/" else ativa
        return super().pagina(titulo, corpo, pagina_ativa)

    def filtro(self, nomes, caso):
        links = []
        for chave, rotulo in nomes.items():
            caminho = "index.html" if chave == "resolucao" else f"{chave}.html"
            ativo = ' aria-current="page"' if chave == caso else ""
            links.append(f'<a href="{caminho}"{ativo}>{escape(rotulo)}</a>')
        return ('<p>Explore respostas reais do modelo para tickets fictícios. '
                'Os quatro casos de login incluem as notas e justificativas do candidato.</p>'
                '<nav class="casos" aria-label="Escolher experimento">' + "".join(links) + '</nav>')

    def avaliar_upload(self, amostra):
        registros = sorted(amostra["resultados"], key=lambda item: item["id"])
        opcoes_nota = '<option value="">Escolha</option>' + "".join(
            f'<option value="{n}">{n}</option>' for n in range(1, 6))
        cartoes = []
        for letra, item in zip("AB", registros, strict=True):
            campos = []
            for chave, nome in CRITERIOS.items():
                prefixo = f"{item['id']}-{chave}"
                campos.append(f'<fieldset><legend>{escape(nome)}</legend><label>Nota de 1 a 5'
                              f'<select required name="{prefixo}-nota">{opcoes_nota}</select></label>'
                              f'<label>Por que essa nota?<textarea required name="{prefixo}-motivo" rows="2">'
                              '</textarea></label></fieldset>')
            cartoes.append(f'<article><h2>Resposta {letra}</h2>{conteudo(item["saida"])}'
                           f'{"".join(campos)}</article>')
        # JSON dentro de um elemento script não pode conter um fechamento de tag literal.
        original = json.dumps(amostra, ensure_ascii=False).replace("<", r"\u003c")
        corpo = (f'<section class="ticket"><b>P01 · leigo · didático · chat</b>'
                 f'<blockquote>{escape(registros[0]["ticket"])}</blockquote></section>'
                 '<p>Leia as duas respostas e justifique cada nota com um trecho ou uma omissão. '
                 'A escala vai de 1 (insuficiente) a 5 (excelente). As versões aparecem após a avaliação. '
                 'As suas notas ficam no arquivo que você baixar.</p>'
                 '<form id="rubrica"><section class="par">' + "".join(cartoes) + '</section>'
                 '<button class="primario">Baixar minha avaliação</button></form>'
                 '<p id="conclusao" role="status"></p>'
                 f'<script id="amostra" type="application/json">{original}</script>'
                 '<script src="rubrica.js" defer></script>')
        return self.pagina("Avaliar respostas de upload", corpo, "avaliar-upload.html")

    def editor(self):
        perfis = {k: f"{k} · {p.nivel} · {p.estilo} · {p.canal}" for k, p in self.perfis.items()}
        corpo = f"""
<p>Escolha um perfil e escreva um ticket para inspecionar as mensagens que seriam enviadas ao modelo.
A prévia é montada no seu navegador. Para gerar uma nova resposta com Groq ou Ollama,
siga as <a href="{REPOSITORIO}#executar-no-linux">instruções de execução local</a>.</p>
<form class="editor" id="editor"><div class="campos">
<label>Perfil<select id="perfil">{opcoes(perfis, "P01")}</select></label>
<label>Conteúdo<select id="tipo">{opcoes(TITULOS, "resolucao")}</select></label>
<label>Versão<select id="versao">{opcoes({"v1":"v1","v2":"v2","v3":"v3 · resolução"}, "v2")}</select></label></div>
<label>Ticket do cliente<textarea id="ticket" maxlength="8000" rows="4" required>{escape(self.tickets["login"])}</textarea></label>
<div class="acoes"><button class="primario">Ver prévia do prompt</button></div></form>
<section class="resultado" id="resultado" hidden><h2 tabindex="-1">Prévia do prompt</h2>
<h3>Instruções do sistema</h3><pre id="sistema"></pre><h3>Dados do atendimento</h3><pre id="dados"></pre></section>
<script src="instrucoes.js" defer></script><script src="editor.js" defer></script>
"""
        return self.pagina("Testar um prompt", corpo, "prompt.html")

    def exportar(self, destino):
        destino.mkdir(parents=True, exist_ok=True)
        self.css += """
.casos{gap:.4rem;padding:.2rem 0}.casos a{color:var(--teal);background:white;border:1px solid var(--line)}
.casos a[aria-current]{background:var(--teal);color:white}.editor .acoes,#rubrica button{margin-top:1rem}#rubrica fieldset{margin:.8rem 0;border:1px solid var(--line);min-width:0}#rubrica label{margin:.5rem 0}
"""
        for caso in self.casos:
            nome = "index" if caso == "resolucao" else caso
            (destino / f"{nome}.html").write_text(self.comparar(caso), encoding="utf-8")
        amostra = ler(RAIZ / "samples/upload-v2-v3.json")
        (destino / "avaliar-upload.html").write_text(self.avaliar_upload(amostra), encoding="utf-8")
        (destino / "rubrica.js").write_bytes(Path(__file__).with_name("demo-rubrica.js").read_bytes())
        (destino / "prompt.html").write_text(self.editor(), encoding="utf-8")
        dados = {"perfis": {}, "sistemas": {}}
        for perfil in self.perfis.values():
            dados["perfis"][perfil.id] = perfil.model_dump()
            for tipo in TITULOS:
                for versao in (("v1", "v2", "v3") if tipo == "resolucao" else ("v1", "v2")):
                    chave = f"{perfil.id}/{tipo}/{versao}"
                    dados["sistemas"][chave] = mensagens(perfil, "", tipo, versao)[0]["content"]
        (destino / "instrucoes.js").write_text("const catalogo = " + json.dumps(dados, ensure_ascii=False) + ";\n", encoding="utf-8")
        (destino / "editor.js").write_bytes(Path(__file__).with_name("demo-editor.js").read_bytes())


def exportar(destino):
    Demonstracao(RAIZ, destino).exportar(destino)
    documento = ler(RAIZ / "samples/login-ollama-avaliado.json")
    (destino / "relatorio.html").write_text(relatorio(documento), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destino", type=Path)
    exportar(parser.parse_args().destino)
