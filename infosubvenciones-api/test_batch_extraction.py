#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar la extracción de campos en múltiples PDFs.
Genera un reporte de qué tan bien funciona el extractor con diferentes formatos.
"""

import os
import json
from pathlib import Path
from extract_pdf_fields import SubvencionPDFParser


def test_batch_extraction(pdf_folder: str, max_pdfs: int = 10):
    """Procesa múltiples PDFs y genera un reporte."""

    parser = SubvencionPDFParser()
    pdf_path = Path(pdf_folder)

    if not pdf_path.exists():
        print(f"ERROR: Carpeta no encontrada: {pdf_folder}")
        return

    # Obtener lista de PDFs
    pdf_files = list(pdf_path.glob("*.pdf"))[:max_pdfs]

    print("=" * 80)
    print(f"PRUEBA DE EXTRACCION EN LOTE - {len(pdf_files)} PDFs")
    print("=" * 80)
    print()

    results = []
    success_count = 0

    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Procesando: {pdf_file.name}")
        print("-" * 80)

        try:
            data = parser.extract_all(str(pdf_file))

            # Analizar qué campos se extrajeron exitosamente
            extracted_fields = {
                'gastos_subvencionables': len(data.get('gastos_subvencionables', [])) > 0,
                'plazo_ejecucion': bool(data.get('plazo_ejecucion', {}).get('fecha_inicio')),
                'plazo_justificacion': bool(data.get('plazo_justificacion', {}).get('fecha_limite')),
                'forma_pago': bool(data.get('forma_pago', {}).get('tipo')),
                'compatibilidad': bool(data.get('compatibilidad', {}).get('compatible') is not None),
                'publicidad': bool(data.get('publicidad', {}).get('obligatorio') is not None),
                'garantias': bool(data.get('garantias', '')),
                'subcontratacion': bool(data.get('subcontratacion', ''))
            }

            # Contar campos exitosos
            successful_fields = sum(extracted_fields.values())
            total_fields = len(extracted_fields)
            success_rate = (successful_fields / total_fields) * 100

            # Mostrar resumen
            print(f"  Campos extraidos: {successful_fields}/{total_fields} ({success_rate:.1f}%)")

            for field, success in extracted_fields.items():
                status = "OK" if success else "MISS"
                print(f"    [{status}] {field}")

            # Guardar resultado
            result = {
                'file': pdf_file.name,
                'success_rate': success_rate,
                'fields': extracted_fields,
                'data': data
            }
            results.append(result)

            if success_rate > 50:
                success_count += 1

        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'file': pdf_file.name,
                'success_rate': 0,
                'error': str(e)
            })

    # Generar reporte final
    print("\n" + "=" * 80)
    print("REPORTE FINAL")
    print("=" * 80)

    avg_success_rate = sum(r.get('success_rate', 0) for r in results) / len(results) if results else 0

    print(f"\nPDFs procesados: {len(results)}")
    print(f"PDFs con >50% extraccion: {success_count}/{len(results)}")
    print(f"Tasa promedio de exito: {avg_success_rate:.1f}%")

    # Análisis por campo
    print("\nExtraccion por campo:")
    print("-" * 80)

    field_stats = {}
    for result in results:
        if 'fields' in result:
            for field, success in result['fields'].items():
                if field not in field_stats:
                    field_stats[field] = {'success': 0, 'total': 0}
                field_stats[field]['total'] += 1
                if success:
                    field_stats[field]['success'] += 1

    for field, stats in sorted(field_stats.items()):
        rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"  {field:30s}: {stats['success']:2d}/{stats['total']:2d} ({rate:5.1f}%)")

    # Guardar resultados completos
    output_file = "batch_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Resultados completos guardados en: {output_file}")

    # Mostrar PDFs con mejor y peor extracción
    if results:
        sorted_results = sorted([r for r in results if 'success_rate' in r],
                              key=lambda x: x.get('success_rate', 0),
                              reverse=True)

        print("\nMejores resultados:")
        for r in sorted_results[:3]:
            print(f"  {r['success_rate']:5.1f}% - {r['file']}")

        print("\nPeores resultados:")
        for r in sorted_results[-3:]:
            print(f"  {r['success_rate']:5.1f}% - {r['file']}")


def main():
    """Ejecutar prueba en lote."""
    pdf_folder = r"d:\IT workspace\infosubvenciones-api\relevant_pdfs"

    # Procesar primeros 10 PDFs
    test_batch_extraction(pdf_folder, max_pdfs=10)


if __name__ == "__main__":
    main()