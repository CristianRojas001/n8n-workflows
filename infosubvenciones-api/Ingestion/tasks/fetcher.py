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
import json
import re
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


def _normalize_beneficiarios(raw_list: Optional[List[str]], raw_objs: Optional[List[Dict[str, Any]]]) -> List[str]:
    """Map beneficiary descriptions to a controlled set of buckets."""
    buckets = set()
    candidates: List[str] = []
    if raw_list:
        candidates.extend([c for c in raw_list if c])
    if raw_objs:
        for obj in raw_objs:
            if isinstance(obj, dict):
                val = obj.get('descripcion') or obj.get('nombre') or obj.get('tipo')
                if val:
                    candidates.append(val)

    for val in candidates:
        text = val.lower()
        if any(k in text for k in ['autónomo', 'autonom', 'persona física que desarrolla']):
            buckets.add('Autonomo')
        if any(k in text for k in ['pyme', 'pymes', 'microempresa', 'empresa', 'sociedad']):
            buckets.add('Empresa')
        if 'gran empresa' in text:
            buckets.add('Empresa')
        if any(k in text for k in ['ayuntamiento', 'diputación', 'diputacion', 'cabildo', 'consell', 'entidad local', 'corporación local', 'corporacion local', 'municip', 'comarca']):
            buckets.add('Entidad local')
        if any(k in text for k in ['fundación', 'fundacion', 'asociación', 'asociacion', 'ong', 'sin ánimo de lucro', 'sin animo de lucro']):
            buckets.add('ONG')
        if any(k in text for k in ['universidad', 'centro universit', 'campus']):
            buckets.add('Universidad')
        if 'cooperativa' in text:
            buckets.add('Cooperativa')
        if any(k in text for k in ['organismo', 'ente público', 'ente publico', 'empresa pública', 'empresa publica']):
            buckets.add('Organismo público')

    return sorted(buckets)


def _normalize_sectores(sectores: Optional[List[str]], sectores_productos: Optional[List[Any]]) -> List[str]:
    """Choose the best available sector labels (API first, then productos)."""
    out: List[str] = []
    if sectores:
        out.extend([s for s in sectores if s])
    elif sectores_productos:
        for item in sectores_productos:
            if isinstance(item, dict):
                val = item.get('descripcion') or item.get('nombre') or item.get('codigo')
                if val:
                    out.append(val)
            elif isinstance(item, str):
                out.append(item)
    # Deduplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            deduped.append(s)
    return deduped


def _parse_region_codes(regiones: Optional[List[str]]) -> List[str]:
    """Extract NUTS codes from strings like 'ES51 - CATALUÑA'."""
    codes: List[str] = []
    if not regiones:
        return codes
    for reg in regiones:
        if not reg:
            continue
        if isinstance(reg, str) and ' - ' in reg:
            code = reg.split(' - ', 1)[0].strip()
            if code:
                codes.append(code)
        elif isinstance(reg, str) and re.match(r'^[A-Z]{2,3}\\d+', reg):
            codes.append(reg.strip())
    # Deduplicate
    seen = set()
    deduped: List[str] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    return deduped


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
    base_url = getattr(InfoSubvencionesClient, "BASE_URL", "https://www.infosubvenciones.es/bdnstrans/api")

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
        def _get_field(obj, key):
            if hasattr(obj, key):
                return getattr(obj, key)
            if isinstance(obj, dict):
                return obj.get(key)
            return None

        # Prefer explicit download URLs; fall back to any URL-like field
        url = _get_field(doc, 'urlDocumento') or _get_field(doc, 'urlDescarga')
        nombre = _get_field(doc, 'nombreDocumento') or _get_field(doc, 'nombreFic')
        id_doc = _get_field(doc, 'idDocumento') or _get_field(doc, 'id')

        # If API didn't give a URL but gave an id, synthesize the download endpoint
        if not url and id_doc:
            url = f"{base_url}/convocatorias/documentos?idDocumento={id_doc}"

        if url and (url.lower().endswith('.pdf') or 'pdf' in url.lower()):
            pdf_info['tiene_pdf'] = True
            pdf_info['pdf_url'] = url
            pdf_info['pdf_nombre'] = nombre
            pdf_info['pdf_id_documento'] = str(id_doc) if id_doc else None
            pdf_info['pdf_hash'] = _hash_pdf_url(url)
            break

    # Fallback: build convocatoria-level PDF endpoint if no document URL found
    if not pdf_info['pdf_url'] and detail.id:
        fallback_url = f"{base_url}/convocatorias/pdf?id={detail.id}&vpd=GE"
        pdf_info['tiene_pdf'] = True
        pdf_info['pdf_url'] = fallback_url
        pdf_info['pdf_id_documento'] = str(detail.id)
        pdf_info['pdf_hash'] = _hash_pdf_url(fallback_url)

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

    # Normalize organo and administrative hierarchy
    organo_obj = getattr(detail, 'organo', None)
    if hasattr(organo_obj, 'model_dump'):
        organo_obj = organo_obj.model_dump()

    nivel1_val = getattr(detail, 'nivel1', None) or (organo_obj.get('nivel1') if isinstance(organo_obj, dict) else None)
    nivel2_val = getattr(detail, 'nivel2', None) or (organo_obj.get('nivel2') if isinstance(organo_obj, dict) else None)
    nivel3_val = (organo_obj.get('nivel3') if isinstance(organo_obj, dict) else None)

    admin_path_parts = [p for p in [nivel1_val, nivel2_val, nivel3_val] if p]
    admin_path_normalized = " > ".join(admin_path_parts).lower() if admin_path_parts else None

    administracion = None
    if organo_obj or admin_path_parts:
        administracion = {
            'nivel1': nivel1_val,
            'nivel2': nivel2_val,
            'nivel3': nivel3_val,
            'organo': organo_obj
        }

    # Normalize beneficiaries/sectors/regions
    beneficiaries_norm = _normalize_beneficiarios(detail.tiposBeneficiario, getattr(detail, 'tiposBeneficiarios', None))
    sectores_norm = _normalize_sectores(detail.sectores, getattr(detail, 'sectoresProductos', None))
    region_codes = _parse_region_codes(detail.regiones if detail.regiones else [])

    # Dates
    fecha_publicacion = parse_date(detail.fechaPublicacion or getattr(detail, 'fechaRecepcion', None))
    fecha_inicio = parse_date(detail.fechaInicioSolicitud)
    fecha_fin = parse_date(detail.fechaFinSolicitud)
    fecha_resolucion = parse_date(detail.fechaResolucion)

    # Derived: is open now?
    is_open_now = None
    try:
        today = datetime.utcnow().date()
        if fecha_inicio and fecha_fin:
            is_open_now = (fecha_inicio.date() <= today <= fecha_fin.date())
        elif fecha_inicio and not fecha_fin:
            is_open_now = (fecha_inicio.date() <= today)
        elif fecha_fin and not fecha_inicio:
            is_open_now = (today <= fecha_fin.date())
    except Exception:
        is_open_now = None

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
        sectores=detail.sectores if detail.sectores else (detail.sectoresProductos if hasattr(detail, 'sectoresProductos') and detail.sectoresProductos else []),
        regiones=detail.regiones if detail.regiones else [],
        sectores_normalizados=sectores_norm,
        region_nuts=region_codes,
        ambito=detail.ambito,

        # Beneficiaries
        tipos_beneficiario=detail.tiposBeneficiario if detail.tiposBeneficiario else [],
        beneficiarios_descripcion=detail.beneficiariosDescripcion,
        requisitos_beneficiarios=detail.requisitosBeneficiarios,
        beneficiarios_normalizados=beneficiaries_norm,

        # Dates
        # Fallback: use fechaRecepcion when fechaPublicacion is missing
        fecha_publicacion=fecha_publicacion,
        fecha_inicio_solicitud=fecha_inicio,
        fecha_fin_solicitud=fecha_fin,
        fecha_resolucion=fecha_resolucion,
        abierto=detail.abierto if detail.abierto is not None else False,
        is_open_now=is_open_now,

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

        # Extra API fields
        mrr=detail.mrr if hasattr(detail, 'mrr') else None,
        fondos=detail.fondos if hasattr(detail, 'fondos') else [],
        nivel1=nivel1_val,
        nivel2=nivel2_val,
        organo=organo_obj if hasattr(detail, 'organo') else None,
        administracion=administracion,
        admin_path_normalized=admin_path_normalized,
        text_inicio=getattr(detail, 'textInicio', None),
        text_fin=getattr(detail, 'textFin', None),
        anuncios=detail.anuncios if hasattr(detail, 'anuncios') else [],
        objetivos=detail.objetivos if hasattr(detail, 'objetivos') else [],
        codigo_bdns=getattr(detail, 'codigoBDNS', None),
        reglamento=json.dumps(detail.reglamento, ensure_ascii=False) if hasattr(detail, 'reglamento') and isinstance(detail.reglamento, (dict, list)) else getattr(detail, 'reglamento', None),
        advertencia=getattr(detail, 'advertencia', None),
        ayuda_estado=getattr(detail, 'ayudaEstado', None),
        url_ayuda_estado=getattr(detail, 'urlAyudaEstado', None),
        instrumentos=detail.instrumentos if hasattr(detail, 'instrumentos') else [],
        descripcion_leng=getattr(detail, 'descripcionLeng', None),
        sede_electronica=getattr(detail, 'sedeElectronica', None),
        presupuesto_total=getattr(detail, 'presupuestoTotal', None),
        tipo_convocatoria=getattr(detail, 'tipoConvocatoria', None),
        sectores_productos=detail.sectoresProductos if hasattr(detail, 'sectoresProductos') else [],
        tipos_beneficiarios_raw=detail.tiposBeneficiarios if hasattr(detail, 'tiposBeneficiarios') else [],
        url_bases_reguladoras=getattr(detail, 'urlBasesReguladoras', None),
        descripcion_finalidad=getattr(detail, 'descripcionFinalidad', None),
        se_publica_diario_oficial=getattr(detail, 'sePublicaDiarioOficial', None),
        descripcion_bases_reguladoras=getattr(detail, 'descripcionBasesReguladoras', None),

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

                # Extract PDF info once for reuse
                pdf_info = _extract_pdf_info(detail)

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
                    retry_count=0,
                    pdf_url=pdf_info['pdf_url'],
                    pdf_hash=pdf_info['pdf_hash']
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
