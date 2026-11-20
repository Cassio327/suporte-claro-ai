import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import httpx
from suporte.__main__ import RAIZ, principal
from suporte.contratos import Perfil, TIPOS
from suporte.motor import gerar, ler

EXEMPLOS = ler(RAIZ / "samples/exemplos_didaticos.json")
PERFIL = Perfil.model_validate(ler(RAIZ / "data/perfis.json")[0])


class TesteSuporte(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)

    def cli(self, *args):
        with patch("sys.argv", ["suporte", "--pasta", str(self.pasta), *args]), redirect_stdout(io.StringIO()):
            principal()

    def test_comparacao_completa_e_retomada_da_rubrica(self):
        # Exercita a CLI real. Apenas o transporte HTTP e o teclado são simulados.
        respostas = [EXEMPLOS[t] for t in TIPOS for _ in range(2)]
        def responder(url, *, json, **kwargs):
            corpo = {"model": "teste", "choices": [{"message": {"content": __import__("json").dumps(respostas.pop(0))}}]}
            return httpx.Response(200, request=httpx.Request("POST", url), json=corpo)
        args = ["comparar", "--perfil", "P01", "--exemplo", "login", "--tipo", "todos"]
        with patch.dict(os.environ, GROQ_MODEL="teste", GROQ_API_KEY="teste"), patch("httpx.post", side_effect=responder) as api:
            self.cli(*args)
            self.cli(*args)
            self.assertEqual(api.call_count, 8)
            self.assertEqual(len(list((self.pasta / "execucoes").glob("*.json"))), 16)
        arquivos = list((self.pasta / "comparacoes").glob("*.json"))
        self.assertEqual(len(arquivos), 2)
        arquivo = next(a for a in arquivos if ler(a)["resultados"][0]["origem"] == "api")
        itens = ler(arquivo)["resultados"]
        for a, b in zip(itens[::2], itens[1::2]):
            for campo in ("perfil", "ticket", "configuracao", "tipo"):
                self.assertEqual(a[campo], b[campo])
            self.assertNotEqual(a["hash_prompt"], b["hash_prompt"])
        with patch("builtins.input", side_effect=["4", "Justificativa de teste."] * 3 + [EOFError()]):
            with self.assertRaises(EOFError):
                self.cli("avaliar", str(arquivo))
        self.assertIsNotNone(ler(arquivo)["resultados"][0]["avaliacao"])
        with patch("builtins.input", side_effect=["3", "Justificativa de teste."] * 21):
            self.cli("avaliar", str(arquivo))
        self.assertTrue(all(i["avaliacao"] for i in ler(arquivo)["resultados"]))

    def test_cache_considera_perfil_modelo_versao_e_execucao_forcada(self):
        api = Mock(return_value=(EXEMPLOS["diagnostico"], "teste"))
        def executar(perfil=PERFIL, versao="v1", modelo="a", novo=False):
            return gerar(self.pasta, perfil, "Teste", "diagnostico", versao, modelo, novo, api)
        primeira = executar()
        self.assertEqual(executar()["execucao_original"], primeira["id"])
        executar(PERFIL.model_copy(update={"canal": "telefone"}))
        executar(versao="v2")
        executar(modelo="b")
        executar(novo=True)
        self.assertEqual(api.call_count, 5)

    def test_saida_invalida_nao_entra_no_cache(self):
        with self.assertRaisesRegex(ValueError, "contrato"):
            gerar(self.pasta, PERFIL, "Teste", "resolucao", "v1", "teste", chamar=lambda _: ({}, "teste"))
        self.assertFalse((self.pasta / "cache").exists())

    def test_ticket_vazio_nao_chama_provedor(self):
        api = Mock()
        with self.assertRaises(ValueError):
            gerar(self.pasta, PERFIL, "  ", "fluxo", "v2", "teste", chamar=api)
        api.assert_not_called()

