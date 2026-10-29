"""Testes simples, rodam sem internet:  python -m unittest"""

import unittest
from datetime import datetime, timedelta, timezone

import resumo

RSS_EXEMPLO = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Exemplo</title>
  <item><title>Senado aprova projeto &lt;b&gt;X&lt;/b&gt;</title>
        <link>https://exemplo.com/1</link>
        <pubDate>Thu, 29 Oct 2026 09:00:00 -0300</pubDate></item>
  <item><title>Noticia antiga</title>
        <link>https://exemplo.com/2</link>
        <pubDate>Mon, 26 Oct 2026 09:00:00 -0300</pubDate></item>
</channel></rss>"""

AGORA = datetime(2026, 10, 29, 12, 0, tzinfo=timezone(timedelta(hours=-3)))


class TestResumo(unittest.TestCase):
    def test_ler_feed_limpa_html(self):
        noticias = resumo.ler_feed(RSS_EXEMPLO)
        self.assertEqual(len(noticias), 2)
        self.assertEqual(noticias[0]["titulo"], "Senado aprova projeto X")

    def test_filtra_ultimas_24h(self):
        recentes = resumo.filtrar_recentes(resumo.ler_feed(RSS_EXEMPLO), AGORA)
        self.assertEqual([n["link"] for n in recentes], ["https://exemplo.com/1"])

    def test_ignora_propaganda(self):
        palavras = ["oferta", "menor preço"]
        self.assertTrue(resumo.eh_propaganda("Celular X pelo MENOR PREÇO", palavras))
        self.assertFalse(resumo.eh_propaganda("Apple lança novo chip", palavras))

    def test_formatar_horas(self):
        self.assertEqual(resumo.formatar_horas(12.5), "12,5 h")

    def test_relatorio_tem_placar(self):
        md = resumo.montar_relatorio(
            "2026-10-29",
            {"Tech Brasil": [{"titulo": "T", "link": "L", "fonte": "F"}]},
            [],
            {"hoje": 30, "horas": 1.0, "dias": 2},
        )
        self.assertIn("## Tech Brasil", md)
        self.assertIn("Acumulado: 1,0 h em 2 dias", md)


if __name__ == "__main__":
    unittest.main()
