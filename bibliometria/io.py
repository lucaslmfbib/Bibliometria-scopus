from typing import Optional


def load_bibliography(path: str, encoding: Optional[str] = None):
    """Carrega um arquivo CSV ou Excel contendo registros bibliográficos.

    Estratégia:
    - Detecta extensão (.csv, .xls, .xlsx)
    - Usa pandas para leitura
    - Normaliza nomes de colunas comuns para: Authors, Title, Year, Source title (journal), Author Keywords, Cited by

    Retorna um pandas.DataFrame com colunas normalizadas (em caso de ausência, coluna não é criada).
    """
    # Import dentro da função para manter importação leve do pacote
    import os
    import pandas as pd

    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(path, encoding=encoding)
    elif ext in (".xls", ".xlsx"):
        df = pd.read_excel(path)
    else:
        # Tentar com pandas autodetect
        try:
            df = pd.read_csv(path, encoding=encoding)
        except Exception:
            df = pd.read_excel(path)

    # normalizar colunas (lowercase and stripped)
    orig_cols = {c: c.strip() for c in df.columns}
    df.rename(columns=orig_cols, inplace=True)
    cols = {c.lower(): c for c in df.columns}

    def try_get(df, names):
        for n in names:
            if n in cols:
                return df[cols[n]]
        return None

    # Mapear colunas comuns
    mapped = {}
    mapped['Authors'] = try_get(df, [
        'authors', 'author', 'author(s)', 'au', 'author(s) ', 'authors '
    ])
    mapped['Title'] = try_get(df, ['title', 'document title', 'article title'])
    mapped['Year'] = try_get(df, ['year', 'py', 'publication year'])
    mapped['Journal'] = try_get(df, ['source title', 'journal', 'journal title', 'source'])
    mapped['Keywords'] = try_get(df, ['author keywords', 'keywords', 'author keywords '])
    mapped['Cited by'] = try_get(df, ['cited by', 'times cited', 'cited_by'])

    out = pd.DataFrame()
    for k, v in mapped.items():
        if v is not None:
            out[k] = v

    # preserve other columns too
    other_cols = [c for c in df.columns if c not in out.columns]
    for c in other_cols:
        out[c] = df[c]

    # pequenas normalizações
    if 'Year' in out.columns:
        # tentar converter para int quando possível
        try:
            out['Year'] = pd.to_numeric(out['Year'], errors='coerce').astype('Int64')
        except Exception:
            pass

    return out
