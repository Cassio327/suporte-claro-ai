import json
import re
import unittest
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from unittest.mock import patch
from urllib.parse import urlencode

from suporte.__main__ import RAIZ
from suporte.motor import ler
from suporte.painel import servidor


class TestePainel(unittest.TestCase):
    def setUp(self):
        pasta = TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        with patch("suporte.painel.configuracao_ambiente", return_value=("ollama", "modelo-teste")):
            self.http = servidor(RAIZ, self.pasta, 0)
        thread = Thread(target=self.http.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.http.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(self.http.shutdown)

    def pedir(self, metodo, caminho, campos=None, host=None):
        con = HTTPConnection("127.0.0.1", self.http.server_port, timeout=5)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if host:
            headers["Host"] = host
        try:
            con.request(metodo, caminho, body=urlencode(campos) if campos else None, headers=headers)
            r = con.getresponse()
            return r.status, r.read().decode()
        finally:
            con.close()

    def test_colecao_e_formulario_sem_api(self):
        with patch("suporte.motor.consultar") as api:
            for caso in ("diagnostico", "perguntas", "resolucao", "fluxo", "perfis", "audio", "upload", "canal", "estilo"):
                status, html = self.pedir("GET", "/?caso=" + caso)
                self.assertEqual(status, 200)
                self.assertEqual(html.count("<article>"), 2)
            self.assertEqual(self.pedir("GET", "/?caso=inexistente")[0], 400)
            self.assertEqual(self.pedir("GET", "/", host="example.com")[0], 403)
            self.assertEqual(self.pedir("POST", "/atender", {"chave":"invalida"})[0], 403)
            api.assert_not_called()

    def test_previa_geracao_cache_e_entrada_invalida(self):
        html = self.pedir("GET", "/atender")[1]
        chave = re.search(r'name="chave" value="([^"]+)"', html)[1]
        dados = dict(chave=chave, perfil="P01", tipo="resolucao", versao="v2", ticket="A < B", acao="prompt")
        exemplo = ler(RAIZ / "samples/exemplos_didaticos.json")["resolucao"]
        with patch("suporte.motor.consultar", return_value=(exemplo, "modelo-teste")) as api:
            status, html = self.pedir("POST", "/atender", dados)
            self.assertEqual(status, 200)
            self.assertIn("A &lt; B", html)
            self.assertFalse((self.pasta / "execucoes").exists())
            dados["acao"] = "gerar"
            for origem in ("api", "cache"):
                status, html = self.pedir("POST", "/atender", dados)
                self.assertEqual(status, 200)
                self.assertIn("Origem: " + origem, html)
            self.assertEqual(api.call_count, 1)
            versoes = [json.loads(f.read_text()) for f in (self.pasta / "execucoes").glob("*.json")]
            self.assertEqual({r["origem"] for r in versoes}, {"api", "cache"})
            dados.update(tipo="fluxo", versao="v3")
            self.assertEqual(self.pedir("POST", "/atender", dados)[0], 400)
            self.assertEqual(api.call_count, 1)
