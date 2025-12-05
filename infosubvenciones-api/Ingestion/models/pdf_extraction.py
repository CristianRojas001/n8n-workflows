"""PDF Extraction model - stores fields extracted from grant PDFs by LLM."""
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, Float, Boolean, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from config.database import Base


class PDFExtraction(Base):
    """
    Stores structured data extracted from PDF documents using LLM (Gemini).

    This table contains 20+ fields that are NOT available in the API but are
    extracted from the PDF text using the LLM, including:
    - Eligible expenses
    - Justification requirements
    - Payment terms
    - Execution deadlines
    - Guarantees and warranties
    """
    __tablename__ = 'pdf_extractions'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to convocatorias (direct reference for fast queries)
    convocatoria_id = Column(
        Integer,
        ForeignKey('convocatorias.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,  # One PDF extraction per convocatoria
        index=True
    )

    # Foreign key to staging_items (pipeline tracking)
    staging_id = Column(
        Integer,
        ForeignKey('staging_items.id', ondelete='CASCADE'),
        nullable=True,  # Nullable for backward compatibility
        unique=True,
        index=True
    )

    # Reference to original convocatoria (for convenience)
    numero_convocatoria = Column(String(50), nullable=False, index=True)

    # Relationship to staging_item
    staging_item = relationship("StagingItem", backref="pdf_extraction")

    # Full extracted text from PDF (for embedding generation)
    extracted_text = Column(Text, nullable=True)  # Raw text from PDF
    extracted_summary = Column(Text, nullable=True)  # LLM-generated summary
    summary_preview = Column(String(500), nullable=True)  # First 500 chars of summary

    # === BASIC INFO (extracted from PDF by LLM) ===
    titulo = Column(String(500), nullable=True)  # Grant title from PDF
    organismo = Column(String(300), nullable=True)  # Organization from PDF
    ambito_geografico = Column(String(200), nullable=True)  # Geographic scope from PDF

    # === BENEFICIARY INFO (for nominative grants) ===
    beneficiario_nombre = Column(String(500), nullable=True)  # Specific beneficiary name
    beneficiario_cif = Column(String(20), nullable=True)  # Tax ID (CIF/NIF)
    proyecto_nombre = Column(String(500), nullable=True)  # Specific project/activity name

    # === PURPOSE / FINALIDAD (from PDF) ===
    finalidad_pdf = Column(Text, nullable=True)  # Purpose extracted from PDF (1-2 sentences)
    finalidad_descripcion_pdf = Column(Text, nullable=True)  # Detailed purpose from PDF (long paragraphs)

    # === BENEFICIARY TYPES (raw + normalized) ===
    tipos_beneficiario_raw = Column(Text, nullable=True)  # Raw beneficiary type text
    tipos_beneficiario_normalized = Column(ARRAY(Text), nullable=True)  # Normalized array

    # === SECTORS (raw + inferred) ===
    sectores_raw = Column(Text, nullable=True)  # Raw sector keywords from PDF
    sectores_inferidos = Column(ARRAY(Text), nullable=True)  # Inferred sectors from activity

    # === INSTRUMENTS (raw + normalized) ===
    instrumentos_raw = Column(Text, nullable=True)  # Raw instrument text
    instrumento_normalizado = Column(String(200), nullable=True)  # Normalized instrument type

    # === PROCEDURE ===
    procedimiento = Column(String(200), nullable=True)  # Procedure type

    # === REGION (mentioned + NUTS) ===
    region_mencionada = Column(Text, nullable=True)  # Region mentioned in PDF
    region_nuts = Column(String(20), nullable=True)  # NUTS code (e.g., "ES612")

    # === SIGNATORIES ===
    firmantes = Column(JSONB, nullable=True)  # Array of signatories: [{nombre, dni, cargo}]

    # === CSV VERIFICATION ===
    csv_codigo = Column(String(200), nullable=True)  # Código Seguro de Verificación
    url_verificacion = Column(Text, nullable=True)  # Verification URL

    # === REQUIRED REPORTS ===
    memoria_obligatoria = Column(JSONB, nullable=True)  # Checklist of required reports

    # === COMPATIBILITY FLAG ===
    es_compatible_otras_ayudas = Column(Boolean, nullable=True)  # Boolean compatibility flag

    # === FINANCIAL DETAILS ===
    gastos_subvencionables = Column(Text, nullable=True)  # Eligible expenses
    cuantia_subvencion = Column(Text, nullable=True)  # Grant amount from PDF
    cuantia_min = Column(Float, nullable=True)  # Minimum amount (parsed)
    cuantia_max = Column(Float, nullable=True)  # Maximum amount (parsed)
    intensidad_ayuda = Column(Text, nullable=True)  # Aid intensity (percentage)
    compatibilidad_otras_ayudas = Column(Text, nullable=True)  # Compatibility with other aids

    # === DEADLINES & EXECUTION ===
    plazo_ejecucion = Column(Text, nullable=True)  # Execution deadline
    plazo_justificacion = Column(Text, nullable=True)  # Justification deadline
    fecha_inicio_ejecucion = Column(Date, nullable=True)  # Start of execution period
    fecha_fin_ejecucion = Column(Date, nullable=True)  # End of execution period
    plazo_resolucion = Column(Text, nullable=True)  # Resolution deadline

    # === JUSTIFICATION REQUIREMENTS ===
    forma_justificacion = Column(Text, nullable=True)  # How to justify expenses
    documentacion_requerida = Column(JSONB, nullable=True)  # Required documentation (array)
    sistema_evaluacion = Column(Text, nullable=True)  # Evaluation system

    # === PAYMENT & GUARANTEES ===
    forma_pago = Column(Text, nullable=True)  # Payment method
    pago_anticipado = Column(Text, nullable=True)  # Advance payment percentage
    garantias = Column(Text, nullable=True)  # Required guarantees
    exige_aval = Column(Text, nullable=True)  # Requires surety bond (Yes/No)

    # === OBLIGATIONS & CONDITIONS ===
    obligaciones_beneficiario = Column(Text, nullable=True)  # Beneficiary obligations
    publicidad_requerida = Column(Text, nullable=True)  # Required publicity
    subcontratacion = Column(Text, nullable=True)  # Subcontracting rules
    modificaciones_permitidas = Column(Text, nullable=True)  # Allowed modifications

    # === SPECIFIC REQUIREMENTS ===
    requisitos_tecnicos = Column(Text, nullable=True)  # Technical requirements
    criterios_valoracion = Column(JSONB, nullable=True)  # Evaluation criteria (structured)
    documentos_fase_solicitud = Column(JSONB, nullable=True)  # Documents for application phase

    # === PHASE 2 FIELDS ===

    # Amounts from PDF (fallbacks when API is null)
    importe_total_pdf = Column(Text, nullable=True)  # Total budget from PDF
    importe_maximo_pdf = Column(Float, nullable=True)  # Maximum amount from PDF

    # Inference fields (raw + normalized)
    tipo_administracion_raw = Column(Text, nullable=True)  # Raw admin type text
    nivel_administracion_raw = Column(Text, nullable=True)  # Raw admin level text
    ambito_raw = Column(Text, nullable=True)  # Raw scope text
    tipo_administracion_normalizado = Column(String(100), nullable=True)  # Normalized
    nivel_administracion_normalizado = Column(String(100), nullable=True)  # Normalized
    ambito_normalizado = Column(String(100), nullable=True)  # Normalized

    # Beneficiary details from PDF
    beneficiarios_descripcion_pdf = Column(Text, nullable=True)  # Full beneficiary description
    requisitos_beneficiarios_pdf = Column(Text, nullable=True)  # Requirements for beneficiaries

    # Application/submission from PDF
    forma_solicitud_pdf = Column(Text, nullable=True)  # How to apply
    lugar_presentacion_pdf = Column(Text, nullable=True)  # Where to submit
    url_tramite_pdf = Column(Text, nullable=True)  # Application URL

    # Normativa from PDF
    bases_reguladoras_pdf = Column(Text, nullable=True)  # Regulatory bases
    normativa_pdf = Column(JSONB, nullable=True)  # Law references array

    # === RAW EXTRACTIONS (for debugging/review) ===
    raw_objeto = Column(Text, nullable=True)  # Raw "objeto" text
    raw_finalidad = Column(Text, nullable=True)  # Raw "finalidad" text
    raw_ambito = Column(Text, nullable=True)  # Raw "ámbito" text
    raw_beneficiarios = Column(Text, nullable=True)  # Raw beneficiaries text
    raw_requisitos_beneficiarios = Column(Text, nullable=True)  # Raw requirements
    raw_importe_total = Column(Text, nullable=True)  # Raw total amount
    raw_importe_maximo = Column(Text, nullable=True)  # Raw maximum amount
    raw_porcentaje_financiacion = Column(Text, nullable=True)  # Raw financing %
    raw_forma_solicitud = Column(Text, nullable=True)  # Raw application form
    raw_lugar_presentacion = Column(Text, nullable=True)  # Raw submission place
    raw_bases_reguladoras = Column(Text, nullable=True)  # Raw regulatory bases
    raw_normativa = Column(Text, nullable=True)  # Raw normativa text
    raw_gastos_subvencionables = Column(Text, nullable=True)  # Raw eligible expenses
    raw_forma_justificacion = Column(Text, nullable=True)  # Raw justification
    raw_plazo_ejecucion = Column(Text, nullable=True)  # Raw execution period
    raw_plazo_justificacion = Column(Text, nullable=True)  # Raw justification deadline
    raw_forma_pago = Column(Text, nullable=True)  # Raw payment form
    raw_compatibilidad = Column(Text, nullable=True)  # Raw compatibility text
    raw_publicidad = Column(Text, nullable=True)  # Raw publicity requirements
    raw_garantias = Column(Text, nullable=True)  # Raw guarantees
    raw_subcontratacion = Column(Text, nullable=True)  # Raw subcontracting

    # === EXTRACTION METADATA ===
    extraction_model = Column(String(50), default='gemini-2.0-flash', nullable=False)  # Model used
    extraction_confidence = Column(Float, nullable=True)  # Confidence score (0-1)
    extraction_error = Column(Text, nullable=True)  # Error message if extraction failed
    markdown_path = Column(String(512), nullable=True)  # Path to markdown file
    pdf_page_count = Column(Integer, nullable=True)  # Number of pages in PDF
    pdf_word_count = Column(Integer, nullable=True)  # Estimated word count

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<PDFExtraction(numero={self.numero_convocatoria}, model={self.extraction_model})>"

    @property
    def has_financial_details(self):
        """Check if financial details were extracted."""
        return bool(self.gastos_subvencionables or self.cuantia_subvencion)

    @property
    def has_deadlines(self):
        """Check if deadline information was extracted."""
        return bool(self.plazo_ejecucion or self.plazo_justificacion)
