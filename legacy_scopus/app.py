#!/usr/bin/env python3
"""App de bibliometria Scopus feito do zero."""

from __future__ import annotations

import io
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

API_URL = "https://api.elsevier.com/content/search/scopus"
DEFAULT_QUERY = 'TITLE-ABS-KEY ("inteligencia artificial" AND bibliotecas)'
APP_VERSION = "2026-03-05-graficos"

STOPWORDS = {
    "a", "as", "o", "os", "de", "da", "das", "do", "dos", "e", "em", "no", "na", "nos", "nas",
    "um", "uma", "para", "por", "com", "the", "and", "for", "in", "on", "of", "to",
}


@dataclass
class SearchResult:
    total_results: int
    entries: list[dict[str, Any]]


def api_headers(api_key: str) -> dict[str, str]:
    return {"Accept": "application/json", "X-ELS-APIKey": api_key}


def get_page(api_key: str, query: str, count: int, start: int) -> dict[str, Any]:
    response = requests.get(
        API_URL,
        headers=api_headers(api_key),
        params={"query": query, "count": count, "start": start},
        timeout=40,
    )
    response.raise_for_status()
    return response.json()


def parse_total(payload: dict[str, Any]) -> int:
    raw = payload.get("search-results", {}).get("opensearch:totalResults", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


@st.cache_data(show_spinner=False)
def search_scopus(api_key: str, query: str, count: int, max_results: int) -> SearchResult:
    payload = get_page(api_key, query, count, 0)
    total = parse_total(payload)
    entries = payload.get("search-results", {}).get("entry", []) or []

    max_to_fetch = min(total, max_results)
    for start in range(count, max_to_fetch, count):
        page = get_page(api_key, query, count, start)
        entries.extend(page.get("search-results", {}).get("entry", []) or [])

    return SearchResult(total_results=total, entries=entries[:max_to_fetch])


def normalize_df(entries: list[dict[str, Any]]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame()

    raw = pd.json_normalize(entries)
    cols = [
        "dc:title",
        "dc:creator",
        "prism:coverDate",
        "prism:publicationName",
        "subtypeDescription",
        "citedby-count",
        "prism:doi",
        "prism:url",
    ]
    df = raw[[c for c in cols if c in raw.columns]].copy()
    df = df.rename(
        columns={
            "dc:title": "titulo",
            "dc:creator": "autor",
            "prism:coverDate": "data",
            "prism:publicationName": "periodico",
            "subtypeDescription": "tipo",
            "citedby-count": "citacoes",
            "prism:doi": "doi",
            "prism:url": "url_scopus",
        }
    )

    if "data" in df.columns:
        df["ano"] = pd.to_datetime(df["data"], errors="coerce").dt.year.astype("Int64")
    if "citacoes" in df.columns:
        df["citacoes"] = pd.to_numeric(df["citacoes"], errors="coerce").fillna(0).astype(int)
    return df


def top_terms(series: pd.Series, top_n: int = 20) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    for text in series.dropna().astype(str):
        for token in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]{3,}", text.lower()):
            if token not in STOPWORDS:
                counter[token] += 1
    return pd.DataFrame(counter.most_common(top_n), columns=["termo", "frequencia"])


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="bibliometria")
    return buffer.getvalue()


def show_rank_chart(
    title: str,
    data: pd.DataFrame,
    index_col: str,
    value_col: str,
) -> None:
    st.subheader(title)
    st.bar_chart(data.set_index(index_col)[value_col], use_container_width=True)
    st.dataframe(data, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Bibliometria Scopus", layout="wide")
    st.title("Bibliometria Scopus")
    st.caption(f"Versao do app: {APP_VERSION}")
    st.caption("Digite os termos, busque e receba análise bibliográfica automática.")
    st.markdown(
        "Por **Lucas Martins**  \n"
        "GitHub: [@lucaslmfbib](https://github.com/lucaslmfbib) | "
        "LinkedIn: [lucaslmf](https://www.linkedin.com/in/lucaslmf/) | "
        "Instagram: [@lucaslmf_](https://www.instagram.com/lucaslmf_/)"
    )

    load_dotenv()
    key_env = os.getenv("api_key") or os.getenv("SCOPUS_API_KEY") or ""

    with st.sidebar:
        st.header("Parâmetros")
        api_key = st.text_input("Chave API Elsevier", type="password", value=key_env)
        st.markdown("[Obter chave da API Scopus](https://dev.elsevier.com/)")
        st.caption("Nao compartilhe sua chave da API. Ela e pessoal e sensivel.")
        query = st.text_area("Consulta Scopus", value=DEFAULT_QUERY, height=110)
        count = st.slider("Resultados por página", min_value=10, max_value=200, value=25, step=5)
        max_results = st.slider("Máximo para analisar", min_value=25, max_value=2000, value=200, step=25)
        run = st.button("Buscar e analisar", type="primary", use_container_width=True)

    if not run:
        st.info("Preencha os campos e clique em 'Buscar e analisar'.")
        return

    if not api_key.strip():
        st.error("Informe sua chave da API Elsevier.")
        return
    if not query.strip():
        st.error("Informe uma consulta Scopus.")
        return

    try:
        with st.spinner("Consultando API do Scopus..."):
            result = search_scopus(api_key.strip(), query.strip(), count, max_results)
        df = normalize_df(result.entries)
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response else "?"
        st.error(f"Erro HTTP na API Scopus: {status}")
        return
    except requests.RequestException as exc:
        st.error(f"Erro de conexão: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        st.error(f"Erro inesperado: {exc}")
        return

    if df.empty:
        st.warning("Nenhum documento retornado para essa busca.")
        return

    st.success(f"Documentos coletados: {len(df)} (total no Scopus: {result.total_results})")

    docs = len(df)
    total_cit = int(df["citacoes"].sum()) if "citacoes" in df.columns else 0
    media_cit = float(df["citacoes"].mean()) if "citacoes" in df.columns else 0.0
    ano_ini = int(df["ano"].min()) if "ano" in df.columns and df["ano"].notna().any() else "-"
    ano_fim = int(df["ano"].max()) if "ano" in df.columns and df["ano"].notna().any() else "-"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documentos", docs)
    c2.metric("Citações totais", total_cit)
    c3.metric("Média citações", f"{media_cit:.2f}")
    c4.metric("Período", f"{ano_ini} - {ano_fim}")

    st.subheader("Base de dados da busca")
    st.dataframe(df, use_container_width=True)

    st.subheader("Gráficos e rankings")

    if "ano" in df.columns:
        por_ano = df.dropna(subset=["ano"]).groupby("ano").size().reset_index(name="publicacoes")
        if not por_ano.empty:
            por_ano = por_ano.sort_values("ano")
            st.subheader("Publicações por ano")
            st.bar_chart(por_ano.set_index("ano")["publicacoes"], use_container_width=True)
            st.dataframe(por_ano, use_container_width=True, hide_index=True)

    if "citacoes" in df.columns and not df["citacoes"].empty:
        bins = [0, 1, 5, 10, 25, 50, 100, float("inf")]
        labels = ["0", "1-4", "5-9", "10-24", "25-49", "50-99", "100+"]
        citacoes = df["citacoes"].clip(lower=0)
        faixas = pd.cut(citacoes, bins=bins, labels=labels, right=False, include_lowest=True)
        dist_citacoes = faixas.value_counts(sort=False).reset_index()
        dist_citacoes.columns = ["faixa_citacoes", "documentos"]
        if not dist_citacoes.empty:
            show_rank_chart(
                "Distribuição de citações",
                dist_citacoes,
                "faixa_citacoes",
                "documentos",
            )

    if "autor" in df.columns:
        top_autores = df["autor"].dropna().astype(str).value_counts().head(15)
        if not top_autores.empty:
            autores_df = top_autores.rename_axis("autor").reset_index(name="publicacoes")
            show_rank_chart("Top autores", autores_df, "autor", "publicacoes")

    if "periodico" in df.columns:
        top_periodicos = df["periodico"].dropna().astype(str).value_counts().head(15)
        if not top_periodicos.empty:
            periodicos_df = top_periodicos.rename_axis("periodico").reset_index(name="publicacoes")
            show_rank_chart("Top periódicos", periodicos_df, "periodico", "publicacoes")

    if "tipo" in df.columns:
        top_tipos = df["tipo"].dropna().astype(str).value_counts().head(10)
        if not top_tipos.empty:
            tipos_df = top_tipos.rename_axis("tipo").reset_index(name="publicacoes")
            show_rank_chart("Tipos de documento", tipos_df, "tipo", "publicacoes")

    if "titulo" in df.columns:
        termos = top_terms(df["titulo"], top_n=20)
        if not termos.empty:
            show_rank_chart(
                "Termos mais frequentes nos títulos",
                termos,
                "termo",
                "frequencia",
            )

    st.download_button(
        "Baixar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="bibliometria_scopus.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        "Baixar Excel",
        data=to_excel_bytes(df),
        file_name="bibliometria_scopus.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
