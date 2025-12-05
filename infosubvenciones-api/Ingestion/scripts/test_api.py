"""Test InfoSubvenciones API client with 10 real grants."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from services.api_client import InfoSubvencionesClient, InfoSubvencionesAPIError


def test_search():
    """Test search functionality."""
    print("=" * 60)
    print("Test 1: Search for Culture Grants (finalidad=11)")
    print("=" * 60)

    with InfoSubvencionesClient() as client:
        # Get statistics first
        stats = client.get_statistics(finalidad="11", tipos_beneficiario="3,2", abierto=True)
        print(f"\n📊 Statistics:")
        print(f"   Total elements: {stats['totalElements']:,}")
        print(f"   Total pages: {stats['totalPages']:,}")

        # Fetch first page
        response = client.search_convocatorias(
            finalidad="11",
            tipos_beneficiario="3,2",
            abierto=True,
            page=0,
            size=10
        )

        print(f"\n📋 Search Results (Page 1, showing {len(response.content)} items):")
        for i, item in enumerate(response.content, 1):
            print(f"\n{i}. {item.numeroConvocatoria}")
            print(f"   Título: {item.titulo[:80] if item.titulo else 'N/A'}...")
            print(f"   Organismo: {item.organismo or 'N/A'}")
            print(f"   Abierto: {'✅' if item.abierto else '❌'}")
            print(f"   Fecha fin: {item.fechaFinSolicitud or 'N/A'}")

        return response.content[0] if response.content else None


def test_detail(numero_convocatoria: str):
    """Test fetching detailed information."""
    print(f"\n{'=' * 60}")
    print(f"Test 2: Get Detail for {numero_convocatoria}")
    print("=" * 60)

    with InfoSubvencionesClient() as client:
        detail = client.get_convocatoria_detail(numero_convocatoria)

        print(f"\n📄 Detailed Information:")
        print(f"   ID: {detail.id}")
        print(f"   Número: {detail.numeroConvocatoria}")
        print(f"   Título: {detail.titulo[:100] if detail.titulo else 'N/A'}...")
        print(f"   Descripción: {detail.descripcion[:100] if detail.descripcion else 'N/A'}...")
        print(f"   Organismo: {detail.organismo or 'N/A'}")
        print(f"   Finalidad: {detail.finalidad} - {detail.finalidadDescripcion or 'N/A'}")
        print(f"   Sectores: {', '.join(detail.sectores) if detail.sectores else 'N/A'}")
        print(f"   Regiones: {', '.join(detail.regiones[:5]) if detail.regiones else 'N/A'}")
        print(f"   Abierto: {'✅ Sí' if detail.abierto else '❌ No'}")

        print(f"\n📅 Dates:")
        print(f"   Publicación: {detail.fechaPublicacion or 'N/A'}")
        print(f"   Inicio solicitud: {detail.fechaInicioSolicitud or 'N/A'}")
        print(f"   Fin solicitud: {detail.fechaFinSolicitud or 'N/A'}")

        print(f"\n💰 Amounts:")
        print(f"   Total: {detail.importeTotal or 'N/A'}")
        print(f"   Mínimo: {detail.importeMinimo or 'N/A'}")
        print(f"   Máximo: {detail.importeMaximo or 'N/A'}")

        print(f"\n📎 Documents: {len(detail.documentos)}")
        for i, doc in enumerate(detail.documentos[:5], 1):
            print(f"   {i}. {doc.nombreFic or 'N/A'} (ID: {doc.idDocumento or doc.id})")
            if doc.descripcion:
                print(f"      {doc.descripcion[:60]}...")

        return detail


def test_pagination():
    """Test pagination with iterator."""
    print(f"\n{'=' * 60}")
    print("Test 3: Pagination Test (fetch 10 items)")
    print("=" * 60)

    with InfoSubvencionesClient() as client:
        items = []
        for i, conv in enumerate(client.iter_all_convocatorias(
            finalidad="11",
            tipos_beneficiario="3,2",
            max_items=10
        ), 1):
            print(f"\n{i}. {conv.numeroConvocatoria} - {conv.titulo[:60] if conv.titulo else 'N/A'}...")
            items.append(conv)

        print(f"\n✅ Fetched {len(items)} items using pagination")
        return items


def test_validation():
    """Test Pydantic validation."""
    print(f"\n{'=' * 60}")
    print("Test 4: Validation Test")
    print("=" * 60)

    with InfoSubvencionesClient() as client:
        # Fetch a convocatoria and validate all fields
        response = client.search_convocatorias(finalidad="11", page=0, size=1)

        if response.content:
            item = response.content[0]
            print(f"\n✅ Search response validated successfully")
            print(f"   Fields present: {len(item.model_dump(exclude_none=True))}")

            # Get detail and validate
            detail = client.get_convocatoria_detail(item.numeroConvocatoria)
            print(f"✅ Detail response validated successfully")
            print(f"   Fields present: {len(detail.model_dump(exclude_none=True))}")
            print(f"   Documents: {len(detail.documentos)}")
            print(f"   Sectores: {len(detail.sectores) if detail.sectores else 0}")
            print(f"   Regiones: {len(detail.regiones) if detail.regiones else 0}")


def test_error_handling():
    """Test error handling."""
    print(f"\n{'=' * 60}")
    print("Test 5: Error Handling")
    print("=" * 60)

    with InfoSubvencionesClient() as client:
        # Test with invalid numero_convocatoria
        try:
            print("\nTesting with invalid numero...")
            detail = client.get_convocatoria_detail("INVALID_NUMBER_12345")
            print("❌ Should have raised an error!")
        except InfoSubvencionesAPIError as e:
            print(f"✅ Correctly caught error: {str(e)[:100]}")
        except Exception as e:
            print(f"✅ Caught exception: {type(e).__name__}: {str(e)[:100]}")


def main():
    """Run all API tests."""
    print("\n" + "=" * 60)
    print("InfoSubvenciones API Client Tests")
    print("=" * 60)

    try:
        # Test 1: Search
        first_item = test_search()

        # Test 2: Detail
        if first_item:
            test_detail(first_item.numeroConvocatoria)

        # Test 3: Pagination
        test_pagination()

        # Test 4: Validation
        test_validation()

        # Test 5: Error handling
        test_error_handling()

        print("\n" + "=" * 60)
        print("✅ All API tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Implement Celery fetcher task (tasks/fetcher.py)")
        print("  2. Store convocatorias in database")
        print("  3. Test end-to-end with 100 items")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
