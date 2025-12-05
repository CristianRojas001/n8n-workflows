# LLM Processing Deduplication

## Overview

The LLM processor has built-in deduplication to avoid reprocessing PDFs that have already been extracted. This saves API costs and processing time.

## How Deduplication Works

**Location:** [Ingestion/tasks/llm_processor.py:84-93](../Ingestion/tasks/llm_processor.py)

```python
# Check if already processed by LLM (skip if force_reprocess is True)
target_model = settings.gemini_model
if extraction.extraction_model == target_model and not force_reprocess:
    logger.info(f"Extraction {extraction_id} already processed with LLM, skipping")
    return {
        'success': True,
        'skipped': True,
        'reason': 'Already processed with LLM',
        'numero_convocatoria': numero
    }
```

The system checks if `pdf_extractions.extraction_model` matches the current model in settings (`gemini-2.5-flash-lite`). If it matches, the extraction is skipped.

## Bypassing Deduplication for Testing/Reprocessing

### Method 1: Using `force_reprocess` Parameter (Recommended)

The `process_with_llm` task now accepts a `force_reprocess` parameter:

```python
from tasks.llm_processor import process_with_llm

# Normal processing (respects deduplication)
result = process_with_llm(extraction_id=123)

# Force reprocessing (bypasses deduplication)
result = process_with_llm(extraction_id=123, force_reprocess=True)
```

### Method 2: Using Test Script

The test script **always bypasses deduplication** automatically:

```bash
# Dry run (doesn't save)
python scripts/test_enhanced_extraction.py 870434

# Save to database (overwrites existing data)
python scripts/test_enhanced_extraction.py 870434 --save
```

The script directly calls the Gemini client and field normalizer, so it always reprocesses regardless of the `extraction_model` value.

### Method 3: Manual Database Reset (For Batch Reprocessing)

To reprocess multiple extractions, reset their `extraction_model` field:

```sql
-- Reset specific extraction
UPDATE pdf_extractions
SET extraction_model = 'pymupdf'
WHERE numero_convocatoria = '870434';

-- Reset all extractions (use with caution!)
UPDATE pdf_extractions
SET extraction_model = 'pymupdf';

-- Reset extractions missing Phase 2 fields
UPDATE pdf_extractions
SET extraction_model = 'pymupdf'
WHERE raw_objeto IS NULL;
```

After resetting, run the batch processor:

```bash
python -c "from tasks.llm_processor import process_llm_batch; process_llm_batch(limit=10)"
```

## Use Cases

### Testing New Field Extractions

When you add new fields to the extraction (like Phase 2 fields), use the test script to verify extraction on a sample without affecting production:

```bash
# Test without saving
python scripts/test_enhanced_extraction.py 870434

# Save when satisfied
python scripts/test_enhanced_extraction.py 870434 --save
```

### Reprocessing After Prompt Changes

If you update the Gemini prompt in `services/gemini_client.py`, you need to reprocess existing extractions to get the new fields:

**Option A: Test Script (Individual)**
```bash
python scripts/test_enhanced_extraction.py 870434 --save
```

**Option B: Database Reset + Batch (Multiple)**
```sql
UPDATE pdf_extractions SET extraction_model = 'pymupdf'
WHERE id IN (SELECT id FROM pdf_extractions LIMIT 10);
```
```bash
python -c "from tasks.llm_processor import process_llm_batch; process_llm_batch(limit=10)"
```

### Reprocessing After Normalization Rule Changes

If you only changed normalization rules in `services/field_normalizer.py` (not the LLM prompt), you can reprocess without calling the LLM:

```python
# Create a script to update normalizations only
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from services.field_normalizer import FieldNormalizer
from sqlalchemy import select

db = next(get_db())
normalizer = FieldNormalizer()

# Get extraction
stmt = select(PDFExtraction).where(PDFExtraction.numero_convocatoria == '870434')
extraction = db.execute(stmt).scalar_one()

# Re-normalize existing raw fields
fields = {
    'sectores_raw': extraction.sectores_raw,
    'tipos_beneficiario_raw': extraction.tipos_beneficiario_raw,
    'instrumentos_raw': extraction.instrumentos_raw,
    'region_mencionada': extraction.region_mencionada,
    # ... other raw fields
}

normalized = normalizer.normalize_all_fields(fields)

# Update normalized fields
extraction.sectores_inferidos = normalized.get('sectores_inferidos')
extraction.tipos_beneficiario_normalized = normalized.get('tipos_beneficiario_normalized')
# ... other normalized fields

db.commit()
```

## Current Status

As of 2025-12-03, the database has:

- **18 total PDF extractions**
- **0% Phase 2 field population** (all null)
- **Reason:** All extractions were processed before Phase 2 fields were added
- **Solution:** Use test script with `--save` or reset `extraction_model` to reprocess

## Important Notes

1. **API Costs:** Reprocessing calls the Gemini API, which incurs costs. Only reprocess when necessary.

2. **Test Script vs Celery Task:**
   - Test script: Synchronous, bypasses deduplication, good for testing individual items
   - Celery task: Asynchronous, respects deduplication (unless `force_reprocess=True`), good for batch processing

3. **Deduplication is Active by Default:** This is intentional to prevent accidental reprocessing and API cost overruns.

4. **When Phase 2 Fields are Null:**
   - If the PDF doesn't contain that information → Expected behavior
   - If the PDF contains it but LLM didn't extract → Reprocess with `force_reprocess=True`
   - If all extractions have null Phase 2 fields → They were processed before Phase 2 was implemented

## See Also

- [Missing Fields vs What CAN Be Extracted From the PDF.md](Missing%20Fields%20vs%20What%20CAN%20Be%20Extracted%20From%20the%20PDF.md) - List of all extractable fields
- [Ingestion/services/gemini_client.py](../Ingestion/services/gemini_client.py) - LLM extraction prompt (78 fields)
- [Ingestion/services/field_normalizer.py](../Ingestion/services/field_normalizer.py) - Field normalization rules
- [Ingestion/tasks/llm_processor.py](../Ingestion/tasks/llm_processor.py) - Main processing logic
