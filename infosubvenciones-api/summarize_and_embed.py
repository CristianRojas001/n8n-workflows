"""
Summarize a single PDF, save the summary as .txt, generate an embedding, and
store it alongside the PDF. Reads OPENAI_API_KEY from environment or .env.

Usage:
  python summarize_and_embed.py --pdf path/to/file.pdf --outdir outputs
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:
    raise SystemExit("Install openai: pip install openai")

try:
    from PyPDF2 import PdfReader  # type: ignore
except ImportError:
    raise SystemExit("Install PyPDF2: pip install PyPDF2")


def load_env_api_key() -> Optional[str]:
    # Try environment first (case-insensitive key lookup)
    for env_key in ("OPENAI_API_KEY", "openai_api_key", "openAI_API_key", "OPENAI_KEY"):
        val = os.getenv(env_key)
        if val:
            return val

    # Fallback: read .env in current project (case-insensitive key)
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip().lower() in {"openai_api_key", "openai_key", "openai", "openai_api"}:
                return v.strip()
    return None


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    chunks = []
    for page in reader.pages:
        text = page.extract_text() or ""
        chunks.append(text)
    return "\n".join(chunks).strip()


def summarize_text(client: OpenAI, text: str, model: str) -> str:
    prompt = (
        "Resume el siguiente texto de una convocatoria de subvención en 6 campos: "
        "objeto, beneficiarios, cuantía, plazos, ámbito geográfico, requisitos/procedimiento. "
        "Responde en español, claro y breve.\n\n"
        f"{text}"
    )
    resp = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=220,
    )
    return resp.output[0].content[0].text


def embed_text(client: OpenAI, text: str, model: str) -> list[float]:
    resp = client.embeddings.create(model=model, input=text)
    return resp.data[0].embedding


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize a PDF and create an embedding (one file)."
    )
    parser.add_argument("--pdf", required=True, help="Path to the PDF to process")
    parser.add_argument(
        "--outdir",
        default="outputs",
        help="Directory to write summary and embedding files",
    )
    parser.add_argument(
        "--summary-model",
        default="gpt-4o-mini",
        help="Model for summarization (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--embed-model",
        default="text-embedding-3-small",
        help="Model for embeddings (default: text-embedding-3-small)",
    )
    args = parser.parse_args()

    api_key = load_env_api_key()
    if not api_key:
        raise SystemExit("OPENAI_API_KEY not found in env or .env")

    client = OpenAI(api_key=api_key)

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting text from {pdf_path.name}...")
    raw_text = extract_text(pdf_path)
    if not raw_text:
        raise SystemExit("No text extracted from PDF (may be scanned/OCR-only).")

    print("Summarizing...")
    summary = summarize_text(client, raw_text, args.summary_model)

    summary_path = outdir / f"{pdf_path.stem}_summary.txt"
    summary_path.write_text(summary, encoding="utf-8")
    print(f"Summary saved to {summary_path}")

    print("Embedding summary...")
    embedding = embed_text(client, summary, args.embed_model)

    embed_path = outdir / f"{pdf_path.stem}_embedding.json"
    embed_path.write_text(
        json.dumps(
            {
                "pdf": str(pdf_path),
                "summary_file": str(summary_path),
                "embedding_model": args.embed_model,
                "embedding": embedding,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Embedding saved to {embed_path}")


if __name__ == "__main__":
    main()
