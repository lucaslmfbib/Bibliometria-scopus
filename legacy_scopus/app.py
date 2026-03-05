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
APP_VERSION = "2026-03-05-resumo-coluna"

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


def show_rank_table(title: str, data: pd.DataFrame) -> None:
    st.subheader(title)
    st.dataframe(data, use_container_width=True, hide_index=True)


def _clean_value(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, float) and pd.isna(value):
        return fallback
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return fallback
    return text


def build_row_work_summary(row: pd.Series) -> str:
    titulo = _clean_value(row.get("titulo"), "Sem titulo")
    autor = _clean_value(row.get("autor"), "Autor nao informado")
    periodico = _clean_value(row.get("periodico"), "Periodico nao informado")
    tipo = _clean_value(row.get("tipo"), "Tipo nao informado")

    ano = row.get("ano")
    if ano is None or (isinstance(ano, float) and pd.isna(ano)):
        ano_text = "-"
    else:
        try:
            ano_text = str(int(ano))
        except (TypeError, ValueError):
            ano_text = _clean_value(ano, "-")

    citacoes_raw = row.get("citacoes", 0)
    if citacoes_raw is None or (isinstance(citacoes_raw, float) and pd.isna(citacoes_raw)):
        citacoes = 0
    else:
        try:
            citacoes = int(citacoes_raw)
        except (TypeError, ValueError):
            citacoes = 0

    return (
        f"{titulo}. Autor principal: {autor}. Ano: {ano_text}. "
        f"Periodico: {periodico}. Tipo: {tipo}. Citacoes: {citacoes}."
    )


def add_works_summary_column(df: pd.DataFrame) -> pd.DataFrame:
    df_display = df.copy()
    df_display["resumo_trabalho"] = df_display.apply(build_row_work_summary, axis=1)
    return df_display


def build_search_summary(
    query: str,
    docs: int,
    total_scopus: int,
    total_cit: int,
    media_cit: float,
    ano_ini: int | str,
    ano_fim: int | str,
    por_ano: pd.DataFrame,
    dist_citacoes: pd.DataFrame,
    autores_df: pd.DataFrame,
    periodicos_df: pd.DataFrame,
    tipos_df: pd.DataFrame,
    termos_df: pd.DataFrame,
) -> str:
    lines = [
        "RESUMO DA PESQUISA",
        f"- Consulta: {query}",
        f"- Amostra analisada: {docs} documentos (total no Scopus: {total_scopus})",
        f"- Periodo da amostra: {ano_ini} - {ano_fim}",
        f"- Citacoes totais: {total_cit}",
        f"- Media de citacoes por documento: {media_cit:.2f}",
    ]

    if not por_ano.empty:
        top_ano = por_ano.sort_values("publicacoes", ascending=False).iloc[0]
        lines.append(
            f"- Ano com mais publicacoes: {int(top_ano['ano'])} ({int(top_ano['publicacoes'])} documentos)"
        )
    if not dist_citacoes.empty:
        top_faixa = dist_citacoes.sort_values("documentos", ascending=False).iloc[0]
        lines.append(
            f"- Faixa de citacoes mais comum: {top_faixa['faixa_citacoes']} "
            f"({int(top_faixa['documentos'])} documentos)"
        )
    if not autores_df.empty:
        top_autor = autores_df.iloc[0]
        lines.append(
            f"- Autor mais frequente: {top_autor['autor']} "
            f"({int(top_autor['publicacoes'])} documentos)"
        )
    if not periodicos_df.empty:
        top_periodico = periodicos_df.iloc[0]
        lines.append(
            f"- Periodico com mais publicacoes: {top_periodico['periodico']} "
            f"({int(top_periodico['publicacoes'])} documentos)"
        )
    if not tipos_df.empty:
        top_tipo = tipos_df.iloc[0]
        lines.append(
            f"- Tipo de documento predominante: {top_tipo['tipo']} "
            f"({int(top_tipo['publicacoes'])} documentos)"
        )
    if not termos_df.empty:
        termos_top3 = ", ".join(termos_df.head(3)["termo"].astype(str).tolist())
        lines.append(f"- Termos de maior destaque nos titulos: {termos_top3}")

    return "\n".join(lines)


def build_works_summary(df: pd.DataFrame, top_n: int = 20) -> tuple[str, pd.DataFrame]:
    required_cols = [
        "titulo",
        "resumo_trabalho",
        "autor",
        "ano",
        "periodico",
        "tipo",
        "citacoes",
        "doi",
        "url_scopus",
    ]
    available_cols = [col for col in required_cols if col in df.columns]
    if not available_cols:
        return "Nao foi possivel montar o resumo dos trabalhos com os campos disponiveis.", pd.DataFrame()

    works_df = df[available_cols].copy()
    if "citacoes" in works_df.columns:
        works_df = works_df.sort_values(["citacoes"], ascending=False, na_position="last")
    works_df = works_df.head(top_n).reset_index(drop=True)

    lines = ["RESUMO DOS TRABALHOS (TOP POR CITACOES)"]
    for idx, row in works_df.iterrows():
        titulo = str(row.get("titulo", "Sem titulo")).strip() or "Sem titulo"
        resumo = str(row.get("resumo_trabalho", "")).strip()
        autor = str(row.get("autor", "Autor nao informado")).strip() or "Autor nao informado"
        ano = row.get("ano", "-")
        periodico = str(row.get("periodico", "Periodico nao informado")).strip() or "Periodico nao informado"
        tipo = str(row.get("tipo", "Tipo nao informado")).strip() or "Tipo nao informado"
        citacoes = int(row.get("citacoes", 0)) if pd.notna(row.get("citacoes", 0)) else 0
        doi = str(row.get("doi", "")).strip()
        url_scopus = str(row.get("url_scopus", "")).strip()

        lines.append(f"{idx + 1}. {titulo}")
        lines.append(
            f"   Autor: {autor} | Ano: {ano} | Citacoes: {citacoes} | Tipo: {tipo}"
        )
        lines.append(f"   Periodico: {periodico}")
        if resumo and resumo.lower() != "nan":
            lines.append(f"   Resumo: {resumo}")
        if doi and doi.lower() != "nan":
            lines.append(f"   DOI: {doi}")
        if url_scopus and url_scopus.lower() != "nan":
            lines.append(f"   Link Scopus: {url_scopus}")
        lines.append("")

    display_df = works_df.copy()
    display_df.insert(0, "rank", range(1, len(display_df) + 1))
    return "\n".join(lines).strip(), display_df


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
        df_display = add_works_summary_column(df)
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

    resumo_df = pd.DataFrame(
        [
            {"indicador": "Documentos coletados", "valor": docs},
            {"indicador": "Total no Scopus", "valor": result.total_results},
            {"indicador": "Citações totais", "valor": total_cit},
            {"indicador": "Média de citações", "valor": round(media_cit, 2)},
            {"indicador": "Período da amostra", "valor": f"{ano_ini} - {ano_fim}"},
        ]
    )

    por_ano = pd.DataFrame()
    if "ano" in df.columns:
        por_ano = df.dropna(subset=["ano"]).groupby("ano").size().reset_index(name="publicacoes")
        if not por_ano.empty:
            por_ano = por_ano.sort_values("ano")

    dist_citacoes = pd.DataFrame()
    if "citacoes" in df.columns and not df["citacoes"].empty:
        bins = [0, 1, 5, 10, 25, 50, 100, float("inf")]
        labels = ["0", "1-4", "5-9", "10-24", "25-49", "50-99", "100+"]
        citacoes = df["citacoes"].clip(lower=0)
        faixas = pd.cut(citacoes, bins=bins, labels=labels, right=False, include_lowest=True)
        dist_citacoes = faixas.value_counts(sort=False).reset_index()
        dist_citacoes.columns = ["faixa_citacoes", "documentos"]

    autores_df = pd.DataFrame()
    if "autor" in df.columns:
        top_autores = df["autor"].dropna().astype(str).value_counts().head(15)
        if not top_autores.empty:
            autores_df = top_autores.rename_axis("autor").reset_index(name="publicacoes")

    periodicos_df = pd.DataFrame()
    if "periodico" in df.columns:
        top_periodicos = df["periodico"].dropna().astype(str).value_counts().head(15)
        if not top_periodicos.empty:
            periodicos_df = top_periodicos.rename_axis("periodico").reset_index(name="publicacoes")

    tipos_df = pd.DataFrame()
    if "tipo" in df.columns:
        top_tipos = df["tipo"].dropna().astype(str).value_counts().head(10)
        if not top_tipos.empty:
            tipos_df = top_tipos.rename_axis("tipo").reset_index(name="publicacoes")

    termos_df = pd.DataFrame()
    if "titulo" in df.columns:
        termos = top_terms(df["titulo"], top_n=20)
        if not termos.empty:
            termos_df = termos

    summary_text = build_search_summary(
        query=query.strip(),
        docs=docs,
        total_scopus=result.total_results,
        total_cit=total_cit,
        media_cit=media_cit,
        ano_ini=ano_ini,
        ano_fim=ano_fim,
        por_ano=por_ano,
        dist_citacoes=dist_citacoes,
        autores_df=autores_df,
        periodicos_df=periodicos_df,
        tipos_df=tipos_df,
        termos_df=termos_df,
    )
    works_summary_text, works_summary_df = build_works_summary(df_display, top_n=20)

    st.subheader("Tabelas da análise")
    show_rank_table("Base de dados da busca", df_display)

    if not por_ano.empty:
        show_rank_table("Publicações por ano", por_ano)
    if not dist_citacoes.empty:
        show_rank_table("Distribuição de citações", dist_citacoes)
    if not autores_df.empty:
        show_rank_table("Top autores", autores_df)
    if not periodicos_df.empty:
        show_rank_table("Top periódicos", periodicos_df)
    if not tipos_df.empty:
        show_rank_table("Tipos de documento", tipos_df)
    if not termos_df.empty:
        show_rank_table("Termos mais frequentes nos títulos", termos_df)

    st.subheader("Gráficos da análise")

    if not por_ano.empty:
        show_rank_chart("Publicações por ano", por_ano, "ano", "publicacoes")
    if not dist_citacoes.empty:
        show_rank_chart(
            "Distribuição de citações",
            dist_citacoes,
            "faixa_citacoes",
            "documentos",
        )
    if not autores_df.empty:
        show_rank_chart("Top autores", autores_df, "autor", "publicacoes")
    if not periodicos_df.empty:
        show_rank_chart("Top periódicos", periodicos_df, "periodico", "publicacoes")
    if not tipos_df.empty:
        show_rank_chart("Tipos de documento", tipos_df, "tipo", "publicacoes")
    if not termos_df.empty:
        show_rank_chart(
            "Termos mais frequentes nos títulos",
            termos_df,
            "termo",
            "frequencia",
        )

    st.download_button(
        "Baixar CSV",
        data=df_display.to_csv(index=False).encode("utf-8"),
        file_name="bibliometria_scopus.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        "Baixar Excel",
        data=to_excel_bytes(df_display),
        file_name="bibliometria_scopus.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.subheader("Resumo da pesquisa")
    st.code(summary_text, language="text")
    st.download_button(
        "Baixar resumo (.txt)",
        data=summary_text.encode("utf-8"),
        file_name="resumo_pesquisa_scopus.txt",
        mime="text/plain",
        use_container_width=True,
    )

    st.subheader("Resumo dos trabalhos")
    st.code(works_summary_text, language="text")
    st.download_button(
        "Baixar resumo dos trabalhos (.txt)",
        data=works_summary_text.encode("utf-8"),
        file_name="resumo_trabalhos_scopus.txt",
        mime="text/plain",
        use_container_width=True,
    )

    st.subheader("Tabelas de resumo")
    show_rank_table("Resumo da análise", resumo_df)
    if not works_summary_df.empty:
        show_rank_table("Trabalhos mais citados (resumo)", works_summary_df)


if __name__ == "__main__":
    main()
