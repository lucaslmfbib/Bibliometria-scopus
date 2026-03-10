from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .analysis import (
    abstract_term_frequency,
    author_document_counts,
    author_productivity_distribution,
    author_year_counts,
    citation_stats,
    citations_by_year,
    coauthorship_edges,
    cumulative_yearly_counts,
    keyword_frequency,
    most_cited_documents,
    research_overview,
    title_term_frequency,
    top_authors,
    top_journals,
    yearly_growth_rates,
    yearly_counts,
)
from .io import load_bibliography
from .viz import (
    plot_author_trends,
    plot_bar,
    plot_coauthorship_network,
    plot_heatmap_author_year,
    plot_pie_top,
    plot_time_series,
    plot_vertical_bar,
)


def _pairs_to_records(
    pairs: List[Tuple[str, int]],
    key_name: str,
    value_name: str = "count",
) -> List[Dict[str, Union[str, int]]]:
    return [{key_name: key, value_name: value} for key, value in pairs]


def _write_csv(records, path: Path, columns: List[str]):
    import pandas as pd

    pd.DataFrame(records, columns=columns).to_csv(path, index=False)


def run_bibliometric_analysis(
    input_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = "analysis_output",
    top_n: int = 20,
    encoding: Optional[str] = None,
    sheet_name: Union[str, int] = 0,
    save_plots: bool = True,
    network_max_authors: int = 30,
    network_min_weight: int = 1,
) -> Dict[str, object]:
    """Executa análises bibliométricas completas a partir de um CSV/XLSX.

    Retorna um dicionário com os principais resultados e, opcionalmente,
    salva relatórios em disco.
    """
    import pandas as pd

    source_path = Path(input_path)
    df = load_bibliography(source_path, encoding=encoding, sheet_name=sheet_name)

    total_documents = int(len(df))
    years = yearly_counts(df)
    authors = top_authors(df, n=top_n)
    author_documents = author_document_counts(df)
    journals = top_journals(df, n=top_n)
    keywords = keyword_frequency(df, n=top_n)
    title_terms = title_term_frequency(df, n=max(top_n, 20))
    abstract_terms = abstract_term_frequency(df, n=max(top_n, 20))
    citations = citation_stats(df)
    cited_docs = most_cited_documents(df, n=max(top_n * 10, 100))
    overview = research_overview(df)
    cumulative_years = cumulative_yearly_counts(years)
    growth_years = yearly_growth_rates(years)
    citations_year = citations_by_year(df)
    authors_per_year = author_year_counts(df, top_n_authors=min(top_n, 20))
    productivity_distribution = author_productivity_distribution(df)
    coauth_edges = coauthorship_edges(
        df,
        max_authors=network_max_authors,
        min_weight=network_min_weight,
    )

    year_values = list(years.keys())
    summary = {
        "input_file": str(source_path.resolve()),
        "total_documents": total_documents,
        "columns_available": list(df.columns),
        "period_start": min(year_values) if year_values else None,
        "period_end": max(year_values) if year_values else None,
        "yearly_counts": years,
        "top_authors": _pairs_to_records(authors, "author"),
        "author_document_counts": author_documents,
        "top_journals": _pairs_to_records(journals, "journal"),
        "top_keywords": _pairs_to_records(keywords, "keyword"),
        "top_title_terms": _pairs_to_records(title_terms, "term"),
        "top_abstract_terms": _pairs_to_records(abstract_terms, "term"),
        "citation_stats": citations,
        "most_cited_documents": cited_docs[: max(top_n, 20)],
        "research_overview": overview,
        "yearly_cumulative": cumulative_years,
        "yearly_growth_pct": growth_years,
        "citations_by_year": {
            year: values for year, values in citations_year.items()
        },
        "author_year_counts": {
            author: values for author, values in authors_per_year.items()
        },
        "author_productivity_distribution": productivity_distribution,
        "coauthorship_edges": [
            {"author_1": left, "author_2": right, "weight": weight}
            for left, right, weight in coauth_edges
        ],
    }

    if output_dir is None:
        return summary

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON principal para integração com outros fluxos
    json_path = out_dir / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # Tabelas em CSV para uso em planilhas e BI (com cabeçalho mesmo sem linhas)
    _write_csv(summary["top_authors"], out_dir / "top_authors.csv", ["author", "count"])
    _write_csv(summary["author_document_counts"], out_dir / "author_document_counts.csv", ["author", "documents"])
    _write_csv(summary["top_journals"], out_dir / "top_journals.csv", ["journal", "count"])
    _write_csv(summary["top_keywords"], out_dir / "top_keywords.csv", ["keyword", "count"])
    _write_csv(summary["top_title_terms"], out_dir / "title_terms.csv", ["term", "count"])
    _write_csv(summary["top_abstract_terms"], out_dir / "abstract_terms.csv", ["term", "count"])
    _write_csv(cited_docs, out_dir / "most_cited_documents.csv", [
        "rank",
        "citations",
        "title",
        "authors",
        "year",
        "journal",
        "doi",
        "keywords",
        "abstract",
    ])
    _write_csv(overview, out_dir / "research_overview.csv", ["indicador", "valor"])

    preferred_cols = ["Title", "Authors", "Year", "Journal", "Cited by", "Keywords", "Abstract", "DOI"]
    available_cols = [col for col in preferred_cols if col in df.columns]
    if available_cols:
        research_records = df[available_cols].copy()
        if "Cited by" in research_records.columns:
            research_records["Cited by"] = pd.to_numeric(research_records["Cited by"], errors="coerce")
        research_records.to_csv(out_dir / "research_records.csv", index=False)
    else:
        _write_csv([], out_dir / "research_records.csv", preferred_cols)
    _write_csv(
        [{"year": year, "count": count} for year, count in summary["yearly_counts"].items()],
        out_dir / "yearly_counts.csv",
        ["year", "count"],
    )
    _write_csv(
        [{"year": year, "count": count} for year, count in summary["yearly_cumulative"].items()],
        out_dir / "yearly_cumulative.csv",
        ["year", "count"],
    )
    _write_csv(
        [{"year": year, "growth_pct": growth} for year, growth in summary["yearly_growth_pct"].items()],
        out_dir / "yearly_growth_pct.csv",
        ["year", "growth_pct"],
    )
    _write_csv(
        [
            {
                "author": author,
                "year": year,
                "count": count,
            }
            for author, year_map in summary["author_year_counts"].items()
            for year, count in year_map.items()
        ],
        out_dir / "author_year_counts.csv",
        ["author", "year", "count"],
    )
    _write_csv(
        [{"publications": pubs, "authors_count": freq} for pubs, freq in productivity_distribution.items()],
        out_dir / "author_productivity_distribution.csv",
        ["publications", "authors_count"],
    )
    _write_csv(
        summary["coauthorship_edges"],
        out_dir / "coauthorship_edges.csv",
        ["author_1", "author_2", "weight"],
    )

    if citations:
        _write_csv([citations], out_dir / "citation_stats.csv", ["count", "mean", "median", "min", "max"])
    else:
        _write_csv([], out_dir / "citation_stats.csv", ["count", "mean", "median", "min", "max"])
    if citations_year:
        _write_csv(
            [{"year": year, **stats} for year, stats in citations_year.items()],
            out_dir / "citations_by_year.csv",
            ["year", "count", "mean", "total", "max"],
        )
    else:
        _write_csv([], out_dir / "citations_by_year.csv", ["year", "count", "mean", "total", "max"])

    if save_plots:
        mpl_dir = os.path.join(tempfile.gettempdir(), "matplotlib")
        os.makedirs(mpl_dir, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", mpl_dir)

        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        if authors:
            fig = plot_bar(authors, title=f"Top {top_n} autores", xlabel="Publicações")
            fig.savefig(out_dir / "top_authors_barh.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

            fig = plot_pie_top(authors, title=f"Participação dos top {min(10, top_n)} autores", top_n=min(10, top_n))
            fig.savefig(out_dir / "top_authors_pie.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if journals:
            fig = plot_bar(journals, title=f"Top {top_n} periódicos", xlabel="Publicações")
            fig.savefig(out_dir / "top_journals_barh.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if keywords:
            fig = plot_bar(keywords, title=f"Top {top_n} palavras-chave", xlabel="Frequência")
            fig.savefig(out_dir / "top_keywords_barh.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if title_terms:
            fig = plot_bar(title_terms, title=f"Top {max(top_n, 20)} termos no título", xlabel="Frequência")
            fig.savefig(out_dir / "title_terms_barh.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if abstract_terms:
            fig = plot_bar(abstract_terms, title=f"Top {max(top_n, 20)} termos no resumo", xlabel="Frequência")
            fig.savefig(out_dir / "abstract_terms_barh.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if cited_docs:
            cited_pairs = [(rec.get("title") or f"Documento {idx + 1}", rec.get("citations", 0)) for idx, rec in enumerate(cited_docs[:top_n])]
            fig = plot_bar(cited_pairs, title=f"Top {top_n} documentos mais citados", xlabel="Citações")
            fig.savefig(out_dir / "most_cited_documents_barh.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if years:
            fig = plot_time_series(years, title="Publicações por ano", ylabel="Quantidade")
            fig.savefig(out_dir / "yearly_counts_line.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

            fig = plot_vertical_bar(years, title="Publicações por ano (barras)", xlabel="Ano", ylabel="Quantidade")
            fig.savefig(out_dir / "yearly_counts_bar.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

            fig = plot_time_series(
                cumulative_years,
                title="Publicações acumuladas por ano",
                ylabel="Acumulado",
            )
            fig.savefig(out_dir / "yearly_cumulative_line.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if growth_years:
            fig = plot_vertical_bar(
                growth_years,
                title="Crescimento anual das publicações (%)",
                xlabel="Ano",
                ylabel="% crescimento",
            )
            fig.savefig(out_dir / "yearly_growth_pct_bar.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if authors_per_year:
            fig = plot_author_trends(authors_per_year, title="Evolução anual dos principais autores")
            fig.savefig(out_dir / "author_trends_line.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

            fig = plot_heatmap_author_year(authors_per_year, title="Heatmap autor x ano")
            fig.savefig(out_dir / "author_year_heatmap.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if productivity_distribution:
            fig = plot_vertical_bar(
                productivity_distribution,
                title="Distribuição de produtividade de autores",
                xlabel="Nº de publicações por autor",
                ylabel="Nº de autores",
            )
            fig.savefig(out_dir / "author_productivity_distribution_bar.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if coauth_edges:
            fig = plot_coauthorship_network(
                coauth_edges,
                title="Grafo de coautoria",
                max_nodes=network_max_authors,
            )
            fig.savefig(out_dir / "coauthorship_network.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

        if citations_year:
            mean_by_year = {year: stats["mean"] for year, stats in citations_year.items()}
            total_by_year = {year: stats["total"] for year, stats in citations_year.items()}

            fig = plot_time_series(
                mean_by_year,
                title="Média de citações por ano de publicação",
                ylabel="Citações médias",
            )
            fig.savefig(out_dir / "citations_by_year_mean_line.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

            fig = plot_vertical_bar(
                total_by_year,
                title="Citações totais por ano de publicação",
                xlabel="Ano",
                ylabel="Citações totais",
            )
            fig.savefig(out_dir / "citations_by_year_total_bar.png", dpi=150, bbox_inches="tight")
            plt.close(fig)

    return summary
