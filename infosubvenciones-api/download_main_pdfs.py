# -*- coding: utf-8 -*-
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://www.infosubvenciones.es/bdnstrans/api"
SEARCH_FILTERS = [
    {"finalidad": "11", "tiposBeneficiario": "3,2", "abierto": "true"},
    {"finalidad": "14", "tiposBeneficiario": "3,2", "abierto": "true"},
]
PAGE_SIZE = 100
DEFAULT_MAX = 1000
KEYWORDS = (
    "convoc",
    "bases",
    "anexo",
    "extracto",
    "resol",
    "ayuda",
    "subvencion",
)


def fetch_json(path: str, params=None, retries: int = 3, delay: float = 1.0):
    params = params or {}
    qs = urllib.parse.urlencode(params, doseq=True)
    url = f"{BASE}/{path}"
    if qs:
        url = f"{url}?{qs}"
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url) as r:
                return json.load(r)
        except Exception as exc:  # pragma: no cover - networking
            last_err = exc
            time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {last_err}")


def fetch_blob(path: str, params=None):
    params = params or {}
    qs = urllib.parse.urlencode(params, doseq=True)
    url = f"{BASE}/{path}"
    if qs:
        url = f"{url}?{qs}"
    with urllib.request.urlopen(url) as r:
        return r.read()


def sanitize_filename(name: str) -> str:
    cleaned = name.replace("/", "_").replace("\\", "_")
    return "".join(ch if ch not in '<>:"|?*' else "_" for ch in cleaned)


def pick_main_document(docs):
    if not docs:
        return None
    scored = []
    for doc in docs:
        name = str(doc.get("nombreFic") or "").strip()
        desc = str(doc.get("descripcion") or "").strip()
        text = f"{name} {desc}".lower()
        if "detalle" in text:
            continue
        if not name.lower().endswith(".pdf"):
            continue
        score = 0
        if any(k in text for k in KEYWORDS):
            score += 2
        score += 1  # baseline for a non-detalle PDF
        scored.append((score, doc))
    if scored:
        scored.sort(key=lambda item: (-item[0], -int(item[1].get("idDocumento", item[1].get("id", 0)))))
        return scored[0][1]
    for doc in docs:
        name = str(doc.get("nombreFic") or "").strip().lower()
        if name.endswith(".pdf"):
            return doc
    return None


def download_convocatoria(conv, outdir: Path, overwrite: bool = False):
    num_conv = conv.get("numeroConvocatoria")
    detalle = fetch_json("convocatorias", {"numConv": num_conv})
    doc = pick_main_document(detalle.get("documentos", []))
    if not doc:
        return None
    doc_id = doc.get("idDocumento") or doc.get("id")
    if not doc_id:
        return None
    name = sanitize_filename(f"{num_conv}_{doc_id}_{doc.get('nombreFic', 'doc.pdf')}")
    target = outdir / name
    if target.exists() and not overwrite:
        return {
            "numeroConvocatoria": num_conv,
            "id": detalle.get("id"),
            "pdf_file": str(target),
            "skipped": "exists",
        }
    blob = fetch_blob("convocatorias/documentos", {"idDocumento": doc_id})
    target.write_bytes(blob)
    return {
        "numeroConvocatoria": num_conv,
        "id": detalle.get("id"),
        "descripcion": detalle.get("descripcion"),
        "fechaRecepcion": detalle.get("fechaRecepcion"),
        "fechaInicioSolicitud": detalle.get("fechaInicioSolicitud"),
        "fechaFinSolicitud": detalle.get("fechaFinSolicitud"),
        "nivel1": detalle.get("nivel1"),
        "nivel2": detalle.get("nivel2"),
        "categoria": conv.get("categoria") or conv.get("finalidad"),
        "pdf_file": str(target.name),
        "doc_nombre": doc.get("nombreFic"),
        "doc_descripcion": doc.get("descripcion"),
    }


def iter_convocatorias(limit: int):
    remaining = limit
    for filt in SEARCH_FILTERS:
        page = 0
        while remaining > 0:
            payload = dict(filt)
            payload.update({"page": page, "size": PAGE_SIZE})
            data = fetch_json("convocatorias/busqueda", payload)
            content = data.get("content", [])
            if not content:
                break
            for conv in content:
                if remaining <= 0:
                    break
                yield conv
                remaining -= 1
            page += 1
            if (page * PAGE_SIZE) >= data.get("totalElements", 0):
                break


def main():
    parser = argparse.ArgumentParser(description="Download main PDFs (not detalle) for convocatorias")
    parser.add_argument("--out", default="relevant_pdfs", help="Output directory for PDFs")
    parser.add_argument("--max", type=int, default=DEFAULT_MAX, help="Max PDFs to download")
    parser.add_argument("--overwrite", action="store_true", help="Re-download existing files")
    args = parser.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    results = []
    downloaded = 0
    for conv in iter_convocatorias(args.max):
        meta = download_convocatoria(conv, outdir, overwrite=args.overwrite)
        if meta:
            results.append(meta)
            if meta.get("skipped") == "exists":
                print(f"[skip] {meta['numeroConvocatoria']} already exists -> {meta['pdf_file']}")
            else:
                downloaded += 1
                print(f"[{downloaded}] saved {meta['numeroConvocatoria']} -> {meta['pdf_file']}")
        else:
            print(f"[miss] {conv.get('numeroConvocatoria')} without suitable PDF")
        if downloaded >= args.max:
            break

    meta_path = outdir / "metadata_main_pdfs.json"
    meta_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done. Downloaded {downloaded} PDFs. Metadata in {meta_path}")


if __name__ == "__main__":
    main()
