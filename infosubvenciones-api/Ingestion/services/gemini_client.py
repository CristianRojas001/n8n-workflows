"""Gemini LLM Client - for generating summaries and extracting structured data from PDFs."""
import json
from typing import Optional, Dict, Any, Tuple
from loguru import logger
import google.generativeai as genai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config.settings import get_settings


class GeminiClient:
    """
    Client for Gemini 2.0 Flash API to process grant PDF text.

    Features:
    - Generate Spanish summaries (max 500 words)
    - Extract structured fields (eligibility, budget, deadlines, etc.)
    - Retry logic for API failures
    - Rate limiting handling
    """

    def __init__(self):
        """Initialize Gemini client with API key from settings."""
        self.settings = get_settings()

        # Configure Gemini API
        genai.configure(api_key=self.settings.gemini_api_key)

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.settings.gemini_model,
            generation_config={
                'temperature': 0.2,  # Lower temperature for more factual responses
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 8192,
            }
        )

        logger.info(f"GeminiClient initialized with model: {self.settings.gemini_model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def generate_summary(self, text: str, numero_convocatoria: str) -> Tuple[str, float]:
        """
        Generate a Spanish summary of the grant PDF text.

        Args:
            text: Extracted text from PDF
            numero_convocatoria: Grant ID for logging

        Returns:
            Tuple of (summary_text, confidence_score)
        """
        if not text or len(text.strip()) < 50:
            logger.warning(f"Text too short for summary: {numero_convocatoria}")
            return "", 0.0

        prompt = f"""Eres un asistente experto en subvenciones españolas.

Analiza el siguiente texto extraído de una convocatoria de ayudas y genera un resumen en español.

REQUISITOS:
- Máximo 500 palabras
- Escribe en español
- Sé conciso pero completo
- Enfócate en: objetivo, beneficiarios, cuantías, plazos, requisitos
- No inventes información que no esté en el texto
- Si falta información importante, indícalo claramente

TEXTO DE LA CONVOCATORIA:
{text[:10000]}

RESUMEN EN ESPAÑOL:"""

        try:
            logger.info(f"Generating summary for {numero_convocatoria}...")

            response = self.model.generate_content(prompt)

            if not response or not response.text:
                logger.error(f"Empty response from Gemini for {numero_convocatoria}")
                return "", 0.0

            summary = response.text.strip()

            # Estimate confidence based on response quality
            confidence = self._estimate_confidence(summary, text)

            logger.success(
                f"Summary generated for {numero_convocatoria}: "
                f"{len(summary)} chars, confidence: {confidence:.2f}"
            )

            return summary, confidence

        except Exception as e:
            logger.error(f"Error generating summary for {numero_convocatoria}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """
        Extract JSON from various text formats with multiple fallback strategies.

        Args:
            text: Raw response text that may contain JSON

        Returns:
            Extracted JSON string or None
        """
        import re

        # Strategy 1: Remove markdown code blocks
        cleaned = text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Strategy 2: Try direct parse
        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass

        # Strategy 3: Find JSON between curly braces
        # Look for the outermost { } pair
        first_brace = cleaned.find('{')
        if first_brace != -1:
            # Count braces to find matching closing brace
            brace_count = 0
            for i in range(first_brace, len(cleaned)):
                if cleaned[i] == '{':
                    brace_count += 1
                elif cleaned[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        potential_json = cleaned[first_brace:i+1]
                        try:
                            json.loads(potential_json)
                            return potential_json
                        except json.JSONDecodeError:
                            break

        # Strategy 4: Look for JSON after common prefixes
        prefixes = ['json\n', 'JSON\n', 'Here is the JSON:\n', 'Response:\n']
        for prefix in prefixes:
            if prefix in cleaned:
                after_prefix = cleaned.split(prefix, 1)[1].strip()
                try:
                    json.loads(after_prefix)
                    return after_prefix
                except json.JSONDecodeError:
                    pass

        return None

    def _fix_common_json_errors(self, json_str: str) -> str:
        """
        Fix common JSON formatting errors.

        Args:
            json_str: Potentially malformed JSON string

        Returns:
            Fixed JSON string
        """
        import re

        # Fix 1: Remove trailing commas before } or ]
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Fix 2: Remove control characters
        json_str = re.sub(r'[\x00-\x1f\x7f]', '', json_str)

        # Fix 3: Fix common escape sequence issues
        # Replace \n inside strings with actual newline (if it's meant to be literal)
        # This is tricky and we'll be conservative

        return json_str

    def extract_structured_fields(
        self,
        text: str,
        numero_convocatoria: str
    ) -> Dict[str, Any]:
        """
        Extract structured fields from grant PDF text.

        Args:
            text: Extracted text from PDF
            numero_convocatoria: Grant ID for logging

        Returns:
            Dictionary with extracted fields
        """
        if not text or len(text.strip()) < 50:
            logger.warning(f"Text too short for extraction: {numero_convocatoria}")
            return {}

        prompt = f"""Eres un asistente experto en análisis de subvenciones españolas.

Extrae la siguiente información del texto de la convocatoria y devuélvela en formato JSON.

CAMPOS A EXTRAER:

**Información Básica:**
1. titulo: Título de la convocatoria (texto breve)
2. organismo: Organismo convocante (texto breve)
3. ambito_geografico: Ámbito geográfico (ej: "Nacional", "Madrid", etc.)

**Propósito / Finalidad:**
4. finalidad_pdf: Propósito/finalidad en 1-2 oraciones (busca en "Objeto del Convenio", "PRIMERO", "TERCERO", descripciones del proyecto)
5. finalidad_descripcion_pdf: Descripción detallada de la finalidad y actividades financiadas (párrafos completos)

**Información del Beneficiario:**
6. beneficiario_nombre: Nombre del beneficiario específico si es subvención nominativa (texto, ej: "Asociación Cultural XYZ")
7. beneficiario_cif: CIF/NIF del beneficiario (texto, solo el código, ej: "G48261150")
8. proyecto_nombre: Nombre del proyecto o actividad específica (texto, ej: "VII Aula de Flamenco")
9. tipos_beneficiario_raw: Tipo de entidad del beneficiario (ej: "Fundación Pública Local", "Asociación sin ánimo de lucro", "Ayuntamiento")

**Sectores (inferir de las actividades):**
10. sectores_raw: Palabras clave relacionadas con sectores (ej: "flamenco, artes escénicas, cultura, turismo cultural")

**Instrumentos y Procedimiento:**
11. instrumentos_raw: Texto literal del tipo de instrumento (busca: "subvención directa", "concesión nominativa", "vía convenio", etc.)
12. instrumento_normalizado: Tipo de instrumento normalizado (ej: "Subvención directa nominativa", "Convenio", "Concesión directa")
13. procedimiento: Procedimiento de concesión (ej: "Concesión directa", "Concurrencia competitiva")

**Región:**
14. region_mencionada: Regiones, provincias o municipios mencionados en el PDF (ej: "Cádiz, Jerez de la Frontera")

**Firmantes (del documento):**
15. firmantes: Array de firmantes (busca en primera página o al final). Formato: [{{"nombre": "...", "dni": "...", "cargo": "..."}}]

**Verificación CSV:**
16. csv_codigo: Código Seguro de Verificación (busca "CSV", "Código Seguro", en pie de página)
17. url_verificacion: URL de verificación del documento (suele estar junto al CSV)

**Objeto y Alcance:**
18. objeto: Oración completa del propósito (busca "OBJETO", "tiene por objeto")
19. tipo_administracion_raw: Tipo de administración del organismo (Ayuntamiento, Diputación, Junta, Ministerio)
20. nivel_administracion_raw: Nivel específico (municipal, provincial, autonómico, estatal)
21. ambito_raw: Ámbito geográfico literal (busca "ámbito provincial", "en la provincia de", "ámbito estatal")

**Beneficiarios (detalles completos):**
22. beneficiarios_descripcion_pdf: Párrafo completo sobre quién puede recibir la ayuda
23. requisitos_beneficiarios_pdf: Requisitos y condiciones de los beneficiarios (lista de bullets)

**Memoria y Compatibilidad:**
24. memoria_obligatoria: Array de documentos/informes obligatorios (busca en sección "OCTAVA", "justificación"). Formato: ["Memoria de actividades", "Informe económico", ...]
25. es_compatible_otras_ayudas: Boolean - ¿Es compatible con otras subvenciones? (busca en sección "SEGUNDA" o "compatibilidad")

**Detalles Financieros:**
26. importe_total_pdf: Importe total/presupuesto total (texto con unidades)
27. importe_maximo_pdf: Importe máximo por beneficiario (número en euros)
28. gastos_subvencionables: Gastos que se pueden subvencionar (texto detallado)
29. cuantia_subvencion: Cuantía de la subvención (texto descriptivo)
30. cuantia_min: Cuantía mínima en euros (número, solo el valor numérico)
31. cuantia_max: Cuantía máxima en euros (número, solo el valor numérico)
32. intensidad_ayuda: Porcentaje de financiación (texto, ej: "80%")
33. compatibilidad_otras_ayudas: Compatibilidad con otras ayudas (texto descriptivo)

**Solicitud y Presentación:**
34. forma_solicitud_pdf: Cómo presentar la solicitud (presencial, electrónica, ambas; mención del modelo/formulario)
35. lugar_presentacion_pdf: Dónde presentar (direcciones postales, Registro General, sede electrónica)
36. url_tramite_pdf: URL de la sede electrónica o formulario de solicitud

**Normativa:**
37. bases_reguladoras_pdf: Referencias a bases reguladoras (BOE/BOP nº, fecha, etc.)
38. normativa_pdf: Array de leyes y decretos mencionados. Formato: ["Ley 38/2003", "Real Decreto 887/2006", ...]

**Plazos y Ejecución:**
39. plazo_ejecucion: Plazo para ejecutar el proyecto (texto)
40. plazo_justificacion: Plazo para justificar gastos (texto)
41. fecha_inicio_ejecucion: Fecha inicio ejecución (formato YYYY-MM-DD o null)
42. fecha_fin_ejecucion: Fecha fin ejecución (formato YYYY-MM-DD o null)
43. plazo_resolucion: Plazo de resolución (texto)

**Requisitos de Justificación:**
44. forma_justificacion: Cómo justificar los gastos (texto detallado)
45. documentacion_requerida: Documentos requeridos (array de strings o null)
46. sistema_evaluacion: Sistema de evaluación (texto)

**Pago y Garantías:**
47. forma_pago: Forma de pago (texto)
48. pago_anticipado: Porcentaje de pago anticipado (texto, ej: "50%")
49. garantias: Garantías requeridas (texto)
50. exige_aval: Requiere aval bancario (texto: "Sí", "No", o null)

**Obligaciones y Condiciones:**
51. obligaciones_beneficiario: Obligaciones del beneficiario (texto detallado)
52. publicidad_requerida: Requisitos de publicidad (texto)
53. subcontratacion: Reglas de subcontratación (texto)
54. modificaciones_permitidas: Modificaciones permitidas (texto)

**Requisitos Específicos:**
55. requisitos_tecnicos: Requisitos técnicos (texto)
56. criterios_valoracion: Criterios de evaluación (array de objetos con criterio y puntos, o null)
57. documentos_fase_solicitud: Documentos necesarios para solicitar (array de strings o null)

**RAW FIELDS (texto literal sin procesar):**
58. raw_objeto: Texto literal de la sección "OBJETO"
59. raw_finalidad: Texto literal de finalidad
60. raw_ambito: Texto literal de ámbito
61. raw_beneficiarios: Texto literal de beneficiarios
62. raw_requisitos_beneficiarios: Texto literal de requisitos
63. raw_importe_total: Texto literal de importe total
64. raw_importe_maximo: Texto literal de importe máximo
65. raw_porcentaje_financiacion: Texto literal del porcentaje
66. raw_forma_solicitud: Texto literal de forma de solicitud
67. raw_lugar_presentacion: Texto literal del lugar
68. raw_bases_reguladoras: Texto literal de bases reguladoras
69. raw_normativa: Texto literal de normativa completa
70. raw_gastos_subvencionables: Texto literal de gastos
71. raw_forma_justificacion: Texto literal de justificación
72. raw_plazo_ejecucion: Texto literal de plazo ejecución
73. raw_plazo_justificacion: Texto literal de plazo justificación
74. raw_forma_pago: Texto literal de forma de pago
75. raw_compatibilidad: Texto literal de compatibilidad
76. raw_publicidad: Texto literal de publicidad
77. raw_garantias: Texto literal de garantías
78. raw_subcontratacion: Texto literal de subcontratación

IMPORTANTE:
- Si un campo no está en el texto, pon null
- Para cuantia_min, cuantia_max, importe_maximo_pdf: extrae SOLO el número en euros (sin símbolos)
- Para fechas, usa formato YYYY-MM-DD si es posible
- Para arrays (documentacion_requerida, criterios_valoracion, documentos_fase_solicitud, firmantes, memoria_obligatoria, normativa_pdf), usa formato JSON array
- Para es_compatible_otras_ayudas, usa true/false (boolean)
- Para firmantes, extrae nombre completo, DNI/NIF, y cargo. Formato: [{{"nombre": "...", "dni": "...", "cargo": "..."}}]
- Para normativa_pdf, extrae refs a leyes: ["Ley 38/2003", "Real Decreto 887/2006", ...]
- Sé preciso y cita textualmente cuando sea posible
- NO inventes información que no está en el texto
- Si hay incertidumbre, mejor pon null
- Para campos raw_*: copia el texto literal completo de esa sección del PDF (sin resumir)
- Para campos _raw sin prefijo raw: copia texto literal pero más breve
- Para instrumento_normalizado, usa uno de: "Subvención directa nominativa", "Subvención concurrencia competitiva", "Convenio", "Concesión directa"
- Para procedimiento, usa uno de: "Concesión directa", "Concurrencia competitiva", "Convenio"

TEXTO DE LA CONVOCATORIA:
{text[:20000]}

Responde SOLO con el JSON, sin texto adicional:"""

        try:
            logger.info(f"Extracting fields for {numero_convocatoria}...")

            response = self.model.generate_content(prompt)

            if not response or not response.text:
                logger.error(f"Empty response from Gemini for {numero_convocatoria}")
                return {}

            # Extract JSON using robust multi-strategy approach
            json_str = self._extract_json_from_text(response.text)

            if not json_str:
                logger.error(f"Could not extract JSON from Gemini response for {numero_convocatoria}")
                logger.error(f"Response text (first 500 chars): {response.text[:500]}...")
                return {}

            # Try to parse the extracted JSON
            try:
                fields = json.loads(json_str)
            except json.JSONDecodeError as e:
                # Try to fix common JSON errors
                logger.warning(f"Initial JSON parse failed for {numero_convocatoria}, attempting to fix common errors: {e}")
                fixed_json = self._fix_common_json_errors(json_str)

                try:
                    fields = json.loads(fixed_json)
                    logger.info(f"Successfully parsed JSON after fixing common errors for {numero_convocatoria}")
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse JSON even after fixes for {numero_convocatoria}: {e2}")
                    logger.error(f"Original error: {e}")
                    logger.error(f"JSON string (first 1000 chars): {json_str[:1000]}")
                    return {}

            logger.success(
                f"Extracted {len(fields)} fields for {numero_convocatoria}"
            )

            return fields

        except Exception as e:
            logger.error(f"Error extracting fields for {numero_convocatoria}: {e}")
            raise

    def process_pdf_text(
        self,
        text: str,
        numero_convocatoria: str
    ) -> Tuple[str, Dict[str, Any], float]:
        """
        Complete processing: generate summary + extract fields.

        Args:
            text: Extracted text from PDF
            numero_convocatoria: Grant ID for logging

        Returns:
            Tuple of (summary, extracted_fields, confidence)
        """
        logger.info(f"Processing PDF text for {numero_convocatoria}...")

        # Generate summary
        summary, confidence = self.generate_summary(text, numero_convocatoria)

        # Extract structured fields
        fields = self.extract_structured_fields(text, numero_convocatoria)

        logger.success(
            f"Completed processing for {numero_convocatoria}: "
            f"summary={len(summary)} chars, fields={len(fields)}, confidence={confidence:.2f}"
        )

        return summary, fields, confidence

    def _estimate_confidence(self, summary: str, original_text: str) -> float:
        """
        Estimate confidence score based on summary quality.

        Args:
            summary: Generated summary
            original_text: Original PDF text

        Returns:
            Confidence score (0.0 - 1.0)
        """
        if not summary or len(summary) < 50:
            return 0.0

        # Base confidence
        confidence = 0.7

        # Adjust based on summary length
        if 200 <= len(summary) <= 3000:
            confidence += 0.1
        elif len(summary) > 5000:
            confidence -= 0.1

        # Check for common quality indicators
        quality_indicators = [
            'beneficiarios', 'cuantía', 'plazo', 'requisitos',
            'objetivo', 'ayuda', 'subvención'
        ]

        matches = sum(1 for indicator in quality_indicators if indicator.lower() in summary.lower())
        confidence += (matches / len(quality_indicators)) * 0.2

        # Cap at 0.95 (never 100% confident)
        return min(confidence, 0.95)


# Example usage
if __name__ == "__main__":
    logger.info("Testing GeminiClient...")

    # Test with sample text
    test_text = """
    ORDEN de 15 de enero de 2024 por la que se convocan ayudas para proyectos culturales.

    Artículo 1. Objeto
    La presente orden tiene por objeto convocar ayudas destinadas a proyectos culturales.

    Artículo 2. Beneficiarios
    Podrán ser beneficiarios las entidades sin ánimo de lucro.

    Artículo 3. Cuantía
    La cuantía máxima de la ayuda será de 50.000 euros.
    """

    try:
        client = GeminiClient()

        summary, fields, confidence = client.process_pdf_text(test_text, "TEST-001")

        logger.info(f"\nSummary:\n{summary}\n")
        logger.info(f"Fields: {json.dumps(fields, indent=2, ensure_ascii=False)}")
        logger.info(f"Confidence: {confidence:.2f}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
