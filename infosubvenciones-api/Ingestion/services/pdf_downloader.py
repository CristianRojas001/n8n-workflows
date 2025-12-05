"""PDF Downloader service - downloads PDF documents from InfoSubvenciones URLs."""
import os
import hashlib
import requests
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config.settings import Settings


class PDFDownloader:
    """
    Downloads PDF files from grant URLs and stores them locally.

    Features:
    - Downloads PDFs with retry logic
    - Verifies content type (PDF)
    - Generates SHA256 hash for deduplication
    - Saves to configured downloads directory
    - Handles timeouts and connection errors
    """

    def __init__(self, downloads_dir: Optional[str] = None):
        """
        Initialize PDF downloader.

        Args:
            downloads_dir: Directory to save PDFs (defaults to settings)
        """
        self.settings = Settings()
        self.downloads_dir = Path(downloads_dir or self.settings.pdf_downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # HTTP session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InfoSubvenciones-RAG/1.0 (contact: your-email@example.com)'
        })

        logger.info(f"PDFDownloader initialized with downloads_dir: {self.downloads_dir}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError)),
        reraise=True
    )
    def download_pdf(
        self,
        url: str,
        numero_convocatoria: str,
        timeout: int = 30
    ) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """
        Download a PDF from a URL.

        Args:
            url: URL of the PDF document
            numero_convocatoria: Grant ID for filename
            timeout: Request timeout in seconds

        Returns:
            Tuple of (file_path, sha256_hash, file_size_bytes) or (None, None, None) on failure

        Raises:
            requests.exceptions.RequestException: On network/HTTP errors
            ValueError: If URL is invalid or response is not a PDF
        """
        if not url or not url.startswith('http'):
            logger.warning(f"Invalid URL for {numero_convocatoria}: {url}")
            return None, None, None

        try:
            logger.info(f"Downloading PDF for {numero_convocatoria} from {url}")

            # Download with streaming to handle large files
            response = self.session.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            # Verify content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                logger.warning(
                    f"Non-PDF content type for {numero_convocatoria}: {content_type}"
                )
                # Still try to process - some servers return incorrect content types

            # Read content
            content = response.content

            if not content:
                logger.error(f"Empty content for {numero_convocatoria}")
                return None, None, None

            # Verify it's actually a PDF (starts with %PDF)
            if not content.startswith(b'%PDF'):
                logger.error(f"Content is not a valid PDF for {numero_convocatoria}")
                return None, None, None

            # Calculate SHA256 hash
            sha256_hash = hashlib.sha256(content).hexdigest()

            # Generate filename (sanitize numero_convocatoria)
            safe_filename = self._sanitize_filename(numero_convocatoria)
            filename = f"{safe_filename}_{sha256_hash[:8]}.pdf"
            file_path = self.downloads_dir / filename

            # Check if file already exists with same hash
            if file_path.exists():
                existing_size = file_path.stat().st_size
                if existing_size == len(content):
                    logger.info(f"PDF already exists: {filename}")
                    return str(file_path), sha256_hash, len(content)

            # Save to disk
            with open(file_path, 'wb') as f:
                f.write(content)

            file_size = len(content)
            logger.success(
                f"Downloaded PDF for {numero_convocatoria}: "
                f"{filename} ({file_size / 1024:.1f} KB)"
            )

            return str(file_path), sha256_hash, file_size

        except requests.exceptions.Timeout:
            logger.error(f"Timeout downloading PDF for {numero_convocatoria}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {numero_convocatoria}: {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {numero_convocatoria}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF for {numero_convocatoria}: {e}")
            return None, None, None

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove/replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length]

        return filename

    def get_file_path(self, numero_convocatoria: str, hash_prefix: str = None) -> Optional[Path]:
        """
        Get the file path for a downloaded PDF.

        Args:
            numero_convocatoria: Grant ID
            hash_prefix: Optional hash prefix to find specific file

        Returns:
            Path to PDF file if exists, None otherwise
        """
        safe_filename = self._sanitize_filename(numero_convocatoria)

        if hash_prefix:
            filename = f"{safe_filename}_{hash_prefix}.pdf"
            file_path = self.downloads_dir / filename
            if file_path.exists():
                return file_path

        # Search for any file matching the numero_convocatoria
        pattern = f"{safe_filename}_*.pdf"
        matches = list(self.downloads_dir.glob(pattern))

        if matches:
            # Return the most recent one
            return max(matches, key=lambda p: p.stat().st_mtime)

        return None

    def verify_pdf(self, file_path: str) -> bool:
        """
        Verify that a file is a valid PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
        except Exception as e:
            logger.error(f"Error verifying PDF {file_path}: {e}")
            return False

    def get_download_stats(self) -> dict:
        """
        Get statistics about downloaded PDFs.

        Returns:
            Dictionary with stats (count, total_size, etc.)
        """
        pdf_files = list(self.downloads_dir.glob("*.pdf"))

        total_size = sum(f.stat().st_size for f in pdf_files)

        return {
            'total_count': len(pdf_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'downloads_dir': str(self.downloads_dir)
        }

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    from loguru import logger

    logger.info("Testing PDFDownloader...")

    with PDFDownloader() as downloader:
        # Test URL (example - replace with real URL)
        test_url = "https://example.com/convocatoria.pdf"
        test_numero = "TEST-001"

        try:
            file_path, hash_val, size = downloader.download_pdf(test_url, test_numero)
            if file_path:
                logger.success(f"Downloaded: {file_path}")
                logger.info(f"Hash: {hash_val}")
                logger.info(f"Size: {size} bytes")
        except Exception as e:
            logger.error(f"Download failed: {e}")

        # Get stats
        stats = downloader.get_download_stats()
        logger.info(f"Download stats: {stats}")
