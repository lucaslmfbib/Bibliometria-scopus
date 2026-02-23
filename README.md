# Bibliometria Scopus (do zero)

Aplicativo Streamlit para busca de artigos no Scopus e análise bibliométrica automática.

## O que o app faz

- Busca artigos pela API da Elsevier/Scopus
- Pagina resultados automaticamente
- Mostra métricas bibliométricas:
  - total de documentos
  - citações totais e média
  - publicações por ano
  - top autores
  - top periódicos
  - termos mais frequentes nos títulos
- Permite download em CSV e Excel

## 1) Criar ambiente e instalar dependências

```bash
cd "/Users/lucasmartins/Documents/New project"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2) Configurar chave da API

Crie um arquivo `.env` na raiz do projeto:

```env
api_key="SUA_CHAVE_ELSEVIER"
```

## 3) Rodar o app

```bash
python -m streamlit run app.py
```

## Consulta exemplo

```text
TITLE-ABS-KEY ("inteligencia artificial" AND bibliotecas)
```
