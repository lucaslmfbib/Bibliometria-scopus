from __future__ import annotations

import io
import json
import sys
import tempfile
import zipfile
from collections.abc import Mapping
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

TOP_SOCIAL_LINKS = {
    "LinkedIn": "https://www.linkedin.com/in/lucaslmf/",
    "GitHub": "https://github.com/lucaslmfbib",
    "Instagram": "https://www.instagram.com/lucaslmf_/",
}


def _inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --bg-main: #f4efe6;
            --bg-panel: rgba(255, 250, 243, 0.92);
            --bg-panel-strong: #fffaf2;
            --ink: #1d1b18;
            --muted: #726a5f;
            --line: rgba(39, 31, 24, 0.12);
            --accent: #b54f2d;
            --accent-2: #215347;
            --shadow: 0 20px 60px rgba(41, 26, 17, 0.08);
            --radius-lg: 24px;
            --radius-md: 18px;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(181, 79, 45, 0.10), transparent 30%),
                radial-gradient(circle at top right, rgba(33, 83, 71, 0.12), transparent 34%),
                linear-gradient(180deg, #f7f2ea 0%, #f2ebe0 100%);
            color: var(--ink);
            font-family: 'IBM Plex Sans', sans-serif;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        h1, h2, h3 {
            font-family: 'Space Grotesk', sans-serif;
            color: var(--ink);
            letter-spacing: -0.03em;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(32, 30, 27, 0.95), rgba(24, 22, 20, 0.98));
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebar"] * {
            color: #f8efe4;
        }

        div[data-testid="stFileUploader"] > section,
        div[data-testid="stVerticalBlock"] div[data-testid="stTabs"] + div,
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            border-radius: var(--radius-md);
        }

        .hero-shell {
            background: linear-gradient(135deg, rgba(255,250,243,0.96), rgba(247,236,224,0.94));
            border: 1px solid var(--line);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
            padding: 1.4rem 1.5rem 1.2rem 1.5rem;
            margin-bottom: 1rem;
        }

        .hero-badge {
            display: inline-block;
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--accent-2);
            background: rgba(33, 83, 71, 0.10);
            border: 1px solid rgba(33, 83, 71, 0.18);
            border-radius: 999px;
            padding: 0.45rem 0.8rem;
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(2rem, 4vw, 3.6rem);
            line-height: 0.95;
            margin: 0;
            color: var(--ink);
        }

        .hero-subtitle {
            margin: 0.85rem 0 0 0;
            max-width: 860px;
            color: var(--muted);
            font-size: 1.02rem;
            line-height: 1.65;
        }

        .social-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1rem;
        }

        .social-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            text-decoration: none;
            color: var(--ink);
            background: rgba(255,255,255,0.82);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.55rem 0.9rem;
            font-size: 0.92rem;
            font-weight: 600;
        }

        .author-note {
            margin-top: 0.7rem;
            color: var(--muted);
            font-size: 0.95rem;
        }

        .workspace-card {
            background: var(--bg-panel);
            border: 1px solid var(--line);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow);
            padding: 1.2rem 1.3rem;
            margin: 1rem 0 1.1rem 0;
        }

        .workspace-title {
            font-family: 'Space Grotesk', sans-serif;
            margin: 0;
            font-size: 1.35rem;
        }

        .workspace-text {
            color: var(--muted);
            margin-top: 0.45rem;
            line-height: 1.6;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 0.9rem;
        }

        .chip {
            padding: 0.55rem 0.8rem;
            background: rgba(33, 83, 71, 0.07);
            border: 1px solid rgba(33, 83, 71, 0.16);
            border-radius: 999px;
            color: var(--accent-2);
            font-size: 0.9rem;
            font-weight: 600;
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.9rem;
            margin: 1rem 0 1.2rem 0;
        }

        .feature-card {
            background: var(--bg-panel);
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            padding: 1rem 1rem 0.9rem 1rem;
            min-height: 150px;
            box-shadow: var(--shadow);
        }

        .feature-card strong {
            display: block;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.02rem;
            margin-bottom: 0.45rem;
        }

        .feature-card span {
            color: var(--muted);
            line-height: 1.55;
            font-size: 0.95rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.9rem;
            margin: 0.8rem 0 1rem 0;
        }

        .stat-card {
            background: var(--bg-panel-strong);
            border: 1px solid var(--line);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow);
            padding: 1rem 1rem 0.9rem 1rem;
        }

        .stat-label {
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }

        .stat-value {
            color: var(--ink);
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.7rem;
            line-height: 1.1;
            margin-top: 0.45rem;
        }

        .stButton button {
            background: linear-gradient(135deg, #b54f2d, #c96c45);
            color: #fffaf4;
            border: none;
            border-radius: 999px;
            font-weight: 700;
            padding: 0.7rem 1.15rem;
            box-shadow: 0 12px 25px rgba(181, 79, 45, 0.22);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.65);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
        }

        .stTabs [aria-selected="true"] {
            background: rgba(181, 79, 45, 0.12);
            color: var(--accent);
            border-color: rgba(181, 79, 45, 0.26);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_hero(social_links: Dict[str, str]):
    social_html = ""
    if social_links:
        pills = [
            f'<a class="social-pill" href="{url}" target="_blank">{label}</a>'
            for label, url in social_links.items()
        ]
        social_html = f'<div class="social-row">{"".join(pills)}</div>'

    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-badge">Plataforma de Analise Bibliometrica</div>
            <h1 class="hero-title">Bibliometria em nuvem, com cara de software.</h1>
            <p class="hero-subtitle">
                Envie um arquivo CSV, Excel ou BibTeX e trabalhe em um painel unico com
                indicadores, tabelas, grafo de coautoria, nuvem de palavras e pacotes
                prontos para exportacao.
            </p>
            <div class="author-note">Criado pelo Bibliotecário e Advogado Lucas Martins</div>
            {social_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_feature_cards():
    st.markdown(
        """
        <div class="feature-grid">
            <div class="feature-card">
                <strong>Upload inteligente</strong>
                <span>Suporte para CSV, Excel e BibTeX com leitura automatica de campos bibliograficos.</span>
            </div>
            <div class="feature-card">
                <strong>Painel analitico</strong>
                <span>Metricas, ranking de autores, citacoes, crescimento anual e visoes prontas para leitura.</span>
            </div>
            <div class="feature-card">
                <strong>Visualizacoes executivas</strong>
                <span>Grafo de coautoria, nuvem de palavras, series temporais e imagens exportaveis.</span>
            </div>
            <div class="feature-card">
                <strong>Entrega em lote</strong>
                <span>Baixe ZIP com tabelas CSV, resumo JSON e figuras para apresentar ou continuar a analise.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_workspace_summary(
    upload_name: str,
    total_documents: Any,
    period_start: Any,
    period_end: Any,
    table_count: int,
    plot_count: int,
):
    chip_values = [
        f"Arquivo: {upload_name}" if upload_name else "Arquivo processado",
        f"Tabelas: {table_count}",
        f"Graficos: {plot_count}",
        "Formato cloud workspace",
    ]
    chips = "".join(f'<div class="chip">{value}</div>' for value in chip_values)
    st.markdown(
        f"""
        <section class="workspace-card">
            <h2 class="workspace-title">Workspace da analise</h2>
            <p class="workspace-text">
                Seu arquivo foi processado e os resultados estao organizados em modulos.
                Navegue entre quadro, nuvem de palavras, grafo, tabelas, graficos e exportacao.
            </p>
            <div class="chip-row">{chips}</div>
        </section>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Documentos</div>
                <div class="stat-value">{total_documents if total_documents is not None else "-"}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Inicio do periodo</div>
                <div class="stat-value">{period_start if period_start is not None else "-"}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Fim do periodo</div>
                <div class="stat-value">{period_end if period_end is not None else "-"}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Modulos ativos</div>
                <div class="stat-value">6+</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def _get_social_links() -> Dict[str, str]:
    links: Dict[str, str] = dict(TOP_SOCIAL_LINKS)
    labels = {
        "linkedin": "LinkedIn",
        "instagram": "Instagram",
        "x": "X",
        "twitter": "Twitter",
        "youtube": "YouTube",
        "github": "GitHub",
        "website": "Site",
    }

    try:
        configured = st.secrets.get("social_links", {})
    except Exception:
        configured = {}

    if not isinstance(configured, Mapping):
        configured = {}

    for key, label in labels.items():
        value = configured.get(key)
        if isinstance(value, str) and value.strip().startswith(("http://", "https://")):
            links[label] = value.strip()

    return links


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
            "upload_name": upload_name,
            "summary": summary,
            "summary_json": summary_json,
            "tables": tables,
            "plots": plots,
            "zip_bytes": zip_bytes,
        }


def main():
    st.set_page_config(page_title="Bibliometria", layout="wide")
    _inject_styles()
    social_links = _get_social_links()
    _render_hero(social_links)

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

        if social_links:
            st.divider()
            st.subheader("Minhas redes")
            for label, url in social_links.items():
                st.markdown(f"- [{label}]({url})")

    upload_col, info_col = st.columns([1.3, 0.7], gap="large")
    with upload_col:
        st.subheader("Central de envio")
        st.caption("Carregue a base bibliografica e inicie a leitura analitica do workspace.")
        uploaded_file = st.file_uploader(
            "Arquivo bibliografico",
            type=["csv", "xls", "xlsx", "bib"],
            help="Aceita CSV, XLS, XLSX e BibTeX (.bib).",
        )
        run_button = st.button("Rodar analise", type="primary", disabled=uploaded_file is None)
    with info_col:
        st.subheader("Fluxo de trabalho")
        st.caption("Uma jornada simples para transformar bases bibliograficas em evidencias visuais.")
        _render_feature_cards()

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
        st.info("Envie um arquivo e clique em 'Rodar analise' para abrir o workspace da pesquisa.")
        return

    summary = results["summary"]
    tables = results["tables"]
    upload_name = results.get("upload_name", "")
    total_documents = summary.get("total_documents")
    period_start = summary.get("period_start")
    period_end = summary.get("period_end")
    coauth_count = len(summary.get("coauthorship_edges", []))
    most_cited_table = tables.get("most_cited_documents.csv", pd.DataFrame()).copy()
    author_documents_table = tables.get("author_document_counts.csv", pd.DataFrame()).copy()
    overview_table = tables.get("research_overview.csv", pd.DataFrame()).copy()
    records_table = tables.get("research_records.csv", pd.DataFrame()).copy()
    word_cloud_terms_table = tables.get("word_cloud_terms.csv", pd.DataFrame()).copy()
    coauth_edges_table = tables.get("coauthorship_edges.csv", pd.DataFrame()).copy()
    coauth_graph_image = results["plots"].get("coauthorship_network.png")
    word_cloud_image = results["plots"].get("word_cloud.png")
    _render_workspace_summary(
        upload_name=upload_name,
        total_documents=total_documents,
        period_start=period_start,
        period_end=period_end,
        table_count=len(tables),
        plot_count=len(results["plots"]),
    )
    st.caption(f"Arestas de coautoria identificadas: {coauth_count}")

    tab_dashboard, tab_word_cloud, tab_graph, tab_tables, tab_plots, tab_raw, tab_download = st.tabs(
        ["Quadro da pesquisa", "Nuvem de palavras", "Grafo", "Tabelas", "Graficos", "Resumo JSON", "Download"]
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

        st.subheader("Termos da nuvem de palavras")
        st.caption("Frequencias combinadas a partir do titulo e do resumo.")
        if word_cloud_terms_table.empty:
            st.warning("Nao ha termos suficientes para montar a nuvem de palavras.")
        else:
            if "count" in word_cloud_terms_table.columns:
                word_cloud_terms_table["count"] = pd.to_numeric(
                    word_cloud_terms_table["count"],
                    errors="coerce",
                )
                display_word_cloud_terms = word_cloud_terms_table.sort_values(
                    by="count",
                    ascending=False,
                    na_position="last",
                )
            else:
                display_word_cloud_terms = word_cloud_terms_table
            st.dataframe(display_word_cloud_terms.head(50), width="stretch", height=300)

    with tab_word_cloud:
        st.subheader("Nuvem de palavras")
        st.caption("Visualizacao baseada nos termos mais frequentes de titulo e resumo.")
        if word_cloud_image is None:
            st.warning("A nuvem de palavras nao foi gerada para este arquivo.")
        else:
            st.image(
                word_cloud_image,
                caption="Nuvem de palavras gerada com os termos combinados de titulo e resumo",
                width="stretch",
            )

        st.subheader("Tabela de termos da nuvem")
        if word_cloud_terms_table.empty:
            st.warning("Nao ha tabela de termos para a nuvem de palavras.")
        else:
            display_word_cloud_terms = word_cloud_terms_table.copy()
            if "count" in display_word_cloud_terms.columns:
                display_word_cloud_terms["count"] = pd.to_numeric(
                    display_word_cloud_terms["count"],
                    errors="coerce",
                )
                display_word_cloud_terms = display_word_cloud_terms.sort_values(
                    by="count",
                    ascending=False,
                    na_position="last",
                )
            st.dataframe(display_word_cloud_terms, width="stretch", height=360)

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
