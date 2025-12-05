"""Simple test for PDF processing with a real URL."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from services.pdf_downloader import PDFDownloader
from services.text_extractor import TextExtractor


def test_download_and_extract():
    """Test downloading and extracting a real PDF."""

    # Real PDF URL retrieved from InfoSubvenciones API on 2025-12-02
    test_url = (
        "https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos"
        "?idDocumento=1362960"
    )
    test_numero = "872189"

    logger.info("=" * 80)
    logger.info("Simple PDF Processing Test")
    logger.info("=" * 80)

    # Test 1: PDF Downloader
    logger.info("\n--- Test 1: PDF Download ---")
    logger.info(f"URL: {test_url}")

    try:
        with PDFDownloader() as downloader:
            file_path, pdf_hash, file_size = downloader.download_pdf(test_url, test_numero)

            if file_path:
                logger.success(f"Download successful!")
                logger.info(f"File path: {file_path}")
                logger.info(f"PDF hash: {pdf_hash}")
                logger.info(f"File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")

                # Test 2: Text Extraction
                logger.info("\n--- Test 2: Text Extraction ---")

                extractor = TextExtractor()

                # Validate PDF first
                is_valid, error = extractor.validate_pdf(file_path)

                if not is_valid:
                    logger.error(f"PDF validation failed: {error}")
                    return

                logger.success("PDF is valid")

                # Extract text
                text, metadata, md_path = extractor.extract_text(file_path, save_markdown=True)

                if text:
                    logger.success("Text extraction successful!")
                    logger.info(f"Page count: {metadata.get('page_count')}")
                    logger.info(f"Word count: {metadata.get('word_count')}")
                    logger.info(f"Char count: {metadata.get('char_count')}")
                    logger.info(f"Is scanned: {metadata.get('is_scanned')}")
                    logger.info(f"Markdown saved to: {md_path}")
                    logger.info(f"\nFirst 500 characters:\n{text[:500]}...")
                else:
                    logger.warning("No text extracted (possibly scanned PDF)")
                    logger.info(f"Metadata: {metadata}")

            else:
                logger.error("Download failed")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("\n" + "=" * 80)
    logger.info("Test completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    logger.info("NOTE: This test uses a placeholder URL.")
    logger.info("To test with real data, provide a real PDF URL from InfoSubvenciones.\n")

    test_download_and_extract()
