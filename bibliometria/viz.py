import math
import os
import tempfile
from collections import Counter


def _get_pyplot():
    # backend não interativo para execução em servidor/terminal sem display
    mpl_dir = os.path.join(tempfile.gettempdir(), "matplotlib")
    os.makedirs(mpl_dir, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", mpl_dir)

    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def _pairs(items, top_n: int = 20):
    if hasattr(items, "items"):
        pairs = list(items.items())
    else:
        pairs = list(items)
    return pairs[:top_n]


def plot_bar(items, title: str = None, xlabel: str = None, ylabel: str = "Count", top_n: int = 20):
    plt = _get_pyplot()

    pairs = _pairs(items, top_n=top_n)
    labels = [str(label) for label, _ in pairs]
    values = [value for _, value in pairs]

    fig, ax = plt.subplots(figsize=(9, max(4, 0.35 * len(labels))))
    ax.barh(range(len(labels)), values, color="tab:blue")
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


def plot_vertical_bar(items, title: str = None, xlabel: str = None, ylabel: str = "Count", top_n: int = 200):
    plt = _get_pyplot()

    pairs = _pairs(items, top_n=top_n)
    labels = [str(label) for label, _ in pairs]
    values = [value for _, value in pairs]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values, color="tab:orange")
    ax.tick_params(axis="x", rotation=45)
    if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    return fig


def plot_time_series(year_counts, title: str = None, ylabel: str = "Count"):
    plt = _get_pyplot()

    years = list(year_counts.keys())
    values = list(year_counts.values())
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(years, values, marker="o", color="tab:blue", linewidth=2)
    ax.grid(alpha=0.25)
    if title:
        ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    return fig


def plot_pie_top(items, title: str = None, top_n: int = 10):
    plt = _get_pyplot()

    pairs = _pairs(items, top_n=top_n)
    labels = [str(label) for label, _ in pairs]
    values = [value for _, value in pairs]
    if not values:
        fig, _ = plt.subplots()
        return fig

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    return fig


def plot_author_trends(author_year_matrix, title: str = None):
    plt = _get_pyplot()

    all_years = sorted({year for series in author_year_matrix.values() for year in series})
    fig, ax = plt.subplots(figsize=(11, 6))

    for author, counts in author_year_matrix.items():
        y_values = [counts.get(year, 0) for year in all_years]
        ax.plot(all_years, y_values, marker="o", linewidth=1.8, label=author)

    if title:
        ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Publicações")
    ax.grid(alpha=0.25)
    if author_year_matrix:
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0.0, fontsize=8)
    fig.tight_layout()
    return fig


def plot_heatmap_author_year(author_year_matrix, title: str = None):
    plt = _get_pyplot()
    import numpy as np

    authors = list(author_year_matrix.keys())
    years = sorted({year for matrix in author_year_matrix.values() for year in matrix})
    if not authors or not years:
        fig, _ = plt.subplots()
        return fig

    matrix = np.array(
        [[author_year_matrix[author].get(year, 0) for year in years] for author in authors],
        dtype=float,
    )

    fig, ax = plt.subplots(figsize=(max(10, len(years) * 0.8), max(5, len(authors) * 0.45)))
    image = ax.imshow(matrix, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, rotation=45)
    ax.set_yticks(range(len(authors)))
    ax.set_yticklabels(authors)
    if title:
        ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Author")
    fig.colorbar(image, ax=ax, label="Publicações")
    fig.tight_layout()
    return fig


def plot_coauthorship_network(edges, title: str = None, max_nodes: int = 30):
    plt = _get_pyplot()

    if not edges:
        fig, _ = plt.subplots()
        return fig

    degree = Counter()
    for left, right, weight in edges:
        degree[left] += weight
        degree[right] += weight

    authors = [author for author, _ in degree.most_common(max_nodes)]
    author_set = set(authors)
    filtered_edges = [
        (left, right, weight)
        for left, right, weight in edges
        if left in author_set and right in author_set
    ]
    if not filtered_edges:
        fig, _ = plt.subplots()
        return fig

    positions = {}
    total = len(authors)
    for idx, author in enumerate(authors):
        angle = 2 * math.pi * idx / total
        positions[author] = (math.cos(angle), math.sin(angle))

    max_weight = max(weight for _, _, weight in filtered_edges) or 1
    max_degree = max(degree[a] for a in authors) or 1

    fig, ax = plt.subplots(figsize=(11, 11))
    for left, right, weight in filtered_edges:
        x1, y1 = positions[left]
        x2, y2 = positions[right]
        scale = weight / max_weight
        ax.plot(
            [x1, x2],
            [y1, y2],
            color="tab:gray",
            alpha=0.15 + 0.7 * scale,
            linewidth=0.5 + 4.0 * scale,
            zorder=1,
        )

    x_coords = []
    y_coords = []
    sizes = []
    labels = []
    for author in authors:
        x, y = positions[author]
        x_coords.append(x)
        y_coords.append(y)
        sizes.append(150 + 900 * (degree[author] / max_degree))
        labels.append(author)

    ax.scatter(x_coords, y_coords, s=sizes, c="tab:blue", alpha=0.9, edgecolors="white", zorder=2)
    for x, y, label in zip(x_coords, y_coords, labels):
        ax.text(x * 1.08, y * 1.08, label, ha="center", va="center", fontsize=8)

    if title:
        ax.set_title(title)
    ax.axis("off")
    ax.set_aspect("equal")
    fig.tight_layout()
    return fig
