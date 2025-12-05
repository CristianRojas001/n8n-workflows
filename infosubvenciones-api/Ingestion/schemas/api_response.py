"""Pydantic schemas for InfoSubvenciones API responses."""
from typing import Optional, List, Any
from datetime import date
from pydantic import BaseModel, Field, field_validator


class DocumentoSchema(BaseModel):
    """Schema for document objects in API responses."""
    id: Optional[int] = None
    idDocumento: Optional[int] = None
    nombreFic: Optional[str] = None
    descripcion: Optional[str] = None
    fechaAlta: Optional[str] = None
    tipoDocumento: Optional[str] = None
    urlDescarga: Optional[str] = None

    class Config:
        extra = "allow"  # Allow additional fields


class ConvocatoriaSearchItem(BaseModel):
    """Schema for convocatoria items in search results."""
    numeroConvocatoria: str
    codigo: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    organismo: Optional[str] = None
    finalidad: Optional[str] = None
    abierto: Optional[bool] = False
    fechaPublicacion: Optional[str] = None
    fechaInicioSolicitud: Optional[str] = None
    fechaFinSolicitud: Optional[str] = None
    categoria: Optional[str] = None

    class Config:
        extra = "allow"


class ConvocatoriaSearchResponse(BaseModel):
    """Schema for paginated search response from /convocatorias/busqueda."""
    content: List[ConvocatoriaSearchItem]
    totalElements: int = 0
    totalPages: int = 0
    size: int = 100
    number: int = 0  # Current page number
    numberOfElements: int = 0

    class Config:
        extra = "allow"


class ConvocatoriaDetail(BaseModel):
    """
    Schema for detailed convocatoria from /convocatorias?numConv=XXX.

    This contains the full set of fields including documents array.
    """
    # Core identification
    id: Optional[int] = None
    numeroConvocatoria: Optional[str] = None  # Will be validated/extracted below
    codigo: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    objeto: Optional[str] = None

    # Administrative info
    organismo: Optional[str] = None
    organismoId: Optional[str] = None
    departamento: Optional[str] = None
    tipoAdministracion: Optional[str] = None
    nivelAdministracion: Optional[str] = None

    # Classification
    finalidad: Optional[str] = None
    finalidadDescripcion: Optional[str] = None
    sectores: Optional[List[str]] = Field(default_factory=list)
    regiones: Optional[List[str]] = Field(default_factory=list)
    ambito: Optional[str] = None
    nivel1: Optional[str] = None  # Category level 1
    nivel2: Optional[str] = None  # Category level 2

    # Beneficiaries
    tiposBeneficiario: Optional[List[str]] = Field(default_factory=list)
    beneficiariosDescripcion: Optional[str] = None
    requisitosBeneficiarios: Optional[str] = None

    # Dates (stored as strings, will parse in service layer)
    fechaPublicacion: Optional[str] = None
    fechaRecepcion: Optional[str] = None
    fechaInicioSolicitud: Optional[str] = None
    fechaFinSolicitud: Optional[str] = None
    fechaResolucion: Optional[str] = None
    abierto: Optional[bool] = False

    # Amounts
    importeTotal: Optional[str] = None
    importeMinimo: Optional[str] = None
    importeMaximo: Optional[str] = None
    porcentajeFinanciacion: Optional[str] = None

    # Application info
    formaSolicitud: Optional[str] = None
    lugarPresentacion: Optional[str] = None
    tramiteElectronico: Optional[bool] = False
    urlTramite: Optional[str] = None

    # Documents
    documentos: Optional[List[DocumentoSchema]] = Field(default_factory=list)

    # Additional info
    basesReguladoras: Optional[str] = None
    normativa: Optional[List[Any]] = Field(default_factory=list)
    compatibilidades: Optional[str] = None
    contacto: Optional[dict] = None
    observaciones: Optional[str] = None

    # Category/finalidad (sometimes different field names)
    categoria: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields from API

    @field_validator('numeroConvocatoria', mode='before')
    @classmethod
    def parse_numero(cls, v):
        """Extract numeroConvocatoria - may be in different fields."""
        if v:
            return str(v)
        # If not provided, it must be extracted from raw data in get_convocatoria_detail
        return None

    @field_validator('documentos', mode='before')
    @classmethod
    def parse_documentos(cls, v):
        """Convert documentos to list if needed."""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]

    @field_validator('sectores', 'regiones', 'tiposBeneficiario', mode='before')
    @classmethod
    def parse_arrays(cls, v):
        """Convert comma-separated strings, objects, or ensure list."""
        if v is None:
            return []
        if isinstance(v, str):
            return [x.strip() for x in v.split(',') if x.strip()]
        if isinstance(v, list):
            # Handle list of objects like [{"descripcion": "...", "codigo": "..."}]
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract descripcion or codigo
                    result.append(item.get('descripcion') or item.get('codigo') or str(item))
                else:
                    result.append(str(item))
            return result
        return []


class APIErrorResponse(BaseModel):
    """Schema for API error responses."""
    error: str
    message: Optional[str] = None
    status: Optional[int] = None
    timestamp: Optional[str] = None
