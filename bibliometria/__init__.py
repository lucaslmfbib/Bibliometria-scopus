"""Bibliometria — módulo simples para análises bibliométricas.

Expondo funções principais para carregar dados, calcular métricas e gerar visualizações.
"""

from .io import load_bibliography
from .analysis import (
    top_authors,
    top_journals,
    yearly_counts,
    keyword_frequency,
    citation_stats,
)
from .viz import plot_bar, plot_time_series

__all__ = [
    "load_bibliography",
    "top_authors",
    "top_journals",
    "yearly_counts",
    "keyword_frequency",
    "citation_stats",
    "plot_bar",
    "plot_time_series",
]
