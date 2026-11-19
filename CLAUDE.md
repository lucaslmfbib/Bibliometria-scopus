# bibliometria-scopus

App Streamlit que busca artigos na API do Scopus (Elsevier) e gera análise bibliométrica automática.

## Estrutura
- `app.py` (raiz): ponto de entrada para o Streamlit Cloud; só importa e chama `legacy_scopus.app.main`.
- `legacy_scopus/app.py`: o app de verdade (busca, tabelas, gráficos).
- `legacy_scopus/summarize_map_reduce.py`: script avulso, fora do app, que resume textos longos com LangChain + OpenAI (map-reduce). Suas dependências (`langchain_*`) não estão no `requirements.txt`.
- `requirements.txt` (raiz) aponta para `legacy_scopus/requirements.txt`, onde as versões estão fixadas.

## Como rodar
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# .env na raiz com: api_key="SUA_CHAVE_ELSEVIER"   (modelo em legacy_scopus/.env.example)
streamlit run app.py
```
Consulta de exemplo: `TITLE-ABS-KEY ("inteligencia artificial" AND bibliotecas)`.

## Convenções
- A chave da Elsevier fica em `.env` (local) ou nos Secrets do Streamlit Cloud. Nunca commitar.
- Dependências novas vão em `legacy_scopus/requirements.txt`.
- Projetos relacionados: `bibliometria` (análise a partir de arquivos) e `semantic` (mesma análise com a API da Semantic Scholar).
- Não há testes automatizados.
