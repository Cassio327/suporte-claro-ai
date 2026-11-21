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
from suporte.motor import consultar, gerar, ler, resumo, salvar
from suporte.prompts import mensagens
from suporte.comparacao import pares, relatorio

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
        def responder(url, **kwargs):
            corpo = {"model": "teste", "choices": [{"message": {"content": json.dumps(respostas.pop(0))}}]}
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
        self.assertEqual(sum(i["avaliacao"] is not None for i in ler(arquivo)["resultados"]), 1)
        with patch("builtins.input", side_effect=["3", "Justificativa de teste."] * 21):
            self.cli("avaliar", str(arquivo))
        self.assertTrue(all(i["avaliacao"] for i in ler(arquivo)["resultados"]))
        self.cli("relatorio", str(arquivo))
        html = arquivo.with_suffix(".html").read_text()
        self.assertEqual(html.count("<article>"), 8)
        self.assertEqual(html.count("<table>"), 4)
        with self.assertRaises(FileExistsError):
            self.cli("relatorio", str(arquivo))

    def par(self):
        registros = [gerar(self.pasta, PERFIL, "Mensagem <b>texto</b>", "perguntas", v,
                           "teste", chamar=lambda _: (EXEMPLOS["perguntas"], "teste"))
                     for v in ("v1", "v2")]
        return {"resultados": registros}

    def test_rejeita_pares_incomparaveis(self):
        for campo, valor in (("ticket", "outro"), ("versao", "v1"), ("modelo_retornado", "outro")):
            with self.subTest(campo=campo):
                doc = self.par()
                doc["resultados"][1][campo] = valor
                with self.assertRaises(ValueError):
                    pares(doc)

    def test_avaliacao_publicada_preserva_as_geracoes_e_os_prompts(self):
        amostras = RAIZ / "samples"
        originais = pares(ler(amostras / "login-ollama.json"))
        avaliadas = pares(ler(amostras / "login-ollama-avaliado.json"))
        self.assertEqual(set(avaliadas), set(TIPOS))
        for tipo, grupo in avaliadas.items():
            for versao, registro in grupo.items():
                with self.subTest(tipo=tipo, versao=versao):
                    avaliado = registro.copy()
                    self.assertIsNotNone(avaliado.pop("avaliado_em"))
                    self.assertIsNotNone(avaliado["avaliacao"])
                    avaliado["avaliacao"] = None
                    self.assertEqual(avaliado, originais[tipo][versao])
                    perfil = Perfil.model_validate(registro["perfil"])
                    prompt = mensagens(perfil, registro["ticket"], tipo, versao)
                    self.assertEqual(resumo(prompt[0]["content"]), registro["hash_prompt"])

    def test_repeticoes_de_permissao_usam_o_mesmo_cenario_e_geracoes_distintas(self):
        rodadas = ler(RAIZ / "samples/permissao-v2-v3.json")["rodadas"]
        self.assertEqual(len(rodadas), 2)
        registros = [pares(rodada)["resolucao"][versao] for rodada in rodadas for versao in ("v2", "v3")]
        self.assertEqual(len({item["id"] for item in registros}), 4)
        for item in registros:
            self.assertEqual(item["origem"], "api")
            self.assertIsNone(item["execucao_original"])
            for campo in ("perfil", "ticket", "tipo", "configuracao", "modelo_retornado", "provedor"):
                self.assertEqual(item[campo], registros[0][campo])
        for a, b in zip(registros[:2], registros[2:], strict=True):
            self.assertEqual(a["hash_prompt"], b["hash_prompt"])
            self.assertEqual(a["chave_cache"], b["chave_cache"])

    def test_amostra_de_comunicacao_isola_canal_e_estilo(self):
        resultados = ler(RAIZ / "samples/upload-comunicacao-v2.json")["resultados"]
        por_id = {item["perfil"]["id"]: item for item in resultados}
        self.assertEqual(set(por_id), {"P03", "P04", "P05"})
        for perfil, atributo in (("P03", "canal"), ("P04", "estilo")):
            a, b = por_id[perfil], por_id["P05"]
            with self.subTest(atributo=atributo):
                for campo in ("ticket", "tipo", "versao", "provedor", "configuracao", "modelo_retornado"):
                    self.assertEqual(a[campo], b[campo])
                diferencas = {k for k in a["perfil"] if a["perfil"][k] != b["perfil"][k]}
                self.assertEqual(diferencas, {"id", atributo})
        for item in resultados:
            TIPOS["resolucao"].model_validate(item["saida"])
            self.assertEqual(item["origem"], "api")

    def test_historico_invalido_da_erro_legivel_e_preserva_o_arquivo(self):
        for campo, valor in (("configuracao", None), ("configuracao", {}), ("tipo", []), ("id", [])):
            with self.subTest(campo=campo):
                doc = self.par()
                doc["resultados"][0][campo] = valor
                arquivo = self.pasta / "historico.json"
                salvar(arquivo, doc)
                original = arquivo.read_bytes()
                for comando in ("avaliar", "relatorio"):
                    with self.assertRaisesRegex(ValueError, "registro|Registro"):
                        self.cli(comando, str(arquivo))
                self.assertEqual(arquivo.read_bytes(), original)
                self.assertFalse(arquivo.with_suffix(".html").exists())

    def test_avaliar_oculta_versao_ate_concluir_e_escapa_ticket(self):
        caminho = self.pasta / "par.json"
        salvar(caminho, self.par())
        with self.assertRaisesRegex(ValueError, "rubrica"):
            relatorio(ler(caminho))
        with patch("sys.argv", ["suporte", "avaliar", str(caminho)]), redirect_stdout(io.StringIO()) as out:
            with patch("builtins.input", side_effect=["4", "Teste de leitura."] * 6):
                principal()
        for versao in ("v1", "v2"):
            self.assertNotIn(versao, out.getvalue())
        self.assertIn("resposta A", out.getvalue())
        self.assertIn("resposta B", out.getvalue())
        self.assertIn("&lt;b&gt;texto&lt;/b&gt;", relatorio(ler(caminho)))

    def test_troca_acidental_dos_arquivos_de_cache(self):
        doc = self.par()
        a, b = doc["resultados"]
        salvar(self.pasta / "cache" / (a["chave_cache"] + ".json"), b)
        with self.assertRaisesRegex(ValueError, "Cache inválido"):
            gerar(self.pasta, PERFIL, a["ticket"], a["tipo"], "v1", "teste")

    def test_api_truncada_tem_erro_especifico(self):
        resposta = httpx.Response(200, request=httpx.Request("POST", "https://example.test"),
                                  json={"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]})
        with patch.dict(os.environ, GROQ_API_KEY="teste"), patch("httpx.post", return_value=resposta):
            with self.assertRaisesRegex(ValueError, "truncada"):
                consultar({})

    def test_api_local_quatro_pares_com_esquema_sem_credencial(self):
        def responder(url, **kwargs):
            self.assertEqual(url, "http://127.0.0.1:11434/v1/chat/completions")
            self.assertEqual(kwargs["headers"], {})
            formato = kwargs["json"]["response_format"]["json_schema"]
            tipo = formato["name"]
            self.assertEqual(formato["schema"], TIPOS[tipo].model_json_schema())
            corpo = {"model": "qwen2.5:3b", "choices": [{"message": {"content": json.dumps(EXEMPLOS[tipo])}}]}
            return httpx.Response(200, request=httpx.Request("POST", url), json=corpo)
        with patch.dict(os.environ, SUPORTE_PROVEDOR="ollama", GROQ_API_KEY=""), patch("httpx.post", side_effect=responder) as api:
            self.cli("comparar", "--perfil", "P01", "--exemplo", "login", "--tipo", "todos")
            self.assertEqual(api.call_count, 8)
        documento = ler(next((self.pasta / "comparacoes").glob("*.json")))
        self.assertEqual(len(pares(documento)), 4)
        self.assertTrue(all(i["provedor"] == "ollama" for i in documento["resultados"]))

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

    def test_versoes_experimentais_na_cli_e_no_relatorio(self):
        with patch.dict(os.environ, GROQ_MODEL="teste"), patch("suporte.motor.consultar",
                return_value=(EXEMPLOS["resolucao"], "teste")) as api:
            with self.assertRaisesRegex(ValueError, "resolucao"):
                self.cli("comparar", "--perfil", "P01", "--exemplo", "upload", "--tipo", "todos",
                         "--versoes", "v2", "v3")
            api.assert_not_called()
            self.cli("comparar", "--perfil", "P01", "--exemplo", "upload", "--tipo", "resolucao",
                     "--versoes", "v2", "v3")
            self.assertEqual(api.call_count, 2)
        caminho = next((self.pasta / "comparacoes").glob("*.json"))
        doc = ler(caminho)
        self.assertEqual(doc["versoes"], ["v2", "v3"])
        self.assertNotEqual(*[r["hash_prompt"] for r in doc["resultados"]])
        with patch("builtins.input", side_effect=["3", "Teste de leitura."] * 6):
            self.cli("avaliar", str(caminho))
        pagina = relatorio(ler(caminho))
        self.assertIn("v3 − v2", pagina)
        self.assertIn("<h3>Prompt v3</h3>", pagina)
        self.assertNotIn("<h3>Prompt v1</h3>", pagina)

