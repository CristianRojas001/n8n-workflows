"""Convocatoria model - stores metadata from InfoSubvenciones API."""
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ARRAY, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from config.database import Base


class Convocatoria(Base):
    """
    Stores grant/subsidy information fetched from InfoSubvenciones API.

    This model contains 40+ fields from the API response, including:
    - Basic identification (numero, codigo, titulo)
    - Administrative info (organismo, sector, region)
    - Dates (publication, deadlines)
    - Beneficiaries and purpose (finalidad, beneficiarios)
    - Amounts and documents
    """
    __tablename__ = 'convocatorias'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # === IDENTIFICATION FIELDS ===
    numero_convocatoria = Column(String(50), unique=True, nullable=False, index=True)
    codigo = Column(String(100), nullable=True)
    titulo = Column(Text, nullable=True)
    descripcion = Column(Text, nullable=True)
    objeto = Column(Text, nullable=True)  # Purpose of the grant

    # === ADMINISTRATIVE FIELDS ===
    organismo = Column(String(255), nullable=True, index=True)  # Granting organization
    organismo_id = Column(String(50), nullable=True)
    departamento = Column(String(255), nullable=True)  # Government department
    tipo_administracion = Column(String(100), nullable=True)  # Type of administration
    nivel_administracion = Column(String(100), nullable=True)  # Administration level

    # === CLASSIFICATION FIELDS ===
    finalidad = Column(String(50), nullable=True, index=True)  # Purpose category (11, 14, etc.)
    finalidad_descripcion = Column(String(255), nullable=True)
    sectores = Column(ARRAY(String), nullable=True)  # Array of sector codes/names
    regiones = Column(ARRAY(String), nullable=True, index=True)  # Array of region codes
    ambito = Column(String(100), nullable=True)  # Scope (nacional, regional, local)

    # === BENEFICIARY FIELDS ===
    tipos_beneficiario = Column(ARRAY(String), nullable=True)  # Types of beneficiaries
    beneficiarios_descripcion = Column(Text, nullable=True)
    requisitos_beneficiarios = Column(Text, nullable=True)

    # === DATE FIELDS ===
    fecha_publicacion = Column(Date, nullable=True)
    fecha_inicio_solicitud = Column(Date, nullable=True, index=True)
    fecha_fin_solicitud = Column(Date, nullable=True, index=True)
    fecha_resolucion = Column(Date, nullable=True)
    abierto = Column(Boolean, default=False, nullable=False, index=True)  # Currently open

    # === AMOUNT FIELDS ===
    importe_total = Column(String(100), nullable=True)  # Total amount (stored as string, may have currency)
    importe_minimo = Column(String(100), nullable=True)
    importe_maximo = Column(String(100), nullable=True)
    porcentaje_financiacion = Column(String(50), nullable=True)  # Financing percentage

    # === APPLICATION FIELDS ===
    forma_solicitud = Column(Text, nullable=True)  # How to apply
    lugar_presentacion = Column(Text, nullable=True)  # Where to submit
    tramite_electronico = Column(Boolean, default=False)  # Electronic processing available
    url_tramite = Column(Text, nullable=True)  # URL for online application

    # === DOCUMENTS ===
    documentos = Column(JSONB, nullable=True)  # Array of document objects from API
    tiene_pdf = Column(Boolean, default=False)  # Whether main PDF was found
    pdf_url = Column(Text, nullable=True)  # URL to main PDF
    pdf_nombre = Column(String(255), nullable=True)  # PDF filename
    pdf_id_documento = Column(String(50), nullable=True)  # Document ID from API
    pdf_hash = Column(String(64), nullable=True, unique=True, index=True)  # SHA256 of PDF content

    # === ADDITIONAL INFO ===
    bases_reguladoras = Column(Text, nullable=True)  # Regulatory bases
    normativa = Column(JSONB, nullable=True)  # Related regulations (array)
    compatibilidades = Column(Text, nullable=True)  # Compatibility with other grants
    contacto = Column(JSONB, nullable=True)  # Contact information
    observaciones = Column(Text, nullable=True)  # Observations/notes

    # === RAW DATA ===
    raw_api_response = Column(JSONB, nullable=True)  # Full API response (for debugging)

    # === METADATA ===
    fuente = Column(String(50), default='infosubvenciones', nullable=False)  # Data source
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<Convocatoria(numero={self.numero_convocatoria}, titulo={self.titulo[:50] if self.titulo else 'N/A'})>"

    @property
    def is_open(self):
        """Check if application is currently open."""
        return self.abierto

    @property
    def has_documents(self):
        """Check if convocatoria has any documents."""
        return bool(self.documentos) and len(self.documentos) > 0
