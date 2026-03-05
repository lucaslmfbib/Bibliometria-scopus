# Bibliometria Scopus (do zero)

Aplicativo Streamlit para busca de artigos no Scopus e analise bibliometrica automatica.

## O que o app faz

- Busca artigos pela API da Elsevier/Scopus
- Pagina resultados automaticamente
- Mostra metricas bibliometricas:
  - total de documentos
  - citacoes totais e media
  - publicacoes por ano
  - top autores
  - top periodicos
  - termos mais frequentes nos titulos
- Permite download em CSV e Excel

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

## 4) Deploy no Streamlit Cloud

- Repositorio: este projeto
- Branch: a branch com estas alteracoes
- Main file path: `legacy_scopus/app.py`

## Consulta exemplo

```text
TITLE-ABS-KEY ("inteligencia artificial" AND bibliotecas)
```
