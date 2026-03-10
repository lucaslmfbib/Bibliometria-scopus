from collections import Counter
from typing import List, Tuple, Dict


def _split_authors(cell: str) -> List[str]:
    if not cell or (isinstance(cell, float) and str(cell) == 'nan'):
        return []
    # autores geralmente separados por ";" ou ","
    if ';' in cell:
        parts = [a.strip() for a in cell.split(';') if a.strip()]
    else:
        parts = [a.strip() for a in cell.split(',') if a.strip()]
    return parts


def top_authors(df, n: int = 10) -> List[Tuple[str, int]]:
    """Retorna os top N autores por número de aparições."""
    authors_series = df.get('Authors')
    if authors_series is None:
        return []
    counter = Counter()
    for cell in authors_series.dropna().astype(str):
        for a in _split_authors(cell):
            counter[a] += 1
    return counter.most_common(n)


def top_journals(df, n: int = 10) -> List[Tuple[str, int]]:
    j = df.get('Journal')
    if j is None:
        return []
    counter = Counter()
    for cell in j.dropna().astype(str):
        counter[cell.strip()] += 1
    return counter.most_common(n)


def yearly_counts(df) -> Dict[int, int]:
    y = df.get('Year')
    if y is None:
        return {}
    counts = Counter()
    for val in y.dropna():
        try:
            counts[int(val)] += 1
        except Exception:
            continue
    # retornar como dict ordenado por ano
    return dict(sorted(counts.items()))


def keyword_frequency(df, n: int = 20) -> List[Tuple[str, int]]:
    k = df.get('Keywords')
    if k is None:
        return []
    counter = Counter()
    for cell in k.dropna().astype(str):
        # separar por ';' ou ',' ou '|' ou '\n'
        parts = []
        if ';' in cell:
            parts = [p.strip() for p in cell.split(';') if p.strip()]
        elif ',' in cell:
            parts = [p.strip() for p in cell.split(',') if p.strip()]
        elif '|' in cell:
            parts = [p.strip() for p in cell.split('|') if p.strip()]
        else:
            parts = [p.strip() for p in cell.split('\n') if p.strip()]
        for kw in parts:
            counter[kw.lower()] += 1
    return counter.most_common(n)


def citation_stats(df) -> Dict[str, float]:
    c = df.get('Cited by')
    import math
    if c is None:
        return {}
    vals = []
    for v in c.dropna():
        try:
            vals.append(float(v))
        except Exception:
            continue
    if not vals:
        return {}
    mean = sum(vals) / len(vals)
    med = sorted(vals)[len(vals) // 2]
    return {
        'count': len(vals),
        'mean': mean,
        'median': med,
        'min': min(vals),
        'max': max(vals),
    }
