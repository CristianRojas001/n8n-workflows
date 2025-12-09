"""
Fetcher Task - Fetch convocatorias from InfoSubvenciones API

This task fetches grant data from the InfoSubvenciones API and stores it in:
1. staging_items table (for progress tracking)
2. convocatorias table (actual grant metadata)

The fetcher is the first stage in the pipeline:
fetcher -> processor (Week 2) -> embedder (Week 2-3)
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from config.celery_app import app
from config.database import get_db
from models.staging import StagingItem, ProcessingStatus
from models.convocatoria import Convocatoria
from services.api_client import InfoSubvencionesClient, InfoSubvencionesAPIError
from schemas.api_response import ConvocatoriaDetail

# Set up logging
logger = logging.getLogger(__name__)


def _hash_pdf_url(pdf_url: Optional[str]) -> Optional[str]:
    """Generate SHA256 hash of PDF URL for duplicate detection."""
    if not pdf_url:
        return None
    return hashlib.sha256(pdf_url.encode('utf-8')).hexdigest()


def _extract_pdf_info(detail: ConvocatoriaDetail) -> Dict[str, Any]:
    """
    Extract PDF information from convocatoria detail.

    Returns dict with: tiene_pdf, pdf_url, pdf_nombre, pdf_id_documento, pdf_hash
    """
    pdf_info = {
        'tiene_pdf': False,
        'pdf_url': None,
        'pdf_nombre': None,
        'pdf_id_documento': None,
        'pdf_hash': None
    }

    # Check if documentos exists and is not empty
    if not detail.documentos or len(detail.documentos) == 0:
        return pdf_info

    # Find the first PDF document (usually "Convocatoria completa" or similar)
    for doc in detail.documentos:
        # Check if document has a URL and looks like a PDF
        url = doc.urlDocumento if hasattr(doc, 'urlDocumento') else None
        nombre = doc.nombreDocumento if hasattr(doc, 'nombreDocumento') else None
        id_doc = doc.idDocumento if hasattr(doc, 'idDocumento') else None

        if url and (url.lower().endswith('.pdf') or 'pdf' in url.lower()):
            pdf_info['tiene_pdf'] = True
            pdf_info['pdf_url'] = url
            pdf_info['pdf_nombre'] = nombre
            pdf_info['pdf_id_documento'] = str(id_doc) if id_doc else None
            pdf_info['pdf_hash'] = _hash_pdf_url(url)
            break

    return pdf_info


def _convert_detail_to_convocatoria(detail: ConvocatoriaDetail, batch_id: Optional[str]) -> Convocatoria:
    """
    Convert API ConvocatoriaDetail to Convocatoria database model.

    Args:
        detail: Pydantic model from API
        batch_id: Batch identifier for this fetch operation

    Returns:
        Convocatoria model ready for database insertion
    """
    # Extract PDF info
    pdf_info = _extract_pdf_info(detail)

    # Convert dates (handle None values)
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    # Create Convocatoria model
    convocatoria = Convocatoria(
        # Identification
        numero_convocatoria=detail.numeroConvocatoria,
        codigo=detail.codigo,
        titulo=detail.titulo,
        descripcion=detail.descripcion,
        objeto=detail.objeto,

        # Administrative
        organismo=detail.organismo,
        organismo_id=detail.organismoId,
        departamento=detail.departamento,
        tipo_administracion=detail.tipoAdministracion,
        nivel_administracion=detail.nivelAdministracion,

        # Classification
        finalidad=str(detail.finalidad) if detail.finalidad else None,
        finalidad_descripcion=detail.finalidadDescripcion,
        sectores=detail.sectores if detail.sectores else [],
        regiones=detail.regiones if detail.regiones else [],
        ambito=detail.ambito,

        # Beneficiaries
        tipos_beneficiario=detail.tiposBeneficiario if detail.tiposBeneficiario else [],
        beneficiarios_descripcion=detail.beneficiariosDescripcion,
        requisitos_beneficiarios=detail.requisitosBeneficiarios,

        # Dates
        fecha_publicacion=parse_date(detail.fechaPublicacion),
        fecha_inicio_solicitud=parse_date(detail.fechaInicioSolicitud),
        fecha_fin_solicitud=parse_date(detail.fechaFinSolicitud),
        fecha_resolucion=parse_date(detail.fechaResolucion),
        abierto=detail.abierto if detail.abierto is not None else False,

        # Amounts
        importe_total=detail.importeTotal,
        importe_minimo=detail.importeMinimo,
        importe_maximo=detail.importeMaximo,
        porcentaje_financiacion=detail.porcentajeFinanciacion,

        # Application
        forma_solicitud=detail.formaSolicitud,
        lugar_presentacion=detail.lugarPresentacion,
        tramite_electronico=detail.tramiteElectronico if detail.tramiteElectronico is not None else False,
        url_tramite=detail.urlTramite,

        # Documents (store raw documentos as JSONB)
        documentos=[doc.model_dump() for doc in detail.documentos] if detail.documentos else [],
        tiene_pdf=pdf_info['tiene_pdf'],
        pdf_url=pdf_info['pdf_url'],
        pdf_nombre=pdf_info['pdf_nombre'],
        pdf_id_documento=pdf_info['pdf_id_documento'],
        pdf_hash=pdf_info['pdf_hash'],

        # Additional info
        bases_reguladoras=detail.basesReguladoras,
        normativa=[norm.model_dump() for norm in detail.normativa] if detail.normativa else [],
        compatibilidades=detail.compatibilidades,
        contacto=detail.contacto.model_dump() if detail.contacto else None,
        observaciones=detail.observaciones,

        # Raw data (for debugging)
        raw_api_response=detail.model_dump(),

        # Metadata
        fuente='infosubvenciones'
    )

    return convocatoria


@app.task(bind=True, name='tasks.fetcher.fetch_convocatorias', max_retries=3)
def fetch_convocatorias(
    self,
    finalidad: str,
    batch_id: str,
    page: int = 0,
    size: int = 100,
    max_items: Optional[int] = None,
    abierto: bool = True
) -> Dict[str, Any]:
    """
    Fetch convocatorias from InfoSubvenciones API and store in database.

    This task:
    1. Fetches convocatorias from API (with pagination)
    2. For each convocatoria, fetches detailed info
    3. Inserts into staging_items (status='pending')
    4. Inserts into convocatorias table
    5. Handles duplicates (skip if already exists)

    Args:
        finalidad: Purpose code (e.g., "11" for culture)
        batch_id: Batch identifier (e.g., "culture_2025-12-05")
        page: Starting page number (0-indexed)
        size: Page size (max 100)
        max_items: Maximum number of items to fetch (None = all)
        abierto: Filter for open grants only (default: True)

    Returns:
        Dict with stats: {fetched, inserted, duplicates, errors}

    Example:
        # Fetch first 100 open culture grants
        result = fetch_convocatorias.delay("11", "culture_batch_1", page=0, size=100)

        # Fetch all grants (open and closed)
        result = fetch_convocatorias.delay("11", "culture_batch_1", abierto=False)

        # Fetch specific number
        result = fetch_convocatorias.delay("11", "culture_batch_1", max_items=10)
    """
    logger.info(f"[Task {self.request.id}] Starting fetch: finalidad={finalidad}, batch={batch_id}, page={page}")

    stats = {
        'fetched': 0,
        'inserted': 0,
        'duplicates': 0,
        'errors': 0,
        'batch_id': batch_id,
        'finalidad': finalidad
    }

    # Initialize API client and database session
    client = InfoSubvencionesClient()
    db: Session = next(get_db())

    try:
        # Search for convocatorias
        logger.info(f"Searching convocatorias: finalidad={finalidad}, page={page}, size={size}, abierto={abierto}")
        response = client.search_convocatorias(
            finalidad=finalidad,
            page=page,
            size=size,
            abierto=abierto
        )

        logger.info(f"Found {response.totalElements} total elements, processing page {page + 1}/{response.totalPages}")

        # Process each convocatoria in the search results
        items_to_process = response.content[:max_items] if max_items else response.content

        for item in items_to_process:
            numero = item.numeroConvocatoria
            stats['fetched'] += 1

            try:
                # Check if already exists in staging (skip duplicates)
                existing_staging = db.query(StagingItem).filter_by(
                    numero_convocatoria=numero
                ).first()

                if existing_staging:
                    logger.debug(f"Skipping duplicate: {numero} (already in staging)")
                    stats['duplicates'] += 1
                    continue

                # Fetch detailed information
                logger.debug(f"Fetching detail for: {numero}")
                detail = client.get_convocatoria_detail(numero)

                # Convert to database model
                convocatoria = _convert_detail_to_convocatoria(detail, batch_id)

                # Check if convocatoria already exists (by numero_convocatoria)
                existing_conv = db.query(Convocatoria).filter_by(
                    numero_convocatoria=numero
                ).first()

                if existing_conv:
                    logger.debug(f"Convocatoria {numero} already exists, updating...")
                    # Update existing record with new data
                    for key, value in convocatoria.__dict__.items():
                        if key not in ['_sa_instance_state', 'id', 'created_at']:
                            setattr(existing_conv, key, value)
                    db.flush()
                else:
                    # Insert new convocatoria
                    db.add(convocatoria)
                    db.flush()

                # Create staging item
                staging_item = StagingItem(
                    numero_convocatoria=numero,
                    status=ProcessingStatus.PENDING,
                    batch_id=batch_id,
                    last_stage='fetcher',
                    retry_count=0
                )
                db.add(staging_item)
                db.commit()

                stats['inserted'] += 1
                logger.debug(f"Inserted: {numero} - {detail.titulo[:50] if detail.titulo else 'N/A'}")

            except IntegrityError as e:
                db.rollback()
                logger.warning(f"Duplicate detected for {numero}: {e}")
                stats['duplicates'] += 1

            except Exception as e:
                db.rollback()
                logger.error(f"Error processing {numero}: {e}", exc_info=True)
                stats['errors'] += 1

                # Create staging item with failed status
                try:
                    staging_item = StagingItem(
                        numero_convocatoria=numero,
                        status=ProcessingStatus.FAILED,
                        batch_id=batch_id,
                        last_stage='fetcher',
                        retry_count=0,
                        error_message=str(e)
                    )
                    db.add(staging_item)
                    db.commit()
                except Exception as inner_e:
                    logger.error(f"Failed to create staging item for {numero}: {inner_e}")
                    db.rollback()

        logger.info(f"[Task {self.request.id}] Completed: {stats}")
        return stats

    except InfoSubvencionesAPIError as e:
        logger.error(f"API error: {e}")
        stats['errors'] += 1
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        stats['errors'] += 1
        raise

    finally:
        db.close()
        client.session.close()


@app.task(name='tasks.fetcher.fetch_batch')
def fetch_batch(
    finalidad: str,
    batch_id: str,
    total_items: int,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Fetch a large batch of convocatorias by spawning multiple fetcher tasks.

    This is a coordinator task that splits a large fetch operation into
    multiple smaller tasks (one per page).

    Args:
        finalidad: Purpose code
        batch_id: Batch identifier
        total_items: Total number of items to fetch
        batch_size: Items per page (max 100)

    Returns:
        Dict with overall stats

    Example:
        # Fetch 1000 culture grants
        fetch_batch.delay("11", "culture_batch_1", total_items=1000)
    """
    logger.info(f"Starting batch fetch: {total_items} items, batch_size={batch_size}")

    total_pages = (total_items + batch_size - 1) // batch_size  # Ceiling division

    # Spawn fetcher tasks for each page
    tasks = []
    for page in range(total_pages):
        task = fetch_convocatorias.delay(
            finalidad=finalidad,
            batch_id=batch_id,
            page=page,
            size=batch_size
        )
        tasks.append(task)

    logger.info(f"Spawned {len(tasks)} fetcher tasks for batch {batch_id}")

    return {
        'batch_id': batch_id,
        'total_pages': total_pages,
        'tasks_spawned': len(tasks),
        'task_ids': [task.id for task in tasks]
    }
