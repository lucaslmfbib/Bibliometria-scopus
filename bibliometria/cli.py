import argparse
from pathlib import Path
from typing import List, Optional

from .pipeline import run_bibliometric_analysis


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bibliometria",
        description="Executa análises bibliométricas a partir de CSV/XLSX.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Caminho do arquivo de entrada (.csv, .xls ou .xlsx).",
    )
    parser.add_argument(
        "--output-dir",
        default="analysis_output",
        help="Pasta de saída para JSON, CSVs e gráficos.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Quantidade máxima de itens nos rankings.",
    )
    parser.add_argument(
        "--encoding",
        default=None,
        help="Encoding do CSV (ex.: utf-8, latin1).",
    )
    parser.add_argument(
        "--sheet-name",
        default="0",
        help="Nome/índice da aba no Excel. Padrão: 0.",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Não gerar arquivos PNG.",
    )
    parser.add_argument(
        "--network-max-authors",
        type=int,
        default=30,
        help="Máximo de autores no grafo de coautoria.",
    )
    parser.add_argument(
        "--network-min-weight",
        type=int,
        default=1,
        help="Peso mínimo (coautorias) para desenhar arestas no grafo.",
    )
    return parser


def _parse_sheet_name(raw_value: str):
    return int(raw_value) if raw_value.isdigit() else raw_value


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    summary = run_bibliometric_analysis(
        input_path=args.input,
        output_dir=args.output_dir,
        top_n=args.top_n,
        encoding=args.encoding,
        sheet_name=_parse_sheet_name(args.sheet_name),
        save_plots=not args.no_plots,
        network_max_authors=args.network_max_authors,
        network_min_weight=args.network_min_weight,
    )

    output_path = Path(args.output_dir).resolve()
    print("Análise bibliométrica concluída.")
    print(f"Arquivo analisado: {summary['input_file']}")
    print(f"Total de documentos: {summary['total_documents']}")
    if summary.get("period_start") is not None:
        print(f"Período: {summary['period_start']} - {summary['period_end']}")
    print(f"Resultados salvos em: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
