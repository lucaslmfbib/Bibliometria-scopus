"""Exemplo mínimo de uso do pacote `bibliometria`.

Coloque um arquivo CSV/Excel com colunas típicas (Authors, Title, Year, Source title, Author Keywords, Cited by)
no caminho `data/sample.csv` ou passe um caminho próprio.
"""

from bibliometria import load_bibliography, top_authors, top_journals, yearly_counts, keyword_frequency


def run_demo(path: str):
    print(f"Carregando: {path}")
    df = load_bibliography(path)

    print('\nTop autores:')
    for a, c in top_authors(df, n=10):
        print(f"{a}: {c}")

    print('\nTop periódicos:')
    for j, c in top_journals(df, n=10):
        print(f"{j}: {c}")

    print('\nContagem por ano:')
    yc = yearly_counts(df)
    for y, c in yc.items():
        print(f"{y}: {c}")

    print('\nTop keywords:')
    for k, c in keyword_frequency(df, n=20):
        print(f"{k}: {c}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        p = sys.argv[1]
    else:
        p = 'data/sample.csv'
    run_demo(p)
