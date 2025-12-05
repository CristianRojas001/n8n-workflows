"""Text Extraction service - extracts text from PDF files using pymupdf + marker fallback."""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, Tuple, Dict
from loguru import logger
import re


class TextExtractor:
    """
    Extracts text from PDF files with fallback strategies.

    Primary method: PyMuPDF (fitz) - fast, handles most PDFs
    Fallback method: marker-pdf - for scanned/complex PDFs (to be implemented)

    Features:
    - Text extraction with page-by-page processing
    - Image-based PDF detection
    - Metadata extraction (page count, word count)
    - Text cleaning and normalization
    - Markdown output support
    """

    def __init__(self):
        """Initialize text extractor."""
        logger.info("TextExtractor initialized with PyMuPDF")

    def extract_text(
        self,
        pdf_path: str,
        save_markdown: bool = True
    ) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Extract text from a PDF file.

        Args:
            pdf_path: Path to PDF file
            save_markdown: Whether to save extracted text as markdown

        Returns:
            Tuple of (extracted_text, metadata, markdown_path)
            - extracted_text: Full text content
            - metadata: Dict with page_count, word_count, is_scanned, etc.
            - markdown_path: Path to saved markdown file (if save_markdown=True)

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: On extraction errors
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            logger.info(f"Extracting text from: {pdf_path.name}")

            # Try PyMuPDF first (primary method)
            text, metadata = self._extract_with_pymupdf(pdf_path)

            # Check if extraction was successful
            if not text or metadata.get('is_scanned', False):
                logger.warning(
                    f"PyMuPDF extraction failed or PDF is scanned: {pdf_path.name}"
                )
                # TODO: Implement marker-pdf fallback for scanned PDFs
                # text, metadata = self._extract_with_marker(pdf_path)

            # Save as markdown if requested
            markdown_path = None
            if save_markdown and text:
                markdown_path = self._save_as_markdown(pdf_path, text, metadata)

            return text, metadata, markdown_path

        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {e}")
            raise

    def _extract_with_pymupdf(self, pdf_path: Path) -> Tuple[str, Dict]:
        """
        Extract text using PyMuPDF (fitz).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (text, metadata)
        """
        doc = fitz.open(pdf_path)

        pages_text = []
        total_chars = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            pages_text.append(page_text)
            total_chars += len(page_text.strip())

        doc.close()

        # Combine all pages
        full_text = "\n\n".join(pages_text)

        # Clean and normalize text
        full_text = self._clean_text(full_text)

        # Calculate metadata
        word_count = len(full_text.split())
        page_count = len(pages_text)

        # Detect if PDF is likely scanned (very little text per page)
        avg_chars_per_page = total_chars / page_count if page_count > 0 else 0
        is_scanned = avg_chars_per_page < 100  # Less than 100 chars/page suggests scanned

        metadata = {
            'page_count': page_count,
            'word_count': word_count,
            'char_count': len(full_text),
            'avg_chars_per_page': avg_chars_per_page,
            'is_scanned': is_scanned,
            'extraction_method': 'pymupdf'
        }

        logger.info(
            f"Extracted {word_count} words from {page_count} pages "
            f"(scanned: {is_scanned})"
        )

        return full_text, metadata

    def _extract_with_marker(self, pdf_path: Path) -> Tuple[str, Dict]:
        """
        Extract text using marker-pdf (for scanned/complex PDFs).

        TODO: Implement marker-pdf integration
        This is a fallback for scanned PDFs that PyMuPDF can't handle.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (text, metadata)
        """
        logger.warning("Marker-pdf extraction not yet implemented")
        return "", {
            'page_count': 0,
            'word_count': 0,
            'char_count': 0,
            'is_scanned': True,
            'extraction_method': 'marker_not_implemented'
        }

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines -> double newline

        # Remove form feed characters
        text = text.replace('\f', '\n')

        # Remove excessive spaces
        text = re.sub(r' +', ' ', text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    def _save_as_markdown(
        self,
        pdf_path: Path,
        text: str,
        metadata: Dict
    ) -> str:
        """
        Save extracted text as markdown file.

        Args:
            pdf_path: Original PDF path
            text: Extracted text
            metadata: Extraction metadata

        Returns:
            Path to saved markdown file
        """
        # Create markdown directory if it doesn't exist
        md_dir = pdf_path.parent / "markdown"
        md_dir.mkdir(exist_ok=True)

        # Generate markdown filename
        md_filename = pdf_path.stem + ".md"
        md_path = md_dir / md_filename

        # Create markdown content with metadata
        md_content = f"""# {pdf_path.stem}

**Source PDF**: {pdf_path.name}
**Pages**: {metadata.get('page_count', 'N/A')}
**Words**: {metadata.get('word_count', 'N/A')}
**Extraction Method**: {metadata.get('extraction_method', 'N/A')}
**Is Scanned**: {metadata.get('is_scanned', False)}

---

{text}
"""

        # Save to file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.success(f"Saved markdown: {md_path.name}")

        return str(md_path)

    def extract_text_preview(self, pdf_path: str, max_words: int = 500) -> Optional[str]:
        """
        Extract a preview of the text (first N words).

        Args:
            pdf_path: Path to PDF file
            max_words: Maximum number of words to extract

        Returns:
            Preview text or None on error
        """
        try:
            pdf_path = Path(pdf_path)
            doc = fitz.open(pdf_path)

            preview_text = ""
            word_count = 0

            for page_num in range(len(doc)):
                if word_count >= max_words:
                    break

                page = doc[page_num]
                page_text = page.get_text()
                words = page_text.split()

                remaining_words = max_words - word_count
                preview_text += " ".join(words[:remaining_words]) + " "
                word_count += len(words[:remaining_words])

            doc.close()

            return self._clean_text(preview_text)

        except Exception as e:
            logger.error(f"Error extracting preview from {pdf_path}: {e}")
            return None

    def validate_pdf(self, pdf_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a PDF can be opened and processed.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            pdf_path = Path(pdf_path)

            if not pdf_path.exists():
                return False, "File not found"

            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()

            if page_count == 0:
                return False, "PDF has no pages"

            return True, None

        except Exception as e:
            return False, str(e)


# Example usage
if __name__ == "__main__":
    from loguru import logger

    logger.info("Testing TextExtractor...")

    extractor = TextExtractor()

    # Test with a sample PDF (replace with actual path)
    test_pdf = "path/to/test.pdf"

    try:
        # Validate first
        is_valid, error = extractor.validate_pdf(test_pdf)
        if not is_valid:
            logger.error(f"PDF validation failed: {error}")
        else:
            # Extract text
            text, metadata, md_path = extractor.extract_text(test_pdf)

            if text:
                logger.success(f"Extraction successful!")
                logger.info(f"Metadata: {metadata}")
                logger.info(f"Markdown saved to: {md_path}")
                logger.info(f"Preview: {text[:200]}...")
            else:
                logger.warning("No text extracted")

    except FileNotFoundError:
        logger.warning("Test PDF not found - skipping test")
    except Exception as e:
        logger.error(f"Test failed: {e}")
