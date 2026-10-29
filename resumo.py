"""
Resumo diário de notícias de tecnologia.

Lê feeds RSS de sites de tecnologia e a cotação do dólar no Banco Central,
gera um relatório em Markdown e contabiliza as horas economizadas.

Uso:
    python resumo.py
Só usa a biblioteca padrão do Python, então não precisa instalar nada.
"""

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

PASTA = Path(__file__).parent
CONFIG = PASTA / "fontes.json"
PASTA_RELATORIOS = PASTA / "relatorios"
HISTORICO = PASTA / "historico.json"
README = PASTA / "README.md"

FUSO_BRASILIA = timezone(timedelta(hours=-3))
USER_AGENT = "Mozilla/5.0 (resumo-diario; +https://github.com)"


# ---------------------------------------------------------------- download
def baixar(url: str, timeout: int = 20) -> bytes:
    """Baixa o conteúdo de uma URL."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ---------------------------------------------------------------- notícias
def limpar_texto(texto: str | None) -> str:
    """Remove tags HTML e espaços extras."""
    if not texto:
        return ""
    texto = re.sub(r"<[^>]+>", " ", unescape(texto))
    return re.sub(r"\s+", " ", texto).strip()


def ler_data(texto: str | None) -> datetime | None:
    """Converte datas de RSS ('Thu, 29 Oct 2026 10:00:00 -0300') ou ISO."""
    if not texto:
        return None
    try:
        return parsedate_to_datetime(texto)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        return None


def ler_feed(xml_bytes: bytes) -> list[dict]:
    """Extrai título, link e data de cada item de um feed RSS (ou Atom)."""
    raiz = ET.fromstring(xml_bytes)
    noticias = []

    # RSS: <item>  |  Atom: <entry>
    itens = raiz.iter("item")
    atom = "{http://www.w3.org/2005/Atom}"
    if raiz.tag == f"{atom}feed":
        itens = raiz.iter(f"{atom}entry")

    for item in itens:
        if item.tag == "item":
            titulo = item.findtext("title")
            link = item.findtext("link")
            data = item.findtext("pubDate")
        else:
            titulo = item.findtext(f"{atom}title")
            link_el = item.find(f"{atom}link")
            link = link_el.get("href") if link_el is not None else None
            data = item.findtext(f"{atom}updated")

        if titulo and link:
            noticias.append({
                "titulo": limpar_texto(titulo),
                "link": link.strip(),
                "data": ler_data(data),
            })
    return noticias


def filtrar_recentes(noticias: list[dict], agora: datetime, horas: int = 24) -> list[dict]:
    """Mantém só notícias das últimas N horas (as sem data entram também)."""
    limite = agora - timedelta(hours=horas)
    return [n for n in noticias if n["data"] is None or n["data"] >= limite]


def eh_propaganda(titulo: str, palavras_ignoradas: list[str]) -> bool:
    """True se o título tiver alguma palavra de oferta/promoção."""
    titulo = titulo.lower()
    return any(p.lower() in titulo for p in palavras_ignoradas)


def coletar_noticias(fontes: list[dict], agora: datetime, por_fonte: int,
                     palavras_ignoradas: list[str] = ()) -> dict[str, list[dict]]:
    """Busca todas as fontes e agrupa as notícias por categoria."""
    por_categoria: dict[str, list[dict]] = {}
    vistos = set()

    for fonte in fontes:
        try:
            url = fonte["url"].format(ano=agora.year)  # {ano} vira o ano atual
            noticias = ler_feed(baixar(url))
        except Exception as erro:  # uma fonte fora do ar não derruba o resumo
            print(f"[aviso] {fonte['nome']}: {erro}")
            continue

        recentes = [n for n in filtrar_recentes(noticias, agora)
                    if not eh_propaganda(n["titulo"], palavras_ignoradas)][:por_fonte]
        for n in recentes:
            chave = n["titulo"].lower()
            if chave in vistos:  # evita repetir a mesma manchete
                continue
            vistos.add(chave)
            n["fonte"] = fonte["nome"]
            por_categoria.setdefault(fonte["categoria"], []).append(n)
        print(f"[ok] {fonte['nome']}: {len(recentes)} notícias")

    return por_categoria


# ---------------------------------------------------------------- indicadores
def buscar_indicador(serie: int) -> dict | None:
    """Último valor de uma série do SGS (Banco Central)."""
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados/ultimos/1?formato=json"
    try:
        dados = json.loads(baixar(url))
        return dados[-1] if dados else None
    except Exception as erro:
        print(f"[aviso] série {serie} do BCB: {erro}")
        return None


def coletar_indicadores(config: list[dict]) -> list[str]:
    linhas = []
    for ind in config:
        dado = buscar_indicador(ind["serie"])
        if dado:
            valor = ind["formato"].format(valor=dado["valor"].replace(".", ","))
            linhas.append(f"| {ind['nome']} | {valor} | {dado['data']} |")
    return linhas


# ---------------------------------------------------------------- horas economizadas
def registrar_execucao(dia: str, minutos: int) -> dict:
    """Salva o dia no histórico (uma vez por dia) e devolve os totais."""
    historico = json.loads(HISTORICO.read_text()) if HISTORICO.exists() else {}
    historico[dia] = minutos
    HISTORICO.write_text(json.dumps(historico, indent=2, sort_keys=True))

    total_min = sum(historico.values())
    return {"dias": len(historico), "horas": total_min / 60, "hoje": minutos}


def formatar_horas(horas: float) -> str:
    return f"{horas:.1f}".replace(".", ",") + " h"


def plural_dias(n: int) -> str:
    return f"{n} dia" if n == 1 else f"{n} dias"


def atualizar_readme(totais: dict, dia: str) -> None:
    """Substitui o trecho entre os marcadores do README pelo placar atual."""
    if not README.exists():
        return
    placar = (
        f"⏱️ **{formatar_horas(totais['horas'])} economizadas** "
        f"em {plural_dias(totais['dias'])} de execução (última: {dia})"
    )
    texto = README.read_text(encoding="utf-8")
    texto = re.sub(
        r"(<!-- HORAS:INICIO -->).*?(<!-- HORAS:FIM -->)",
        rf"\1\n{placar}\n\2",
        texto,
        flags=re.S,
    )
    README.write_text(texto, encoding="utf-8")


# ---------------------------------------------------------------- relatório
ORDEM_CATEGORIAS = ["Tech Brasil", "Tech Mundo"]


def montar_relatorio(dia: str, noticias: dict, indicadores: list[str], totais: dict) -> str:
    md = [f"# Resumo diário de tecnologia ({dia})", ""]

    if indicadores:
        md += ["## Indicadores (Banco Central)", "",
               "| Indicador | Valor | Data |", "|---|---|---|", *indicadores, ""]

    categorias = sorted(noticias, key=lambda c: ORDEM_CATEGORIAS.index(c)
                        if c in ORDEM_CATEGORIAS else 99)
    for cat in categorias:
        md += [f"## {cat}", ""]
        for n in noticias[cat]:
            md.append(f"- [{n['titulo']}]({n['link']}) · *{n['fonte']}*")
        md.append("")

    if not noticias:
        md += ["_Nenhuma notícia encontrada hoje (as fontes podem estar fora do ar)._", ""]

    md += [
        "---",
        f"⏱️ Hoje: {totais['hoje']} min economizados · "
        f"Acumulado: {formatar_horas(totais['horas'])} em {plural_dias(totais['dias'])}",
        "",
    ]
    return "\n".join(md)


# ---------------------------------------------------------------- principal
def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    agora = datetime.now(FUSO_BRASILIA)
    dia = agora.strftime("%Y-%m-%d")

    noticias = coletar_noticias(config["fontes"], agora, config["noticias_por_fonte"],
                                config.get("palavras_ignoradas", []))
    indicadores = coletar_indicadores(config["indicadores_bcb"])
    totais = registrar_execucao(dia, config["minutos_economizados_por_execucao"])

    PASTA_RELATORIOS.mkdir(exist_ok=True)
    arquivo = PASTA_RELATORIOS / f"{dia}.md"
    arquivo.write_text(montar_relatorio(dia, noticias, indicadores, totais), encoding="utf-8")
    atualizar_readme(totais, dia)

    print(f"\nRelatório salvo em {arquivo}")
    print(f"Horas economizadas até agora: {formatar_horas(totais['horas'])}")


if __name__ == "__main__":
    main()
