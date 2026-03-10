from collections import Counter, defaultdict
from itertools import combinations
import re
from typing import Dict, List, Tuple


def _split_authors(cell: str) -> List[str]:
    if cell is None:
        return []
    text = str(cell).strip()
    if not text or text.lower() in {"nan", "none"}:
        return []
    # autores geralmente separados por ";" (Scopus/WoS) ou "," em alguns exports
    if ";" in text:
        return [a.strip() for a in text.split(";") if a.strip()]
    return [a.strip() for a in text.split(",") if a.strip()]


def author_counts(df) -> Dict[str, int]:
    authors_series = df.get("Authors")
    if authors_series is None:
        return {}
    counter = Counter()
    for cell in authors_series.dropna().astype(str):
        for author in _split_authors(cell):
            counter[author] += 1
    return dict(counter)


def author_document_counts(df) -> List[Dict[str, object]]:
    counts = author_counts(df)
    records = [{"author": author, "documents": total} for author, total in counts.items()]
    records.sort(key=lambda item: item["documents"], reverse=True)
    return records


def top_authors(df, n: int = 10) -> List[Tuple[str, int]]:
    """Retorna os top N autores por número de aparições."""
    return Counter(author_counts(df)).most_common(n)


def top_journals(df, n: int = 10) -> List[Tuple[str, int]]:
    journal_series = df.get("Journal")
    if journal_series is None:
        return []
    counter = Counter()
    for cell in journal_series.dropna().astype(str):
        counter[cell.strip()] += 1
    return counter.most_common(n)


def yearly_counts(df) -> Dict[int, int]:
    year_series = df.get("Year")
    if year_series is None:
        return {}
    counts = Counter()
    for value in year_series.dropna():
        try:
            counts[int(value)] += 1
        except Exception:
            continue
    return dict(sorted(counts.items()))


def cumulative_yearly_counts(year_counts: Dict[int, int]) -> Dict[int, int]:
    running_total = 0
    cumulative = {}
    for year in sorted(year_counts):
        running_total += year_counts[year]
        cumulative[year] = running_total
    return cumulative


def yearly_growth_rates(year_counts: Dict[int, int]) -> Dict[int, float]:
    years = sorted(year_counts)
    growth = {}
    for index in range(1, len(years)):
        previous_year = years[index - 1]
        current_year = years[index]
        prev = year_counts[previous_year]
        curr = year_counts[current_year]
        if prev == 0:
            growth[current_year] = 0.0
        else:
            growth[current_year] = ((curr - prev) / prev) * 100.0
    return growth


def keyword_frequency(df, n: int = 20) -> List[Tuple[str, int]]:
    keyword_series = df.get("Keywords")
    if keyword_series is None:
        return []
    counter = Counter()
    for cell in keyword_series.dropna().astype(str):
        if ";" in cell:
            parts = [part.strip() for part in cell.split(";") if part.strip()]
        elif "," in cell:
            parts = [part.strip() for part in cell.split(",") if part.strip()]
        elif "|" in cell:
            parts = [part.strip() for part in cell.split("|") if part.strip()]
        else:
            parts = [part.strip() for part in cell.split("\n") if part.strip()]
        for keyword in parts:
            counter[keyword.lower()] += 1
    return counter.most_common(n)


def citation_stats(df) -> Dict[str, float]:
    cited_by_series = df.get("Cited by")
    if cited_by_series is None:
        return {}
    values = []
    for value in cited_by_series.dropna():
        try:
            values.append(float(value))
        except Exception:
            continue
    if not values:
        return {}
    sorted_values = sorted(values)
    median = sorted_values[len(sorted_values) // 2]
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "median": median,
        "min": min(values),
        "max": max(values),
    }


def citations_by_year(df) -> Dict[int, Dict[str, float]]:
    years = df.get("Year")
    cited_by = df.get("Cited by")
    if years is None or cited_by is None:
        return {}

    grouped = defaultdict(list)
    for year_value, citation_value in zip(years, cited_by):
        try:
            year = int(year_value)
            citation = float(citation_value)
            grouped[year].append(citation)
        except Exception:
            continue

    out = {}
    for year in sorted(grouped):
        vals = grouped[year]
        out[year] = {
            "count": len(vals),
            "mean": sum(vals) / len(vals),
            "total": sum(vals),
            "max": max(vals),
        }
    return out


def author_year_counts(df, top_n_authors: int = 10) -> Dict[str, Dict[int, int]]:
    year_series = df.get("Year")
    authors_series = df.get("Authors")
    if year_series is None or authors_series is None:
        return {}

    top_author_names = [author for author, _ in top_authors(df, top_n_authors)]
    if not top_author_names:
        return {}

    selected = set(top_author_names)
    matrix = {author: Counter() for author in top_author_names}

    for year_value, author_cell in zip(year_series, authors_series):
        try:
            year = int(year_value)
        except Exception:
            continue
        for author in _split_authors(author_cell):
            if author in selected:
                matrix[author][year] += 1

    return {
        author: dict(sorted(counter.items()))
        for author, counter in matrix.items()
        if counter
    }


def author_productivity_distribution(df) -> Dict[int, int]:
    counts = author_counts(df)
    if not counts:
        return {}
    distribution = Counter(counts.values())
    return dict(sorted(distribution.items()))


def coauthorship_edges(
    df,
    max_authors: int = 30,
    min_weight: int = 1,
) -> List[Tuple[str, str, int]]:
    authors_series = df.get("Authors")
    if authors_series is None:
        return []

    ordered_authors = [author for author, _ in top_authors(df, n=max_authors)]
    selected = set(ordered_authors)

    edges = Counter()
    for cell in authors_series.dropna().astype(str):
        authors = [author for author in _split_authors(cell) if author in selected]
        unique_authors = sorted(set(authors))
        if len(unique_authors) < 2:
            continue
        for left, right in combinations(unique_authors, 2):
            edges[(left, right)] += 1

    records = [
        (left, right, weight)
        for (left, right), weight in edges.items()
        if weight >= min_weight
    ]
    records.sort(key=lambda item: item[2], reverse=True)
    return records


_TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{3,}")
_STOPWORDS = {
    # portugues
    "para",
    "com",
    "sem",
    "sobre",
    "entre",
    "uma",
    "um",
    "uns",
    "umas",
    "dos",
    "das",
    "nos",
    "nas",
    "que",
    "por",
    "como",
    "mais",
    "menos",
    "tambem",
    "também",
    "aos",
    "aos",
    "ano",
    "anos",
    "estudo",
    "estudos",
    "analise",
    "análise",
    "metodo",
    "método",
    "metodos",
    "métodos",
    "resultados",
    "introducao",
    "introdução",
    "conclusao",
    "conclusão",
    "revista",
    "artigo",
    "artigos",
    "dados",
    "base",
    "bases",
    "nivel",
    "nível",
    "sistema",
    "sistemas",
    "modelo",
    "modelos",
    "paper",
    # ingles
    "the",
    "and",
    "for",
    "with",
    "without",
    "from",
    "into",
    "using",
    "use",
    "used",
    "this",
    "that",
    "these",
    "those",
    "their",
    "its",
    "our",
    "your",
    "his",
    "her",
    "they",
    "them",
    "are",
    "was",
    "were",
    "been",
    "being",
    "have",
    "has",
    "had",
    "will",
    "would",
    "can",
    "could",
    "should",
    "may",
    "might",
    "not",
    "than",
    "then",
    "also",
    "between",
    "over",
    "under",
    "about",
    "across",
    "within",
    "study",
    "studies",
    "analysis",
    "method",
    "methods",
    "results",
    "introduction",
    "conclusion",
    "journal",
    "article",
    "articles",
    "data",
    "based",
    "approach",
    "approaches",
    "new",
}


def _term_frequency(series, n: int = 30, min_len: int = 3) -> List[Tuple[str, int]]:
    counter = Counter()
    if series is None:
        return []
    for text in series.dropna().astype(str):
        for token in _TOKEN_PATTERN.findall(text.lower()):
            if len(token) < min_len:
                continue
            if token in _STOPWORDS:
                continue
            counter[token] += 1
    return counter.most_common(n)


def title_term_frequency(df, n: int = 30) -> List[Tuple[str, int]]:
    return _term_frequency(df.get("Title"), n=n)


def abstract_term_frequency(df, n: int = 30) -> List[Tuple[str, int]]:
    return _term_frequency(df.get("Abstract"), n=n)


def most_cited_documents(df, n: int = 100) -> List[Dict[str, object]]:
    import pandas as pd

    if "Cited by" not in df.columns:
        return []

    tmp = df.copy()
    tmp["citations"] = pd.to_numeric(tmp["Cited by"], errors="coerce")
    tmp = tmp.dropna(subset=["citations"])
    if tmp.empty:
        return []

    tmp = tmp.sort_values("citations", ascending=False).head(n)
    base_columns = [
        ("Title", "title"),
        ("Authors", "authors"),
        ("Year", "year"),
        ("Journal", "journal"),
        ("DOI", "doi"),
        ("Keywords", "keywords"),
        ("Abstract", "abstract"),
    ]

    records: List[Dict[str, object]] = []
    for rank, (_, row) in enumerate(tmp.iterrows(), start=1):
        rec: Dict[str, object] = {
            "rank": rank,
            "citations": float(row["citations"]),
        }
        for source_col, out_col in base_columns:
            if source_col in tmp.columns:
                value = row[source_col]
                if value is None:
                    rec[out_col] = None
                else:
                    text = str(value).strip()
                    rec[out_col] = text if text and text.lower() != "nan" else None
        records.append(rec)
    return records


def research_overview(df) -> List[Dict[str, object]]:
    import pandas as pd

    total_documents = int(len(df))
    years = yearly_counts(df)
    authors = author_counts(df)
    journals = df.get("Journal")
    journal_count = int(journals.dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()) if journals is not None else 0
    citations = pd.to_numeric(df.get("Cited by"), errors="coerce") if "Cited by" in df.columns else pd.Series(dtype=float)
    docs_with_citations = int(citations.notna().sum()) if not citations.empty else 0
    citations_total = float(citations.dropna().sum()) if docs_with_citations else 0.0
    citations_mean = float(citations.dropna().mean()) if docs_with_citations else 0.0
    docs_with_abstract = int(df["Abstract"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().shape[0]) if "Abstract" in df.columns else 0
    docs_with_keywords = int(df["Keywords"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().shape[0]) if "Keywords" in df.columns else 0

    period = "-"
    if years:
        period = f"{min(years)}-{max(years)}"

    metrics = [
        ("Total de documentos", total_documents),
        ("Periodo", period),
        ("Autores unicos", len(authors)),
        ("Periodicos unicos", journal_count),
        ("Total de citacoes", round(citations_total, 2)),
        ("Media de citacoes por documento", round(citations_mean, 2)),
        ("Documentos com citacoes", docs_with_citations),
        ("Documentos com resumo", docs_with_abstract),
        ("Documentos com palavras-chave", docs_with_keywords),
    ]

    return [{"indicador": key, "valor": value} for key, value in metrics]
