from typing import Iterable


def plot_bar(items, title: str = None, xlabel: str = None, ylabel: str = "Count", top_n: int = 20):
    """Cria e retorna um gráfico de barras (matplotlib Figure) para uma lista de pares (label, value) ou um dict/Series.

    Importa matplotlib apenas dentro da função para não forçar dependências no import do pacote.
    """
    import matplotlib.pyplot as plt

    # aceitar list of (k,v) ou dict-like
    if hasattr(items, 'items'):
        pairs = list(items.items())
    else:
        pairs = list(items)

    pairs = pairs[:top_n]
    labels = [p[0] for p in pairs]
    values = [p[1] for p in pairs]

    fig, ax = plt.subplots(figsize=(8, max(4, 0.3 * len(labels))))
    ax.barh(range(len(labels)), values, color='tab:blue')
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    return fig


def plot_time_series(year_counts, title: str = None):
    """Plota uma série temporal simples (ano -> contagem)."""
    import matplotlib.pyplot as plt

    years = list(year_counts.keys())
    values = list(year_counts.values())
    fig, ax = plt.subplots()
    ax.plot(years, values, marker='o')
    if title:
        ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel('Count')
    fig.tight_layout()
    return fig
