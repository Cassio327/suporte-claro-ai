"""Exporta o painel de experimentos fictícios para hospedagem estática."""
import argparse
import json
from html import escape
from pathlib import Path

from .__main__ import RAIZ
from .comparacao import TITULOS, relatorio
from .motor import ler
from .painel import Laboratorio, opcoes
from .prompts import mensagens

REPOSITORIO = "https://github.com/Cassio327/suporte-claro-ai"


class Demonstracao(Laboratorio):
    navegacao = (("index.html", "Experimentos"), ("prompt.html", "Testar prompt"),
                 ("relatorio.html", "Relatório"), (REPOSITORIO, "GitHub"))

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
.casos a[aria-current]{background:var(--teal);color:white}.editor .acoes{margin-top:1rem}
"""
        for caso in self.casos:
            nome = "index" if caso == "resolucao" else caso
            (destino / f"{nome}.html").write_text(self.comparar(caso), encoding="utf-8")
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
