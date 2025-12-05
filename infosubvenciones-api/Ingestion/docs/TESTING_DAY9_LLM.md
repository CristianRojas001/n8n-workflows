# Testing Instructions for Day 9-10: LLM Processing with Gemini

## Overview
Test the Gemini LLM integration for generating Spanish summaries and extracting structured fields from grant PDF text. The code is complete and ready for testing.

---

## Prerequisites

1. **Gemini API Key**: Ensure `GEMINI_API_KEY` is set in `.env` file
2. **PDF Extractions**: At least 5 PDF extractions from Day 8 (with `extraction_model='pymupdf'`)
3. **Dependencies**: Install `google-generativeai` package

```bash
cd "d:\IT workspace\infosubvenciones-api\Ingestion"
pip install google-generativeai
```

---

## Test Plan

### **Test 1: Verify Imports and Gemini Configuration**

```bash
# Test Gemini client import
python -c "from services.gemini_client import GeminiClient; print('✓ GeminiClient')"

# Test LLM processor import
python -c "from tasks.llm_processor import process_with_llm; print('✓ LLM processor')"

# Test Gemini API key
python -c "
import sys
sys.path.insert(0, '.')
from config.settings import get_settings
s = get_settings()
print(f'✓ Gemini API key: {s.gemini_api_key[:10]}...')
print(f'✓ Gemini model: {s.gemini_model}')
"
```

**Expected**: All imports succeed, Gemini API key loaded

---

### **Test 2: Simple Gemini Client Test**

Test the Gemini client directly with sample text:

```bash
python -c "
import sys
sys.path.insert(0, '.')
from services.gemini_client import GeminiClient

# Sample Spanish grant text
test_text = '''
ORDEN de 15 de enero de 2024 por la que se convocan ayudas para proyectos culturales.

Artículo 1. Objeto
La presente orden tiene por objeto convocar ayudas destinadas a la financiación de proyectos culturales destinados a promover la cultura española.

Artículo 2. Beneficiarios
Podrán ser beneficiarios de estas ayudas las entidades sin ánimo de lucro que desarrollen actividades culturales.

Artículo 3. Cuantía
La cuantía máxima de la ayuda será de 50.000 euros por proyecto. La cuantía mínima será de 5.000 euros.

Artículo 4. Plazo de ejecución
Los proyectos deberán ejecutarse en un plazo máximo de 12 meses desde la fecha de concesión.

Artículo 5. Justificación
Los beneficiarios deberán presentar una memoria justificativa en el plazo de 3 meses tras finalizar el proyecto.
'''

client = GeminiClient()
summary, fields, confidence = client.process_pdf_text(test_text, 'TEST-001')

print('\n=== SUMMARY ===')
print(summary[:500] + '...')

print('\n=== EXTRACTED FIELDS ===')
import json
print(json.dumps(fields, indent=2, ensure_ascii=False))

print(f'\n=== CONFIDENCE: {confidence:.2f} ===')
"
```

**Expected Results**:
- ✅ Summary generated in Spanish (~200-500 words)
- ✅ Fields extracted as JSON (cuantia_max=50000, cuantia_min=5000, etc.)
- ✅ Confidence score between 0.7-0.95
- ✅ Summary mentions: beneficiarios, cuantía, plazo

---

### **Test 3: Single PDF LLM Processing (Full Pipeline)**

Run the test script to process one real PDF:

```bash
python scripts/test_llm_processor.py
```

This will run 4 tests:
1. Process single PDF extraction with Gemini
2. Batch processing (3 extractions)
3. Statistics reporting
4. Field quality analysis

**Expected Results**:

**Test 1 - Single Processing**:
- ✅ Finds a PDF extraction with `extraction_model='pymupdf'`
- ✅ Reads markdown file successfully
- ✅ Calls Gemini API (may take 10-30 seconds)
- ✅ Generates Spanish summary
- ✅ Extracts 5-13 structured fields
- ✅ Updates `pdf_extractions` table:
  - `extraction_model` → value of `GEMINI_MODEL` (default `gemini-2.5-flash-lite`)
  - `extraction_confidence` → 0.7-0.95
  - Populated fields: gastos_subvencionables, cuantia_subvencion, plazos, etc.
- ✅ Summary stored in `raw_gastos_subvencionables` (temporary)
- ℹ️ Modify `GEMINI_MODEL` in `Ingestion/.env` to switch Gemini versions without touching the code.

**Test 2 - Batch Processing**:
- ✅ Queues 3 LLM tasks
- ✅ Returns task group ID

**Test 3 - Statistics**:
- ✅ Shows: total extractions, LLM processed, pending, avg confidence
- ✅ Completion rate calculated

**Test 4 - Field Quality**:
- ✅ Displays populated fields for each processed extraction
- ✅ Shows confidence scores

---

### **Test 4: Process Multiple PDFs (Real Data)**

Process 5 PDFs with Gemini:

```bash
python -c "
import sys
sys.path.insert(0, '.')
from tasks.llm_processor import process_with_llm, get_llm_processing_stats
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from sqlalchemy import select

db = next(get_db())

# Get 5 unprocessed extractions
stmt = (
    select(PDFExtraction)
    .where(PDFExtraction.extraction_model == 'pymupdf')
    .where(PDFExtraction.pdf_word_count > 0)
    .limit(5)
)

extractions = db.execute(stmt).scalars().all()

print(f'Found {len(extractions)} extractions to process\n')

for extraction in extractions:
    print(f'Processing: {extraction.numero_convocatoria}...')
    result = process_with_llm(extraction.id)

    if result['success']:
        print(f'  ✓ Summary: {result.get(\"summary_length\")} chars')
        print(f'  ✓ Fields: {result.get(\"fields_extracted\")}')
        print(f'  ✓ Confidence: {result.get(\"confidence\", 0):.2f}\n')
    else:
        print(f'  ✗ Error: {result.get(\"error\")}\n')

db.close()

# Show final stats
stats = get_llm_processing_stats()
print(f'\n=== FINAL STATS ===')
print(f'Total processed: {stats.get(\"llm_processed\", 0)}')
print(f'Avg confidence: {stats.get(\"avg_confidence\", 0):.2f}')
"
```

**Expected Results**:
- ✅ 5 PDFs processed successfully (may take 2-5 minutes total)
- ✅ Each generates Spanish summary
- ✅ Each extracts 5-13 fields
- ✅ Confidence scores 0.7-0.95
- ✅ No API errors (if errors occur, check Gemini API key & quota)

---

### **Test 5: Verify Database Updates**

Check that LLM results are stored correctly:

```bash
python -c "
import sys
sys.path.insert(0, '.')
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from sqlalchemy import select

db = next(get_db())

# Get LLM-processed extractions
stmt = (
    select(PDFExtraction)
    .where(PDFExtraction.extraction_model == '<GEMINI_MODEL>')
    .limit(3)
)

extractions = db.execute(stmt).scalars().all()

print(f'LLM-processed extractions: {len(extractions)}\n')

for ext in extractions:
    print(f'=== {ext.numero_convocatoria} ===')
    print(f'Confidence: {ext.extraction_confidence:.2f}')
    print(f'Cuantía: {ext.cuantia_subvencion}')
    print(f'Cuantía min: {ext.cuantia_min}')
    print(f'Cuantía max: {ext.cuantia_max}')
    print(f'Plazo ejecución: {ext.plazo_ejecucion}')
    print(f'Plazo justificación: {ext.plazo_justificacion}')
    print(f'Forma pago: {ext.forma_pago}')

    # Show summary preview (stored in raw_gastos_subvencionables)
    if ext.raw_gastos_subvencionables:
        summary = ext.raw_gastos_subvencionables.replace('SUMMARY:\n', '')
        print(f'\nSummary preview (first 300 chars):')
        print(summary[:300] + '...\n')

db.close()
"
```

**Expected Results**:
- ✅ At least 3 extractions with `extraction_model=<GEMINI_MODEL>`
- ✅ `extraction_confidence` populated (0.7-0.95)
- ✅ Financial fields populated (cuantía, intensidad)
- ✅ Deadline fields populated (plazos)
- ✅ Summary visible in raw_gastos_subvencionables

---

### **Test 6: Quality Checks**

Verify summary quality and field accuracy:

```bash
python -c "
import sys
sys.path.insert(0, '.')
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from sqlalchemy import select

db = next(get_db())

stmt = select(PDFExtraction).where(
    PDFExtraction.extraction_model == '<GEMINI_MODEL>'
).limit(1)

ext = db.execute(stmt).scalar_one_or_none()

if ext:
    # Check summary
    summary = ext.raw_gastos_subvencionables.replace('SUMMARY:\n', '') if ext.raw_gastos_subvencionables else ''

    print('=== SUMMARY QUALITY CHECKS ===')
    print(f'Length: {len(summary)} chars')
    print(f'Word count: ~{len(summary.split())} words')

    # Check for Spanish
    spanish_keywords = ['ayuda', 'subvención', 'beneficiario', 'euros', 'plazo']
    found = sum(1 for kw in spanish_keywords if kw in summary.lower())
    print(f'Spanish keywords found: {found}/{len(spanish_keywords)}')

    # Check for key info
    print(f'Has cuantía info: {\"cuantía\" in summary.lower() or \"importe\" in summary.lower()}')
    print(f'Has beneficiarios info: {\"beneficiario\" in summary.lower()}')
    print(f'Has plazo info: {\"plazo\" in summary.lower()}')

    print(f'\nFull summary:\n{summary}')

    # Check extracted fields
    print('\n=== EXTRACTED FIELDS ===')
    field_names = ['gastos_subvencionables', 'cuantia_subvencion', 'plazo_ejecucion',
                   'plazo_justificacion', 'forma_pago']

    for field in field_names:
        value = getattr(ext, field, None)
        if value:
            print(f'{field}: {str(value)[:100]}...')

db.close()
"
```

**Expected Results**:
- ✅ Summary is in Spanish
- ✅ Summary is 200-3000 chars (~50-500 words)
- ✅ Contains Spanish keywords (ayuda, subvención, etc.)
- ✅ Mentions key information (cuantía, beneficiarios, plazos)
- ✅ Fields contain relevant extracted data

---

## Success Criteria

All tests pass with:
- [x] Gemini API connection working
- [x] Summaries generated in Spanish
- [x] Summaries are coherent and accurate (no hallucinations)
- [x] Structured fields extracted (5-13 per PDF)
- [x] Confidence scores reasonable (0.7-0.95)
- [x] Database records updated correctly
- [x] No API errors or rate limiting

---

## Common Issues & Troubleshooting

**Issue 1: `google.generativeai` import error**
- **Solution**: `pip install google-generativeai`

**Issue 2: Gemini API key invalid**
- **Solution**: Check `.env` file has correct `GEMINI_API_KEY`
- Get key from: https://aistudio.google.com/app/apikey

**Issue 3: API rate limiting (429 errors)**
- **Solution**: Gemini free tier has limits (50 requests/day)
- Use retry logic (already implemented with tenacity)
- Wait 1-2 minutes between batches

**Issue 4: Empty summaries**
- **Solution**: Check PDF text length (need >50 chars)
- Check markdown file exists and is readable

**Issue 5: JSON parse errors**
- **Expected**: Some PDFs may not have all fields
- The code handles missing fields gracefully (returns empty dict)

**Issue 6: Slow processing**
- **Expected**: Each API call takes 5-15 seconds
- Processing 5 PDFs sequentially = 25-75 seconds
- Use batch processing for parallel execution

---

## Reporting Results

Please report:

1. **Test 1-2**: Import success and simple Gemini test
   - Summary preview (first 200 chars)
   - Fields extracted (list the keys)
   - Confidence score

2. **Test 3**: Full pipeline test results
   - Number of PDFs processed
   - Success/failure for each test
   - Any error messages

3. **Test 4**: Batch processing
   - Number successfully processed
   - Summary lengths
   - Field counts
   - Confidence scores

4. **Test 5-6**: Database & quality verification
   - Sample summary (full text for 1 PDF)
   - Sample extracted fields (for 1 PDF)
   - Spanish language confirmed
   - Field accuracy assessment

---

## Next Steps After Testing

Once testing is complete:
1. Verify Day 9-10 success criteria met
2. Ready to proceed to Day 11-12: Embeddings & Vector Search

---

**Files to Test**:
- [services/gemini_client.py](../services/gemini_client.py) - Gemini LLM integration
- [tasks/llm_processor.py](../tasks/llm_processor.py) - LLM Celery tasks
- [scripts/test_llm_processor.py](../scripts/test_llm_processor.py) - Test suite
