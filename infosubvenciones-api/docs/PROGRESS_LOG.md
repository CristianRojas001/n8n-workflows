# Project Progress Log

This document tracks major milestones, decisions, and progress on a weekly basis.

---

## **Week 1: Foundation (Dec 1 - Dec 7, 2025)**

**Status: COMPLETED**

This week focused on establishing the foundational infrastructure and code for the data ingestion pipeline. The primary goal was to ensure we could successfully connect to the API, fetch data, and store it in a structured database. The project is ahead of schedule, with all core components for initial data fetching completed and tested. All sprint goals were successfully met.

### **Key Accomplishments**

- **Infrastructure Verified**: Confirmed availability and versions of Python, PostgreSQL, and Redis.
- **Project Structure Created**: The `Ingestion` pipeline project was scaffolded with a logical structure (`config`, `models`, `services`, `tasks`, `scripts`).
- **Database Schema Implemented**: All initial database models (`Convocatoria`, `StagingItem`, `PDFExtraction`, `Embedding`) were created and the database was initialized using the `init_db.py` script.
- **API Client Developed**: A robust client for the InfoSubvenciones API was built, including pagination, error handling, and Pydantic validation schemas.
- **Fetcher Task Implemented**: A Celery task (`fetch_convocatorias`) was created to fetch grants and store them in the database, complete with duplicate detection.
- **Initial Testing Completed**: The fetcher was successfully tested by fetching and storing 50 real grant records.
- **Model Configuration Updated**: Switched the default configuration from OpenAI models to Google's Gemini (`gemini-2.5-flash-lite`) and embedding models (`text-embedding-google-free`) with the correct dimensions (768).
- **Core Documentation Written**: Created `README.md` files for both the root project and the `Ingestion` pipeline, and created test/utility scripts (`test_pipeline.py`, `export_stats.py`).
- **Final End-to-End Test Passed**: Successfully ran the `test_pipeline.py` script, confirming the entire fetch-and-store process works as expected.

### **Decisions & Learnings**

- **Technology Choices**:
  - **Database**: Decided to use PostgreSQL with the `pgvector` extension instead of a separate vector database to simplify architecture.
  - **API Framework**: Confirmed Django REST Framework will be used for the future API to align with existing projects.
  - **AI Models**: Switched to Google's Gemini and embedding models as per requirements.
- **API Insights**:
  - The InfoSubvenciones API has significant data quality issues, with many `null` or `N/A` values. This is an expected behavior of the source.
  - The scale of available data is larger than initially estimated (>119,000 grants for "culture" alone).

### **Blockers Resolved**

- **API Keys**: The required API keys for Google Gemini were provided and configured in the `.env` file.

### **Next Steps (Week 2 Plan)**

The focus for Week 2 will be on processing the data that is now being fetched. The main priorities are:

1.  **PDF Downloader**: Implement a service to download the PDF documents associated with each grant.
2.  **PDF Processing**: Begin work on extracting text and structured data from the downloaded PDFs.
3.  **Summarization & Embedding**: Create the pipeline tasks that will:
    - Use Gemini to generate summaries from the extracted PDF text.
    - Use Google's embedding model to create vector embeddings from the summaries.
    - Store this enriched data in the `embeddings` table.