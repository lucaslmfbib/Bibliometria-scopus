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
