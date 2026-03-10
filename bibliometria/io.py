import unicodedata
from pathlib import Path
from typing import Optional, Union


def _normalize_header(name: str) -> str:
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.strip().lower().replace("_", " ").split())


def load_bibliography(
    path: Union[str, Path],
    encoding: Optional[str] = None,
    sheet_name: Union[str, int] = 0,
):
    """Carrega um arquivo CSV/Excel contendo registros bibliográficos.

    Colunas conhecidas são normalizadas para:
    - Authors
    - Title
    - Year
    - Journal
    - Keywords
    - Cited by
    - Abstract
    - DOI

    Demais colunas do arquivo original são preservadas.
    """
    import pandas as pd

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    ext = file_path.suffix.lower()
    if ext == ".csv":
        # sep=None habilita autodetecção de delimitador (vírgula, ponto e vírgula etc.)
        df = pd.read_csv(file_path, encoding=encoding, sep=None, engine="python")
    elif ext in (".xls", ".xlsx"):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    else:
        # fallback por autodetecção
        try:
            df = pd.read_csv(file_path, encoding=encoding, sep=None, engine="python")
        except Exception:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

    df = df.rename(columns={c: str(c).strip() for c in df.columns})
    normalized_columns = {_normalize_header(c): c for c in df.columns}

    def try_get(names):
        for name in names:
            original = normalized_columns.get(_normalize_header(name))
            if original is not None:
                return df[original]
        return None

    mapped = {
        "Authors": try_get(
            [
                "authors",
                "author",
                "author(s)",
                "au",
                "autores",
            ]
        ),
        "Title": try_get(
            [
                "title",
                "document title",
                "article title",
                "titulo",
            ]
        ),
        "Year": try_get(
            [
                "year",
                "py",
                "publication year",
                "ano",
            ]
        ),
        "Journal": try_get(
            [
                "source title",
                "journal",
                "journal title",
                "source",
                "periodico",
                "revista",
            ]
        ),
        "Keywords": try_get(
            [
                "author keywords",
                "keywords",
                "index keywords",
                "palavras-chave",
                "palavras chave",
            ]
        ),
        "Cited by": try_get(
            [
                "cited by",
                "times cited",
                "cited_by",
                "citado por",
            ]
        ),
        "Abstract": try_get(
            [
                "abstract",
                "summary",
                "resumo",
                "description",
                "ab",
            ]
        ),
        "DOI": try_get(
            [
                "doi",
                "document object identifier",
                "article doi",
                "id doi",
            ]
        ),
    }

    out = pd.DataFrame()
    for canonical, series in mapped.items():
        if series is not None:
            out[canonical] = series

    canonical_set = set(out.columns)
    for col in df.columns:
        if col not in canonical_set:
            out[col] = df[col]

    if "Year" in out.columns:
        out["Year"] = pd.to_numeric(out["Year"], errors="coerce").astype("Int64")

    return out
