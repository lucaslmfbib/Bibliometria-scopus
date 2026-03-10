# Bibliometria Scopus

Aplicativo Streamlit para busca de artigos no Scopus e analise bibliometrica automatica.

## 1) Criar ambiente e instalar dependencias

```bash
cd "/Users/lucasmartins/Documents/New project"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r legacy_scopus/requirements.txt
```

## 2) Configurar chave da API

Crie um arquivo `.env` na raiz do projeto:

```env
api_key="SUA_CHAVE_ELSEVIER"
```

## 3) Rodar o app

```bash
python -m streamlit run legacy_scopus/app.py
```

## Consulta exemplo

```text
TITLE-ABS-KEY ("inteligencia artificial" AND bibliotecas)
```

## Análises bibliométricas (novo pacote)

Criei um pacote auxiliar `bibliometria/` com funções para carregar dados (CSV/Excel), calcular métricas básicas e gerar visualizações. Arquivos adicionados nesta branch:

- `bibliometria/__init__.py` — exporta as funções principais
- `bibliometria/io.py` — carregador de CSV/Excel e normalização mínima de colunas
- `bibliometria/analysis.py` — funções de análise (top authors, journals, years, keywords, citações)
- `bibliometria/viz.py` — funções simples de visualização (matplotlib)
- `examples/demo.py` — script exemplo de linha de comando
- `requirements_app.txt` — dependências recomendadas para rodar o app

Uso rápido:

```bash
python -m pip install -r requirements_app.txt
python examples/demo.py path/para/seu_arquivo.csv
```

Observações:
- O carregador tenta mapear colunas comuns (Authors, Title, Year, Source title, Author Keywords, Cited by).
- As dependências do projeto principal permanecem — este arquivo `requirements_app.txt` é específico para a parte de análise/visualização.

