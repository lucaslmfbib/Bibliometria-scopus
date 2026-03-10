from __future__ import annotations

import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError

# Permite executar tanto de dentro quanto de fora do diretório do pacote.
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from bibliometria.pipeline import run_bibliometric_analysis


def _parse_sheet_name(raw_value: str):
    value = raw_value.strip()
    if not value:
        return 0
    return int(value) if value.isdigit() else value


def _build_zip(output_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(output_dir.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, arcname=file_path.name)
    return buffer.getvalue()


def _run_analysis(
    upload_name: str,
    upload_bytes: bytes,
    top_n: int,
    encoding: str,
    sheet_name_raw: str,
    generate_plots: bool,
    network_max_authors: int,
    network_min_weight: int,
) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="bibliometria_streamlit_") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / upload_name
        input_path.write_bytes(upload_bytes)
        output_dir = temp_path / "analysis_output"

        summary = run_bibliometric_analysis(
            input_path=input_path,
            output_dir=output_dir,
            top_n=top_n,
            encoding=encoding or None,
            sheet_name=_parse_sheet_name(sheet_name_raw),
            save_plots=generate_plots,
            network_max_authors=network_max_authors,
            network_min_weight=network_min_weight,
        )

        tables = {}
        for csv_path in sorted(output_dir.glob("*.csv")):
            try:
                tables[csv_path.name] = pd.read_csv(csv_path)
            except EmptyDataError:
                tables[csv_path.name] = pd.DataFrame()

        plots = {}
        for png_path in sorted(output_dir.glob("*.png")):
            plots[png_path.name] = png_path.read_bytes()

        zip_bytes = _build_zip(output_dir)
        summary_json = (output_dir / "summary.json").read_text(encoding="utf-8")

        return {
            "summary": summary,
            "summary_json": summary_json,
            "tables": tables,
            "plots": plots,
            "zip_bytes": zip_bytes,
        }


def main():
    st.set_page_config(page_title="Bibliometria", layout="wide")
    st.title("Analise Bibliometrica com CSV ou Excel")
    st.caption("Envie um arquivo e gere tabelas, graficos e grafo de coautoria.")

    with st.sidebar:
        st.header("Configuracoes")
        top_n = st.slider("Top N", min_value=5, max_value=100, value=20, step=1)
        encoding = st.text_input("Encoding CSV (opcional)", value="")
        sheet_name = st.text_input("Aba do Excel (indice ou nome)", value="0")
        generate_plots = st.checkbox("Gerar graficos", value=True)
        network_max_authors = st.slider(
            "Maximo de autores no grafo",
            min_value=10,
            max_value=100,
            value=30,
            step=1,
        )
        network_min_weight = st.slider(
            "Peso minimo da aresta",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
        )

    uploaded_file = st.file_uploader(
        "Arquivo bibliografico",
        type=["csv", "xls", "xlsx"],
        help="Aceita CSV, XLS e XLSX.",
    )

    run_button = st.button("Rodar analise", type="primary", disabled=uploaded_file is None)
    if run_button and uploaded_file is not None:
        with st.spinner("Processando analise bibliometrica..."):
            try:
                st.session_state["results"] = _run_analysis(
                    upload_name=uploaded_file.name,
                    upload_bytes=uploaded_file.getvalue(),
                    top_n=top_n,
                    encoding=encoding,
                    sheet_name_raw=sheet_name,
                    generate_plots=generate_plots,
                    network_max_authors=network_max_authors,
                    network_min_weight=network_min_weight,
                )
            except Exception as exc:
                st.error(f"Falha ao processar o arquivo: {exc}")

    results = st.session_state.get("results")
    if not results:
        st.info("Envie um arquivo e clique em 'Rodar analise'.")
        return

    summary = results["summary"]
    tables = results["tables"]
    total_documents = summary.get("total_documents")
    period_start = summary.get("period_start")
    period_end = summary.get("period_end")
    coauth_count = len(summary.get("coauthorship_edges", []))
    most_cited_table = tables.get("most_cited_documents.csv", pd.DataFrame()).copy()
    author_documents_table = tables.get("author_document_counts.csv", pd.DataFrame()).copy()
    overview_table = tables.get("research_overview.csv", pd.DataFrame()).copy()
    records_table = tables.get("research_records.csv", pd.DataFrame()).copy()
    title_terms_table = tables.get("title_terms.csv", pd.DataFrame()).copy()
    abstract_terms_table = tables.get("abstract_terms.csv", pd.DataFrame()).copy()
    coauth_edges_table = tables.get("coauthorship_edges.csv", pd.DataFrame()).copy()
    coauth_graph_image = results["plots"].get("coauthorship_network.png")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Documentos", total_documents)
    col2.metric("Inicio", period_start if period_start is not None else "-")
    col3.metric("Fim", period_end if period_end is not None else "-")
    col4.metric("Arestas coautoria", coauth_count)

    tab_dashboard, tab_graph, tab_tables, tab_plots, tab_raw, tab_download = st.tabs(
        ["Quadro da pesquisa", "Grafo", "Tabelas", "Graficos", "Resumo JSON", "Download"]
    )

    with tab_dashboard:
        st.subheader("Quadro geral da pesquisa")
        if overview_table.empty:
            st.warning("Tabela de quadro geral indisponivel para este arquivo.")
        else:
            st.table(overview_table)

        st.subheader("Informacoes dos documentos")
        if records_table.empty:
            st.warning("Nao foi possivel montar a tabela de documentos.")
        else:
            st.dataframe(records_table, width="stretch", height=320)

        st.subheader("Autores e numero de trabalhos")
        if author_documents_table.empty:
            st.warning("Nao ha dados de autores para montar a tabela.")
        else:
            author_order = st.radio(
                "Ordenacao da tabela de autores",
                ["Decrescente", "Crescente"],
                index=0,
                horizontal=True,
            )
            if "documents" in author_documents_table.columns:
                author_documents_table["documents"] = pd.to_numeric(
                    author_documents_table["documents"],
                    errors="coerce",
                )
                display_authors = author_documents_table.sort_values(
                    by="documents",
                    ascending=(author_order == "Crescente"),
                    na_position="last",
                )
            else:
                display_authors = author_documents_table
            st.dataframe(display_authors, width="stretch", height=300)

        st.subheader("Documentos mais citados")
        if most_cited_table.empty:
            st.warning("Nao ha dados de citacao para montar ranking.")
        else:
            citation_order = st.radio(
                "Ordenacao das citacoes",
                ["Crescente", "Decrescente"],
                index=0,
                horizontal=True,
            )
            ascending = citation_order == "Crescente"
            if "citations" in most_cited_table.columns:
                most_cited_table["citations"] = pd.to_numeric(
                    most_cited_table["citations"],
                    errors="coerce",
                )
                display_cited = most_cited_table.sort_values(
                    by="citations",
                    ascending=ascending,
                    na_position="last",
                )
            else:
                display_cited = most_cited_table
            st.dataframe(display_cited, width="stretch", height=320)

        col_kw_1, col_kw_2 = st.columns(2)
        with col_kw_1:
            st.subheader("Palavras-chave no titulo")
            if title_terms_table.empty:
                st.warning("Sem termos no titulo para exibir.")
            else:
                st.dataframe(title_terms_table, width="stretch", height=300)
        with col_kw_2:
            st.subheader("Palavras-chave no resumo")
            if abstract_terms_table.empty:
                st.warning("Sem termos no resumo para exibir.")
            else:
                st.dataframe(abstract_terms_table, width="stretch", height=300)

    with tab_tables:
        if not tables:
            st.warning("Nenhuma tabela CSV foi gerada.")
        else:
            selected_table = st.selectbox("Tabela", list(tables.keys()))
            st.dataframe(tables[selected_table], width="stretch")

    with tab_graph:
        st.subheader("Grafo de coautoria")
        if coauth_graph_image is None:
            st.warning("O grafo de coautoria nao foi gerado para este arquivo.")
        else:
            st.image(
                coauth_graph_image,
                caption="Rede de coautoria entre autores (peso da aresta = numero de coautorias)",
                width="stretch",
            )

        st.subheader("Arestas do grafo")
        if coauth_edges_table.empty:
            st.warning("Nao ha arestas de coautoria para exibir.")
        else:
            max_edges = min(300, len(coauth_edges_table))
            n_edges = st.slider(
                "Quantidade de arestas exibidas",
                min_value=10 if max_edges >= 10 else 1,
                max_value=max_edges,
                value=min(50, max_edges),
                step=1,
            )
            if "weight" in coauth_edges_table.columns:
                coauth_edges_table["weight"] = pd.to_numeric(
                    coauth_edges_table["weight"],
                    errors="coerce",
                )
                display_edges = coauth_edges_table.sort_values(
                    by="weight",
                    ascending=False,
                    na_position="last",
                ).head(n_edges)
            else:
                display_edges = coauth_edges_table.head(n_edges)
            st.dataframe(display_edges, width="stretch", height=320)

    with tab_plots:
        plots = results["plots"]
        if not plots:
            st.warning("Nenhum grafico foi gerado.")
        else:
            for file_name in sorted(plots):
                st.image(plots[file_name], caption=file_name, width="stretch")

    with tab_raw:
        st.code(json.dumps(summary, indent=2, ensure_ascii=False), language="json")

    with tab_download:
        st.download_button(
            label="Baixar resultados (ZIP)",
            data=results["zip_bytes"],
            file_name="analysis_output.zip",
            mime="application/zip",
        )


if __name__ == "__main__":
    main()
