"""Bibliometria — módulo simples para análises bibliométricas.

Expondo funções principais para carregar dados, calcular métricas e gerar visualizações.
"""

from .io import load_bibliography
from .analysis import (
    abstract_term_frequency,
    author_document_counts,
    author_productivity_distribution,
    author_year_counts,
    citations_by_year,
    coauthorship_edges,
    cumulative_yearly_counts,
    most_cited_documents,
    research_overview,
    title_term_frequency,
    top_authors,
    top_journals,
    yearly_counts,
    yearly_growth_rates,
    keyword_frequency,
    citation_stats,
)
from .viz import (
    plot_author_trends,
    plot_bar,
    plot_coauthorship_network,
    plot_heatmap_author_year,
    plot_pie_top,
    plot_time_series,
    plot_vertical_bar,
)
from .pipeline import run_bibliometric_analysis

__all__ = [
    "load_bibliography",
    "cumulative_yearly_counts",
    "yearly_growth_rates",
    "citations_by_year",
    "author_year_counts",
    "author_productivity_distribution",
    "coauthorship_edges",
    "title_term_frequency",
    "abstract_term_frequency",
    "author_document_counts",
    "most_cited_documents",
    "research_overview",
    "top_authors",
    "top_journals",
    "yearly_counts",
    "keyword_frequency",
    "citation_stats",
    "plot_bar",
    "plot_vertical_bar",
    "plot_time_series",
    "plot_pie_top",
    "plot_author_trends",
    "plot_heatmap_author_year",
    "plot_coauthorship_network",
    "run_bibliometric_analysis",
]
