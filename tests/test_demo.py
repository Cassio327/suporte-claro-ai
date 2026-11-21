import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from suporte.__main__ import RAIZ
from suporte.contratos import Perfil
from suporte.demo import exportar
from suporte.motor import ler
from suporte.prompts import mensagens


class TesteDemonstracao(TestCase):
    def test_exportacao_reproduz_as_avaliacoes_e_as_instrucoes(self):
        with TemporaryDirectory() as pasta:
            destino = Path(pasta)
            exportar(destino)
            inicial = (destino / "index.html").read_text()
            for nome in ("diagnostico", "index", "perguntas", "fluxo", "audio", "perfis", "upload", "canal", "estilo", "permissao-1", "permissao-2"):
                self.assertIn(f'href="{nome}.html"', inicial)
                self.assertEqual((destino / f"{nome}.html").read_text().count("<article>"), 2)
            self.assertEqual((destino / "relatorio.html").read_text().count("/5</b>"), 24)
            self.assertTrue((destino / "editor.js").is_file())
            catalogo = (destino / "instrucoes.js").read_text()
            dados = json.loads(catalogo.removeprefix("const catalogo = ").removesuffix(";\n"))
            perfis = [Perfil.model_validate(p) for p in ler(RAIZ / "data/perfis.json")]
            for p in perfis:
                self.assertEqual(dados["perfis"][p.id], p.model_dump())
                sistema = mensagens(p, "Ticket de teste", "resolucao", "v3")[0]["content"]
                self.assertEqual(dados["sistemas"][f"{p.id}/resolucao/v3"], sistema)
                self.assertNotIn(f"{p.id}/fluxo/v3", dados["sistemas"])
