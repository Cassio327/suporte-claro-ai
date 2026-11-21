"""Verificação de interface no Chrome; executada no GitHub Actions."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import expect, sync_playwright

from suporte.__main__ import RAIZ
from suporte.painel import servidor


def verificar():
    with TemporaryDirectory() as tmp, servidor(RAIZ, Path(tmp), 0) as http, sync_playwright() as pw:
        thread = Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            browser = pw.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": 1180, "height": 900})
            origem = f"http://127.0.0.1:{http.server_port}"
            page.goto(origem)
            expect(page.get_by_role("heading", name="Comparar respostas")).to_be_visible()
            expect(page.get_by_role("article")).to_have_count(2)
            page.get_by_text("Notas e justificativas", exact=True).first.click()
            expect(page.locator("details[open]")).to_have_count(1)
            page.get_by_label("Experimento").select_option("perfis")
            page.get_by_role("button", name="Ver comparação").click()
            expect(page.get_by_role("article").first).to_contain_text("leigo")
            expect(page.get_by_role("article").last).to_contain_text("avançado")
            page.get_by_role("link", name="Novo atendimento").click()
            page.get_by_label("Ticket do cliente").fill("Não consigo ouvir a gravação.")
            page.get_by_role("button", name="Ver prévia do prompt").click()
            expect(page.get_by_role("heading", name="Prévia do prompt")).to_be_visible()
            expect(page.locator(".resultado")).to_contain_text("Não consigo ouvir a gravação.")
            page.get_by_role("button", name="Gerar resposta").click()
            expect(page.get_by_role("alert")).to_be_visible()
            page.set_viewport_size({"width":375, "height":812})
            for caminho in ("/", "/atender", "/?caso=upload"):
                page.goto(origem + caminho)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            browser.close()
        finally:
            http.shutdown()
            thread.join()


if __name__ == "__main__":
    verificar()
