# Bibliometria

Ferramenta para executar análises bibliométricas a partir de arquivos `CSV` ou `Excel` (`.xls`/`.xlsx`).

## Entrada esperada

O sistema tenta mapear automaticamente colunas comuns (em inglês/português), como:

- `Authors` / `Autores`
- `Title` / `Título`
- `Year` / `Ano`
- `Journal` / `Source title` / `Periódico`
- `Keywords` / `Author Keywords` / `Palavras-chave`
- `Cited by` / `Citado por`

## Como executar

No diretório pai do pacote:

```bash
python3 -m bibliometria.cli --input "/caminho/arquivo.xlsx" --output-dir "./analysis_output"
```

Ou para CSV:

```bash
python3 -m bibliometria.cli --input "/caminho/dados.csv" --encoding "utf-8"
```

## Saídas geradas

Na pasta `analysis_output` (ou outra definida em `--output-dir`):

- `summary.json`
- `top_authors.csv`
- `author_document_counts.csv` (autores e número de trabalhos)
- `top_journals.csv`
- `top_keywords.csv`
- `title_terms.csv` (termos mais frequentes no título)
- `abstract_terms.csv` (termos mais frequentes no resumo)
- `most_cited_documents.csv`
- `research_overview.csv` (quadro geral estilo dashboard)
- `research_records.csv` (tabela com informações dos documentos)
- `yearly_counts.csv`
- `yearly_cumulative.csv`
- `yearly_growth_pct.csv`
- `author_year_counts.csv`
- `author_productivity_distribution.csv`
- `coauthorship_edges.csv`
- `citations_by_year.csv` (quando houver `Year` + `Cited by`)
- `citation_stats.csv` (quando houver citações)
- Gráficos `.png`, incluindo:
  - rankings de autores/periódicos/palavras-chave
  - termos mais frequentes em título e resumo
  - documentos mais citados
  - linha, barras, acumulado e crescimento por ano
  - tendência dos autores por ano (linhas)
  - heatmap autor x ano
  - distribuição de produtividade dos autores
  - grafo de coautoria

## Opções úteis

- `--top-n 30`: muda o tamanho dos rankings
- `--sheet-name 1` ou `--sheet-name MinhaAba`: escolhe aba no Excel
- `--no-plots`: não gera os gráficos em PNG
- `--network-max-authors 40`: tamanho máximo do grafo de coautoria
- `--network-min-weight 2`: só mostra conexões com pelo menos 2 coautorias

## Teste direto no Streamlit

No diretório do projeto:

```bash
streamlit run streamlit_app.py
```

Se necessário, instale antes:

```bash
pip install streamlit
```

## Publicar no GitHub e Streamlit Cloud

1. Suba este projeto para um repositório no GitHub.
2. Acesse [https://share.streamlit.io](https://share.streamlit.io) e conecte sua conta GitHub.
3. Clique em `New app`.
4. Selecione:
   - Repositório: `lucaslmfbib/Bibliometria-scopus`
   - Branch: a branch publicada (ex.: `main` ou `codex/streamlit-graficos`)
   - Main file path: `streamlit_app.py`
5. Clique em `Deploy`.

O Streamlit Cloud instalará automaticamente as dependências de `requirements.txt`.
