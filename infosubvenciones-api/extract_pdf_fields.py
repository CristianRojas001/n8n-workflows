#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extractor de campos críticos desde PDFs de subvenciones.

Extrae:
1. Gastos subvencionables
2. Requisitos de justificación
3. Plazos de ejecución
4. Términos de pago
5. Reglas de compatibilidad
6. Requisitos de publicidad
7. Garantías
8. Subcontratación
"""

import PyPDF2
import re
import json
from typing import Dict, List, Optional
from pathlib import Path


class SubvencionPDFParser:
    """Parser para extraer campos críticos de PDFs de subvenciones."""

    # Palabras clave para identificar secciones
    SECTIONS = {
        'gastos_subvencionables': [
            'gastos o partidas subvencionables',
            'gastos subvencionables',
            'partidas subvencionables',
            'conceptos subvencionables'
        ],
        'forma_justificacion': [
            'forma de justificación',
            'forma de justificacion',
            'justificación de la subvención',
            'documentación justificativa'
        ],
        'plazo_ejecucion': [
            'plazo para la realización',
            'plazo de ejecución',
            'periodo de ejecución',
            'realización de la actividad'
        ],
        'plazo_justificacion': [
            'plazo de justificación',
            'plazo para justificar',
            'plazo de presentación'
        ],
        'forma_pago': [
            'forma de realización del pago',
            'forma de pago',
            'modalidad de pago',
            'pago de la subvención'
        ],
        'compatibilidad': [
            'compatibilidad/incompatibilidad',
            'compatibilidad',
            'concurrencia',
            'otras ayudas'
        ],
        'publicidad': [
            'publicidad de la subvención',
            'requisitos de publicidad',
            'difusión',
            'imagen institucional'
        ],
        'garantias': [
            'exigencia de garantía',
            'garantías',
            'avales'
        ],
        'subcontratacion': [
            'subcontratación',
            'externalización'
        ]
    }

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrae texto completo del PDF."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
        return text

    def find_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """Encuentra una sección en el texto basándose en keywords."""
        text_lower = text.lower()

        for keyword in keywords:
            # Buscar la palabra clave
            idx = text_lower.find(keyword.lower())
            if idx != -1:
                # Extraer desde el keyword hasta el próximo título (todo en mayúsculas)
                # o hasta 1500 caracteres
                start = idx
                remaining = text[start:]

                # Buscar el siguiente título en mayúsculas (línea con muchas mayúsculas)
                lines = remaining.split('\n')
                content_lines = [lines[0]]  # Incluir título

                for i, line in enumerate(lines[1:], 1):
                    # Si encontramos un título nuevo (muchas mayúsculas), parar
                    if len(line) > 15 and sum(c.isupper() for c in line) > len(line) * 0.7:
                        break
                    content_lines.append(line)

                    # Límite de seguridad
                    if i > 50:
                        break

                return '\n'.join(content_lines).strip()

        return None

    def parse_gastos_subvencionables(self, text: str) -> List[str]:
        """Extrae la lista de gastos subvencionables."""
        if not text:
            return []

        gastos = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            # Buscar líneas que empiezan con -, •, *, o números
            if re.match(r'^[-•*]\s+', line) or re.match(r'^\d+[\.\)]\s+', line):
                gasto = re.sub(r'^[-•*\d\.\)]+\s*', '', line).strip()
                if len(gasto) > 10:  # Filtrar muy cortos
                    gastos.append(gasto)

        return gastos

    def parse_plazos(self, text: str) -> Dict[str, str]:
        """Extrae fechas y plazos."""
        if not text:
            return {}

        result = {'texto_completo': text}

        # Buscar formato "del DD de MES de YYYY al DD de MES de YYYY"
        range_pattern = r'del\s+(\d{1,2}\s+de\s+\w+\s+(?:de\s+)?\d{4})\s+al\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
        match = re.search(range_pattern, text, re.IGNORECASE)
        if match:
            result['fecha_inicio'] = match.group(1)
            result['fecha_fin'] = match.group(2)

        # Buscar "Hasta el DD de MES de YYYY"
        until_pattern = r'[Hh]asta\s+el\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
        match = re.search(until_pattern, text)
        if match:
            result['fecha_limite'] = match.group(1)

        return result

    def parse_forma_pago(self, text: str) -> Dict[str, any]:
        """Analiza forma de pago."""
        if not text:
            return {}

        result = {'texto_completo': text}
        text_lower = text.lower()

        # Tipo de pago
        if 'libramiento único' in text_lower or 'pago único' in text_lower:
            result['tipo'] = 'único'
        elif 'plazos' in text_lower:
            result['tipo'] = 'plazos'

        # Momento
        if 'anticipado' in text_lower or 'con carácter previo' in text_lower:
            result['momento'] = 'anticipado'
        elif 'tras justificación' in text_lower:
            result['momento'] = 'posterior'

        # Porcentaje de anticipo
        anticipo_match = re.search(r'(\d+)\s*%.*anticipo', text_lower)
        if anticipo_match:
            result['porcentaje_anticipo'] = int(anticipo_match.group(1))

        # Método
        if 'transferencia' in text_lower:
            result['metodo'] = 'transferencia'

        return result

    def parse_compatibilidad(self, text: str) -> Dict[str, any]:
        """Analiza compatibilidad con otras ayudas."""
        if not text:
            return {}

        result = {'texto_completo': text}
        text_lower = text.lower()

        # Determinar si es compatible
        if 'compatible con otras' in text_lower:
            result['compatible'] = True
        elif 'incompatible' in text_lower:
            result['compatible'] = False

        # Límite
        if 'no podrá superar' in text_lower or 'no supere el coste' in text_lower:
            result['limite'] = 'no_superar_coste_actividad'

        return result

    def parse_publicidad(self, text: str) -> Dict[str, any]:
        """Analiza requisitos de publicidad."""
        if not text:
            return {}

        result = {'texto_completo': text}
        text_lower = text.lower()

        result['obligatorio'] = 'deberá' in text_lower

        # Canales
        canales = []
        if 'página web' in text_lower or 'web' in text_lower:
            canales.append('web')
        if 'folleto' in text_lower:
            canales.append('folletos')
        if 'cartel' in text_lower:
            canales.append('carteles')
        if 'redes sociales' in text_lower:
            canales.append('redes_sociales')

        result['canales'] = canales
        result['requiere_logo'] = 'imagen institucional' in text_lower or 'logotipo' in text_lower

        return result

    def extract_all(self, pdf_path: str) -> Dict:
        """Extrae todos los campos del PDF."""
        print(f"Procesando: {pdf_path}")

        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {'error': 'No se pudo extraer texto del PDF'}

        result = {}

        # Extraer cada sección
        for section_name, keywords in self.SECTIONS.items():
            section_text = self.find_section(text, keywords)
            result[f'_raw_{section_name}'] = section_text

        # Parsear secciones específicas
        gastos_text = result.get('_raw_gastos_subvencionables', '')
        result['gastos_subvencionables'] = self.parse_gastos_subvencionables(gastos_text)

        plazo_ejec_text = result.get('_raw_plazo_ejecucion', '')
        result['plazo_ejecucion'] = self.parse_plazos(plazo_ejec_text)

        plazo_just_text = result.get('_raw_plazo_justificacion', '')
        result['plazo_justificacion'] = self.parse_plazos(plazo_just_text)

        pago_text = result.get('_raw_forma_pago', '')
        result['forma_pago'] = self.parse_forma_pago(pago_text)

        compat_text = result.get('_raw_compatibilidad', '')
        result['compatibilidad'] = self.parse_compatibilidad(compat_text)

        pub_text = result.get('_raw_publicidad', '')
        result['publicidad'] = self.parse_publicidad(pub_text)

        result['garantias'] = result.get('_raw_garantias', '')
        result['subcontratacion'] = result.get('_raw_subcontratacion', '')

        return result


def main():
    """Ejemplo de uso."""
    parser = SubvencionPDFParser()

    # Procesar el PDF de ejemplo
    pdf_path = r"d:\IT workspace\infosubvenciones-api\sample_871838_1362058.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return

    print("=" * 70)
    print("EXTRACTOR DE CAMPOS CRÍTICOS - PDF SUBVENCIONES")
    print("=" * 70)
    print()

    data = parser.extract_all(pdf_path)

    # Mostrar resultados
    print(">> GASTOS SUBVENCIONABLES:")
    print("-" * 70)
    for i, gasto in enumerate(data.get('gastos_subvencionables', []), 1):
        print(f"  {i}. {gasto}")

    print("\n>> PLAZO DE EJECUCION:")
    print("-" * 70)
    plazo_ejec = data.get('plazo_ejecucion', {})
    if 'fecha_inicio' in plazo_ejec:
        print(f"  Inicio: {plazo_ejec['fecha_inicio']}")
        print(f"  Fin: {plazo_ejec['fecha_fin']}")
    else:
        print(f"  {plazo_ejec.get('texto_completo', 'No encontrado')[:200]}...")

    print("\n>> PLAZO DE JUSTIFICACION:")
    print("-" * 70)
    plazo_just = data.get('plazo_justificacion', {})
    if 'fecha_limite' in plazo_just:
        print(f"  Hasta: {plazo_just['fecha_limite']}")
    else:
        print(f"  {plazo_just.get('texto_completo', 'No encontrado')[:200]}...")

    print("\n>> FORMA DE PAGO:")
    print("-" * 70)
    pago = data.get('forma_pago', {})
    if 'tipo' in pago:
        print(f"  Tipo: {pago.get('tipo', 'N/A')}")
        print(f"  Momento: {pago.get('momento', 'N/A')}")
        print(f"  Metodo: {pago.get('metodo', 'N/A')}")
    else:
        print(f"  {pago.get('texto_completo', 'No encontrado')[:200]}...")

    print("\n>> COMPATIBILIDAD:")
    print("-" * 70)
    compat = data.get('compatibilidad', {})
    if 'compatible' in compat:
        print(f"  Compatible: {'Si' if compat['compatible'] else 'No'}")
        print(f"  Limite: {compat.get('limite', 'N/A')}")
    else:
        print(f"  {compat.get('texto_completo', 'No encontrado')[:200]}...")

    print("\n>> PUBLICIDAD:")
    print("-" * 70)
    pub = data.get('publicidad', {})
    if 'obligatorio' in pub:
        print(f"  Obligatorio: {'Si' if pub['obligatorio'] else 'No'}")
        print(f"  Canales: {', '.join(pub.get('canales', []))}")
        print(f"  Requiere logo: {'Si' if pub.get('requiere_logo') else 'No'}")
    else:
        print(f"  {pub.get('texto_completo', 'No encontrado')[:200]}...")

    print("\n" + "=" * 70)

    # Guardar resultado completo en JSON
    output_file = "extracted_pdf_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Datos completos guardados en: {output_file}")


if __name__ == "__main__":
    main()