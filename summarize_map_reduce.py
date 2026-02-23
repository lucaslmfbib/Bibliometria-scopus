#!/usr/bin/env python3
"""Summarize long text files using LangChain map-reduce."""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter


def summarize_text(
    text: str,
    model_name: str = "gpt-4o-mini",
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> str:
    """Return a final summary generated with map-reduce."""
    if not text.strip():
        raise ValueError("Input text is empty.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    docs = splitter.create_documents([text])

    llm = ChatOpenAI(model=model_name, temperature=0)
    parser = StrOutputParser()

    map_prompt = ChatPromptTemplate.from_template(
        "Você é um assistente especialista em sumarização.\n"
        "Resuma o trecho abaixo em até 5 bullets curtos, mantendo fatos principais.\n\n"
        "Trecho:\n{context}"
    )
    map_chain = map_prompt | llm | parser
    partial_summaries = [
        map_chain.invoke({"context": doc.page_content}) for doc in docs
    ]

    reduce_prompt = ChatPromptTemplate.from_template(
        "Você recebeu resumos parciais de um documento longo.\n"
        "Gere um resumo final em português com:\n"
        "1) visão geral (2-3 frases)\n"
        "2) principais pontos em bullets\n"
        "3) próximos passos sugeridos (opcional)\n\n"
        "Resumos parciais:\n{summaries}"
    )
    reduce_chain = reduce_prompt | llm | parser
    final_summary = reduce_chain.invoke(
        {"summaries": "\n\n".join(partial_summaries)}
    )
    return final_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize a .txt file using LangChain map-reduce."
    )
    parser.add_argument("input_file", type=Path, help="Path to a .txt file")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model name (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=2000,
        help="Characters per chunk (default: 2000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlapping characters between chunks (default: 200)",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    if not args.input_file.exists():
        raise FileNotFoundError(f"File not found: {args.input_file}")

    text = args.input_file.read_text(encoding="utf-8")
    summary = summarize_text(
        text=text,
        model_name=args.model,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(summary)


if __name__ == "__main__":
    main()
