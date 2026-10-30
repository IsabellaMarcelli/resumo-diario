# 💻 Resumo Diário de Tecnologia

Automação em Python que, todo dia às 7h (horário de Brasília), lê as principais notícias de tecnologia do Brasil e do mundo, pega a cotação do dólar no Banco Central e gera um resumo em Markdown na pasta [`relatorios/`](relatorios/).

Ela substitui cerca de **30 minutos por dia** de leitura manual em vários sites, ou seja, cerca de 180 horas por ano.

<!-- HORAS:INICIO -->
⏱️ **1,0 h economizadas** em 2 dias de execução (última: 2026-10-30)
<!-- HORAS:FIM -->

## Como funciona

```
GitHub Actions (7h todo dia)
        │
        ▼
   resumo.py ──► feeds RSS (Tecnoblog, Olhar Digital, TechCrunch, The Verge, Ars Technica)
        │    └─► API do Banco Central (cotação do dólar)
        ▼
relatorios/AAAA-MM-DD.md  +  historico.json  +  placar no README
        │
        ▼
   commit automático no repositório
```

- **Sem propaganda:** ignora títulos com "oferta", "cupom", "menor preço" etc.
- **Sem dependências:** usa só a biblioteca padrão do Python.
- **Tolerante a falhas:** se uma fonte sair do ar, o resumo é gerado com as demais.
- **Configurável:** fontes, indicadores e minutos economizados ficam em [`fontes.json`](fontes.json).

## Fontes

| Fonte | Foco |
|---|---|
| Tecnoblog | Tecnologia no Brasil: apps, operadoras, lançamentos |
| Olhar Digital | Ciência e tecnologia em português |
| TechCrunch | Startups, IA e investimentos |
| The Verge | Produtos, gadgets e big techs |
| Ars Technica | Análises técnicas: segurança, hardware, ciência |

## Rodando no seu computador

```bash
git clone https://github.com/IsabellaMarcelli/resumo-diario.git
cd resumo-diario
python resumo.py          # gera o relatório de hoje
python -m unittest        # roda os testes (não precisa de internet)
```

Requer Python 3.10 ou superior.

## Publicando e agendando no GitHub

1. Crie um repositório no GitHub e envie os arquivos (`git push`).
2. O agendamento já está pronto em [`.github/workflows/resumo.yml`](.github/workflows/resumo.yml).
3. Para testar na hora: aba **Actions** → **Resumo diário** → **Run workflow**.

> O cron do GitHub usa UTC: `0 10 * * *` = 7h em Brasília. O GitHub pode atrasar alguns minutos em horários de pico.

## Personalizando

| Quer... | Edite |
|---|---|
| Adicionar/remover fontes | `fontes` em `fontes.json` |
| Mudar o tempo economizado | `minutos_economizados_por_execucao` |
| Mais ou menos notícias | `noticias_por_fonte` |
| Filtrar mais propagandas | `palavras_ignoradas` |
| Outros indicadores do BCB (ou `[]` para remover) | `indicadores_bcb` (códigos das séries no [SGS](https://www3.bcb.gov.br/sgspub/)) |
| Mudar o horário | `cron` no workflow |

## Ideias para evoluir

- Enviar o resumo por e-mail ou Telegram.
- Usar uma IA para resumir cada notícia em uma frase.
- Publicar os relatórios como site com GitHub Pages.

## Licença

MIT
