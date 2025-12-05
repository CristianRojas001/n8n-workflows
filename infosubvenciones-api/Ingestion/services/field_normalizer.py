"""
Field Normalizer Service - Post-processes LLM extracted fields.

This service applies deterministic normalization rules to raw extracted fields:
- Sectors: Maps keywords to standardized sector names
- Instruments: Normalizes instrument types
- Regions: Maps locations to NUTS codes
- Beneficiary types: Standardizes entity types

Author: Claude
Date: 2025-12-03
"""

from typing import List, Optional, Dict, Any
from loguru import logger
import re


class FieldNormalizer:
    """
    Normalizes extracted fields using rule-based mappings.

    This complements LLM extraction with deterministic post-processing
    that can be tweaked over time without reprocessing PDFs.
    """

    # Sector keyword mappings (CNAE-like sectors)
    SECTOR_KEYWORDS = {
        'Cultura y artes': [
            'flamenco', 'artes escénicas', 'teatro', 'danza', 'música',
            'cultura', 'cultural', 'artístico', 'patrimonio cultural',
            'museo', 'exposición', 'festival', 'concierto'
        ],
        'Turismo': [
            'turismo', 'turístico', 'hotelero', 'hostelería',
            'alojamiento turístico', 'promoción turística'
        ],
        'Comercio': [
            'comercio', 'comercial', 'venta', 'tienda', 'establecimiento comercial',
            'pyme comercial', 'pequeño comercio'
        ],
        'Industria': [
            'industria', 'industrial', 'fabricación', 'manufactura',
            'producción industrial'
        ],
        'Tecnología e innovación': [
            'tecnología', 'tecnológico', 'innovación', 'i+d+i', 'investigación',
            'desarrollo tecnológico', 'digitalización', 'transformación digital'
        ],
        'Medio ambiente': [
            'medio ambiente', 'ambiental', 'sostenibilidad', 'energía renovable',
            'eficiencia energética', 'economía circular', 'reciclaje'
        ],
        'Agricultura y ganadería': [
            'agricultura', 'agrícola', 'ganadería', 'ganadero', 'rural',
            'desarrollo rural', 'agropecuario'
        ],
        'Servicios sociales': [
            'social', 'servicios sociales', 'asistencia social', 'dependencia',
            'mayores', 'discapacidad', 'inclusión social'
        ],
        'Educación y formación': [
            'educación', 'educativo', 'formación', 'capacitación',
            'enseñanza', 'escolar', 'académico'
        ],
        'Deporte': [
            'deporte', 'deportivo', 'actividad física', 'instalación deportiva'
        ]
    }

    # Instrument normalization
    INSTRUMENT_MAPPINGS = {
        'Subvención directa nominativa': [
            'subvención directa nominativa', 'subvención nominativa',
            'concesión nominativa', 'nominativa'
        ],
        'Subvención concurrencia competitiva': [
            'concurrencia competitiva', 'convocatoria pública',
            'régimen de concurrencia'
        ],
        'Convenio': [
            'convenio', 'convenio de colaboración', 'acuerdo',
            'vía convenio'
        ],
        'Concesión directa': [
            'concesión directa', 'directa'
        ]
    }

    # Procedure mappings
    PROCEDURE_MAPPINGS = {
        'Concesión directa': [
            'concesión directa', 'directa', 'sin concurrencia',
            'procedimiento directo'
        ],
        'Concurrencia competitiva': [
            'concurrencia competitiva', 'competitivo', 'convocatoria pública'
        ],
        'Convenio': [
            'convenio', 'vía convenio'
        ]
    }

    # Administration type mappings
    TIPO_ADMIN_MAPPINGS = {
        'Local': [
            'ayuntamiento', 'municipio', 'concejo', 'cabildo',
            'corporación municipal', 'consistorio'
        ],
        'Provincial': [
            'diputación', 'diputación provincial', 'cabildo insular',
            'fundación provincial'
        ],
        'Autonómica': [
            'comunidad autónoma', 'junta de', 'generalitat', 'gobierno de',
            'xunta de', 'gobierno vasco', 'gobierno autonómico'
        ],
        'Estatal': [
            'ministerio', 'estado', 'gobierno de españa', 'administración general del estado',
            'age', 'secretaría de estado'
        ]
    }

    # Administration level mappings
    NIVEL_ADMIN_MAPPINGS = {
        'Municipal': [
            'ayuntamiento', 'municipio', 'concejo', 'consistorio'
        ],
        'Provincial': [
            'diputación', 'provincia', 'cabildo insular'
        ],
        'Autonómico': [
            'autonómica', 'comunidad autónoma', 'autonomía', 'autonómico'
        ],
        'Estatal': [
            'estado', 'estatal', 'nacional', 'ministerio'
        ],
        'Internacional': [
            'internacional', 'europeo', 'unión europea', 'comisión europea'
        ]
    }

    # Scope (ámbito) mappings
    AMBITO_MAPPINGS = {
        'Local': [
            'ámbito local', 'ámbito municipal', 'municipio de', 'en el término municipal'
        ],
        'Provincial': [
            'ámbito provincial', 'en la provincia de', 'la provincia de', 'provincial'
        ],
        'Autonómico': [
            'ámbito autonómico', 'comunidad autónoma', 'autonómico'
        ],
        'Estatal': [
            'ámbito estatal', 'ámbito nacional', 'todo el territorio español', 'estatal'
        ],
        'Internacional': [
            'ámbito internacional', 'internacional', 'europeo'
        ]
    }

    # Beneficiary type normalization
    BENEFICIARY_TYPE_MAPPINGS = {
        'Fundación': [
            'fundación', 'fundación pública', 'fundación privada',
            'fundación pública local'
        ],
        'Asociación': [
            'asociación', 'asociación sin ánimo de lucro',
            'asociación cultural', 'asociación deportiva'
        ],
        'Ayuntamiento': [
            'ayuntamiento', 'municipio', 'corporación local',
            'entidad local'
        ],
        'Empresa': [
            'empresa', 'sociedad', 'pyme', 'autónomo', 'emprendedor',
            'pequeña empresa', 'mediana empresa'
        ],
        'Universidad': [
            'universidad', 'centro universitario', 'institución académica'
        ],
        'ONG': [
            'ong', 'organización no gubernamental', 'entidad sin ánimo de lucro'
        ],
        'Cooperativa': [
            'cooperativa', 'sociedad cooperativa'
        ],
        'Cámara de Comercio': [
            'cámara de comercio', 'cámara oficial'
        ]
    }

    # Spanish regions to NUTS codes
    REGION_NUTS_MAPPINGS = {
        # Autonomous Communities (NUTS-2)
        'ES61': ['Andalucía', 'Andalucia'],
        'ES24': ['Aragón', 'Aragon'],
        'ES12': ['Asturias', 'Principado de Asturias'],
        'ES53': ['Islas Baleares', 'Baleares', 'Illes Balears'],
        'ES70': ['Canarias', 'Islas Canarias'],
        'ES13': ['Cantabria'],
        'ES42': ['Castilla-La Mancha', 'Castilla La Mancha'],
        'ES41': ['Castilla y León', 'Castilla Leon'],
        'ES51': ['Cataluña', 'Catalunya', 'Catalonia'],
        'ES43': ['Extremadura'],
        'ES11': ['Galicia'],
        'ES30': ['Madrid', 'Comunidad de Madrid'],
        'ES62': ['Murcia', 'Región de Murcia'],
        'ES22': ['Navarra', 'Comunidad Foral de Navarra'],
        'ES21': ['País Vasco', 'Euskadi', 'Pais Vasco'],
        'ES23': ['La Rioja', 'Rioja'],
        'ES52': ['Valencia', 'Comunitat Valenciana', 'Comunidad Valenciana'],
        'ES63': ['Ceuta'],
        'ES64': ['Melilla'],

        # Major provinces (NUTS-3) - Most common ones
        'ES612': ['Cádiz', 'Cadiz'],
        'ES618': ['Sevilla', 'Seville'],
        'ES614': ['Córdoba', 'Cordoba'],
        'ES611': ['Almería', 'Almeria'],
        'ES613': ['Granada'],
        'ES615': ['Huelva'],
        'ES616': ['Jaén', 'Jaen'],
        'ES617': ['Málaga', 'Malaga'],

        'ES300': ['Madrid'],

        'ES511': ['Barcelona'],
        'ES512': ['Girona', 'Gerona'],
        'ES513': ['Lleida', 'Lérida'],
        'ES514': ['Tarragona'],

        'ES521': ['Alicante', 'Alacant'],
        'ES522': ['Castellón', 'Castellon', 'Castelló'],
        'ES523': ['Valencia', 'València'],

        'ES211': ['Álava', 'Araba', 'Alava'],
        'ES213': ['Bizkaia', 'Vizcaya'],
        'ES212': ['Gipuzkoa', 'Guipúzcoa', 'Guipuzcoa'],
    }

    def normalize_sectors(self, sectores_raw: Optional[str]) -> List[str]:
        """
        Infer sectors from raw keywords.

        Args:
            sectores_raw: Raw sector keywords from LLM

        Returns:
            List of standardized sector names
        """
        if not sectores_raw:
            return []

        sectors = set()
        text_lower = sectores_raw.lower()

        for sector, keywords in self.SECTOR_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    sectors.add(sector)
                    break

        result = sorted(list(sectors))
        logger.debug(f"Normalized sectors: {sectores_raw} -> {result}")
        return result

    def normalize_instrument(self, instrumentos_raw: Optional[str], instrumento_llm: Optional[str]) -> Optional[str]:
        """
        Normalize instrument type.

        Uses LLM suggestion first, then applies deterministic rules.

        Args:
            instrumentos_raw: Raw instrument text from PDF
            instrumento_llm: LLM's normalized suggestion

        Returns:
            Standardized instrument name
        """
        # Try LLM suggestion first if it's valid
        if instrumento_llm:
            for standard_name, patterns in self.INSTRUMENT_MAPPINGS.items():
                if instrumento_llm.lower() in [p.lower() for p in patterns]:
                    return standard_name
                if any(pattern in instrumento_llm.lower() for pattern in patterns):
                    return standard_name

        # Fall back to raw text matching
        if instrumentos_raw:
            text_lower = instrumentos_raw.lower()
            for standard_name, patterns in self.INSTRUMENT_MAPPINGS.items():
                if any(pattern in text_lower for pattern in patterns):
                    return standard_name

        # Return LLM suggestion as-is if no match
        return instrumento_llm

    def normalize_procedure(self, procedimiento_llm: Optional[str], instrumentos_raw: Optional[str]) -> Optional[str]:
        """
        Normalize procedure type.

        Args:
            procedimiento_llm: LLM's procedure suggestion
            instrumentos_raw: Raw instrument text (fallback)

        Returns:
            Standardized procedure name
        """
        # Try LLM suggestion first
        if procedimiento_llm:
            text_lower = procedimiento_llm.lower()
            for standard_name, patterns in self.PROCEDURE_MAPPINGS.items():
                if any(pattern in text_lower for pattern in patterns):
                    return standard_name

        # Fall back to instrument raw text
        if instrumentos_raw:
            text_lower = instrumentos_raw.lower()
            for standard_name, patterns in self.PROCEDURE_MAPPINGS.items():
                if any(pattern in text_lower for pattern in patterns):
                    return standard_name

        return procedimiento_llm

    def normalize_beneficiary_types(self, tipos_beneficiario_raw: Optional[str]) -> List[str]:
        """
        Normalize beneficiary types to standard categories.

        Args:
            tipos_beneficiario_raw: Raw beneficiary type text

        Returns:
            List of standardized beneficiary types
        """
        if not tipos_beneficiario_raw:
            return []

        types = set()
        text_lower = tipos_beneficiario_raw.lower()

        for standard_type, patterns in self.BENEFICIARY_TYPE_MAPPINGS.items():
            if any(pattern in text_lower for pattern in patterns):
                types.add(standard_type)

        result = sorted(list(types))
        logger.debug(f"Normalized beneficiary types: {tipos_beneficiario_raw} -> {result}")
        return result

    def infer_nuts_code(self, region_mencionada: Optional[str]) -> Optional[str]:
        """
        Infer NUTS code from mentioned region.

        Args:
            region_mencionada: Region/location text from PDF

        Returns:
            NUTS code (most specific available) or None
        """
        if not region_mencionada:
            return None

        text_lower = region_mencionada.lower()

        # Try to find most specific match (NUTS-3 before NUTS-2)
        # Sort by code specificity (longer codes = more specific)
        sorted_mappings = sorted(
            self.REGION_NUTS_MAPPINGS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for nuts_code, region_names in sorted_mappings:
            for region_name in region_names:
                if region_name.lower() in text_lower:
                    logger.debug(f"Matched region: {region_mencionada} -> {nuts_code}")
                    return nuts_code

        logger.debug(f"No NUTS match for region: {region_mencionada}")
        return None

    def normalize_tipo_admin(self, tipo_admin_raw: Optional[str]) -> Optional[str]:
        """Normalize administration type."""
        if not tipo_admin_raw:
            return None

        text_lower = tipo_admin_raw.lower()
        for standard_type, patterns in self.TIPO_ADMIN_MAPPINGS.items():
            if any(pattern in text_lower for pattern in patterns):
                return standard_type
        return None

    def normalize_nivel_admin(self, nivel_admin_raw: Optional[str]) -> Optional[str]:
        """Normalize administration level."""
        if not nivel_admin_raw:
            return None

        text_lower = nivel_admin_raw.lower()
        for standard_level, patterns in self.NIVEL_ADMIN_MAPPINGS.items():
            if any(pattern in text_lower for pattern in patterns):
                return standard_level
        return None

    def normalize_ambito(self, ambito_raw: Optional[str]) -> Optional[str]:
        """Normalize scope/ambito."""
        if not ambito_raw:
            return None

        text_lower = ambito_raw.lower()
        for standard_ambito, patterns in self.AMBITO_MAPPINGS.items():
            if any(pattern in text_lower for pattern in patterns):
                return standard_ambito
        return None

    def normalize_all_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all normalization rules to extracted fields.

        Args:
            fields: Raw fields from LLM extraction

        Returns:
            Dictionary with additional normalized fields
        """
        normalized = {}

        # Sectors
        if 'sectores_raw' in fields:
            normalized['sectores_inferidos'] = self.normalize_sectors(fields.get('sectores_raw'))

        # Instrument
        if 'instrumentos_raw' in fields or 'instrumento_normalizado' in fields:
            normalized['instrumento_normalizado'] = self.normalize_instrument(
                fields.get('instrumentos_raw'),
                fields.get('instrumento_normalizado')
            )

        # Procedure
        if 'procedimiento' in fields or 'instrumentos_raw' in fields:
            normalized['procedimiento'] = self.normalize_procedure(
                fields.get('procedimiento'),
                fields.get('instrumentos_raw')
            )

        # Beneficiary types
        if 'tipos_beneficiario_raw' in fields:
            normalized['tipos_beneficiario_normalized'] = self.normalize_beneficiary_types(
                fields.get('tipos_beneficiario_raw')
            )

        # Region NUTS
        if 'region_mencionada' in fields:
            normalized['region_nuts'] = self.infer_nuts_code(fields.get('region_mencionada'))

        # Administration type
        if 'tipo_administracion_raw' in fields:
            normalized['tipo_administracion_normalizado'] = self.normalize_tipo_admin(
                fields.get('tipo_administracion_raw')
            )

        # Administration level
        if 'nivel_administracion_raw' in fields:
            normalized['nivel_administracion_normalizado'] = self.normalize_nivel_admin(
                fields.get('nivel_administracion_raw')
            )

        # Scope/Ambito
        if 'ambito_raw' in fields:
            normalized['ambito_normalizado'] = self.normalize_ambito(fields.get('ambito_raw'))

        logger.debug(f"Normalized {len(normalized)} fields")
        return normalized


# Example usage
if __name__ == "__main__":
    logger.info("Testing FieldNormalizer...")

    normalizer = FieldNormalizer()

    # Test data
    test_fields = {
        'sectores_raw': 'flamenco, artes escénicas, cultura, turismo cultural',
        'instrumentos_raw': 'subvención directa nominativa vía convenio',
        'instrumento_normalizado': 'Subvención directa nominativa',
        'procedimiento': 'concesión directa',
        'tipos_beneficiario_raw': 'Fundación Pública Local',
        'region_mencionada': 'Cádiz, Jerez de la Frontera'
    }

    normalized = normalizer.normalize_all_fields(test_fields)

    logger.info("\nTest Results:")
    logger.info(f"  Sectors: {normalized.get('sectores_inferidos')}")
    logger.info(f"  Instrument: {normalized.get('instrumento_normalizado')}")
    logger.info(f"  Procedure: {normalized.get('procedimiento')}")
    logger.info(f"  Beneficiary types: {normalized.get('tipos_beneficiario_normalized')}")
    logger.info(f"  NUTS code: {normalized.get('region_nuts')}")
