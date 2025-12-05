"""InfoSubvenciones API client with retry logic and pagination support."""
import sys
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from schemas.api_response import (
    ConvocatoriaSearchResponse,
    ConvocatoriaDetail,
    ConvocatoriaSearchItem
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InfoSubvencionesAPIError(Exception):
    """Custom exception for API errors."""
    pass


class InfoSubvencionesClient:
    """
    Client for InfoSubvenciones API with automatic retry logic.

    Features:
    - Pagination support (100 items/page)
    - Exponential backoff retry (max 3 attempts)
    - Rate limiting handling (429 errors)
    - Timeout handling
    - Response validation with Pydantic
    """

    BASE_URL = "https://www.infosubvenciones.es/bdnstrans/api"
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_PAGE_SIZE = 100

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        base_url: Optional[str] = None
    ):
        """
        Initialize API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            base_url: Override base URL (for testing)
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'InfoSubvenciones-Ingestion/1.0',
            'Accept': 'application/json'
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Make HTTP request with automatic retry.

        Args:
            endpoint: API endpoint (e.g., "convocatorias/busqueda")
            params: Query parameters
            method: HTTP method

        Returns:
            JSON response as dict

        Raises:
            InfoSubvencionesAPIError: On API errors or validation failures
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(endpoint, params, method)

            # Raise for HTTP errors
            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout for {url}: {e}")
            raise

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            raise InfoSubvencionesAPIError(f"HTTP {response.status_code}: {str(e)}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise InfoSubvencionesAPIError(f"Request failed: {str(e)}")

        except ValueError as e:
            logger.error(f"Invalid JSON response from {url}: {e}")
            raise InfoSubvencionesAPIError(f"Invalid JSON: {str(e)}")

    def search_convocatorias(
        self,
        finalidad: Optional[str] = None,
        tipos_beneficiario: Optional[str] = None,
        abierto: Optional[bool] = None,
        page: int = 0,
        size: int = DEFAULT_PAGE_SIZE,
        **kwargs
    ) -> ConvocatoriaSearchResponse:
        """
        Search for convocatorias with filters.

        Args:
            finalidad: Purpose code (e.g., "11" for culture, "14" for research)
            tipos_beneficiario: Beneficiary types (e.g., "3,2" for companies+individuals)
            abierto: Filter by open status
            page: Page number (0-indexed)
            size: Page size (max 100)
            **kwargs: Additional search parameters

        Returns:
            ConvocatoriaSearchResponse with paginated results

        Example:
            response = client.search_convocatorias(finalidad="11", abierto=True, page=0)
            for item in response.content:
                print(item.numeroConvocatoria, item.titulo)
        """
        params = {
            "page": page,
            "size": min(size, 100)  # API max is 100
        }

        if finalidad:
            params["finalidad"] = finalidad
        if tipos_beneficiario:
            params["tiposBeneficiario"] = tipos_beneficiario
        if abierto is not None:
            params["abierto"] = "true" if abierto else "false"

        # Add any additional parameters
        params.update(kwargs)

        data = self._make_request("convocatorias/busqueda", params)

        try:
            return ConvocatoriaSearchResponse(**data)
        except Exception as e:
            logger.error(f"Failed to parse search response: {e}")
            raise InfoSubvencionesAPIError(f"Response validation failed: {str(e)}")

    def get_convocatoria_detail(self, numero_convocatoria: str) -> ConvocatoriaDetail:
        """
        Get detailed information for a specific convocatoria.

        Args:
            numero_convocatoria: Convocatoria number (e.g., "871838")

        Returns:
            ConvocatoriaDetail with full metadata including documents

        Example:
            detail = client.get_convocatoria_detail("871838")
            print(detail.titulo)
            print(f"Documents: {len(detail.documentos)}")
        """
        params = {"numConv": numero_convocatoria}
        data = self._make_request("convocatorias", params)

        # Ensure numeroConvocatoria is in the response
        if 'numeroConvocatoria' not in data and numero_convocatoria:
            data['numeroConvocatoria'] = numero_convocatoria

        try:
            return ConvocatoriaDetail(**data)
        except Exception as e:
            logger.error(f"Failed to parse detail response for {numero_convocatoria}: {e}")
            raise InfoSubvencionesAPIError(f"Response validation failed: {str(e)}")

    def download_document(self, documento_id: int) -> bytes:
        """
        Download a PDF document by ID.

        Args:
            documento_id: Document ID from documentos array

        Returns:
            PDF content as bytes

        Example:
            pdf_bytes = client.download_document(1362058)
            with open("grant.pdf", "wb") as f:
                f.write(pdf_bytes)
        """
        params = {"idDocumento": documento_id}
        url = f"{self.base_url}/convocatorias/documentos"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            if response.headers.get('Content-Type', '').startswith('application/pdf'):
                return response.content
            else:
                raise InfoSubvencionesAPIError(
                    f"Expected PDF but got {response.headers.get('Content-Type')}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download document {documento_id}: {e}")
            raise InfoSubvencionesAPIError(f"Download failed: {str(e)}")

    def iter_all_convocatorias(
        self,
        finalidad: Optional[str] = None,
        tipos_beneficiario: Optional[str] = None,
        abierto: Optional[bool] = None,
        max_items: Optional[int] = None,
        **kwargs
    ):
        """
        Generator to iterate through all convocatorias with automatic pagination.

        Args:
            finalidad: Purpose code filter
            tipos_beneficiario: Beneficiary types filter
            abierto: Open status filter
            max_items: Maximum number of items to fetch (None = all)
            **kwargs: Additional search parameters

        Yields:
            ConvocatoriaSearchItem objects

        Example:
            # Fetch first 1000 culture grants
            for conv in client.iter_all_convocatorias(finalidad="11", max_items=1000):
                print(conv.numeroConvocatoria, conv.titulo)
        """
        page = 0
        fetched = 0

        while True:
            # Fetch page
            response = self.search_convocatorias(
                finalidad=finalidad,
                tipos_beneficiario=tipos_beneficiario,
                abierto=abierto,
                page=page,
                **kwargs
            )

            if not response.content:
                break

            # Yield items
            for item in response.content:
                yield item
                fetched += 1

                if max_items and fetched >= max_items:
                    return

            # Check if more pages exist
            if page >= response.totalPages - 1:
                break

            page += 1
            logger.info(f"Fetched {fetched} items, moving to page {page + 1}/{response.totalPages}")

    def get_statistics(
        self,
        finalidad: Optional[str] = None,
        tipos_beneficiario: Optional[str] = None,
        abierto: Optional[bool] = None
    ) -> Dict[str, int]:
        """
        Get count statistics for given filters.

        Args:
            finalidad: Purpose code filter
            tipos_beneficiario: Beneficiary types filter
            abierto: Open status filter

        Returns:
            Dict with totalElements, totalPages, etc.
        """
        response = self.search_convocatorias(
            finalidad=finalidad,
            tipos_beneficiario=tipos_beneficiario,
            abierto=abierto,
            page=0,
            size=1  # Minimal fetch
        )

        return {
            "totalElements": response.totalElements,
            "totalPages": response.totalPages,
            "estimatedItems": response.totalElements
        }

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
