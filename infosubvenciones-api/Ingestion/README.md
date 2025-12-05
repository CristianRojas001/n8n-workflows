# Ingestion Pipeline

This directory contains the complete data ingestion pipeline for the `infosubvenciones-api` project. Its purpose is to fetch grant data from the InfoSubvenciones national database, process it, and store it in a PostgreSQL database for further analysis and use.

## Features

- **Robust API Client**: A resilient client for interacting with the InfoSubvenciones API, featuring error handling and retry logic.
- **Database Models**: SQLAlchemy models for storing grant data, including `pgvector` support for future semantic search capabilities.
- **Task-Based Architecture**: Uses Celery for defining and running asynchronous data fetching and processing tasks.
- **Structured Schemas**: Pydantic schemas for validating and parsing API responses.
- **Comprehensive Testing**: Scripts to test individual components and the end-to-end pipeline.

## Project Structure

```
Ingestion/
├── config/         # Configuration files (Database, Celery)
├── models/         # SQLAlchemy database models
├── schemas/        # Pydantic schemas for API data
├── scripts/        # Standalone scripts for testing, DB initialization, etc.
├── services/       # Core services (e.g., API client)
├── tasks/          # Celery tasks for fetching and processing data
├── .env.example    # Example environment variables file
└── requirements.txt  # Python dependencies
```

## Setup Instructions

Follow these steps to set up and run the ingestion pipeline.

### 1. Install Dependencies

First, install all required Python packages from `requirements.txt`. It is recommended to do this within a virtual environment.

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

The pipeline requires several environment variables, including database credentials and API keys.

1.  Create a `.env` file by copying the template:
    ```bash
    cp .env.example .env
    ```
2.  Edit the `.env` file and fill in the required values:
    - `DATABASE_URL`: The connection string for your PostgreSQL database.
    - `REDIS_URL`: The connection string for your Redis instance (used by Celery).
    - `GEMINI_API_KEY`: Your Google AI Studio API key.

### 3. Initialize the Database

Before running the pipeline for the first time, you must initialize the database schema. The `init_db.py` script creates all necessary tables and indexes.

```bash
python Ingestion/scripts/init_db.py
```
This script will check for required database extensions (like `pgvector`) and create the `convocatorias`, `staging_items`, `pdf_extractions`, and `embeddings` tables.

## Usage

Once set up, you can use the following scripts to run and monitor the pipeline.

### Test the Pipeline

To run a quick, end-to-end test of the fetching pipeline, use the `test_pipeline.py` script. This will fetch a small number of grants from the API and verify that they are correctly inserted into the database.

The `--direct` flag runs the test without needing a Celery worker, making it ideal for quick checks.

```bash
# Run a test fetching 10 items directly
python Ingestion/scripts/test_pipeline.py --items 10 --direct
```

### Export Database Statistics

To get a summary of the data currently in your database, run the `export_stats.py` script.

```bash
python Ingestion/scripts/export_stats.py
```

### Running with Celery (Asynchronous Processing)

For large-scale data fetching, you can run the tasks asynchronously using a Celery worker.

1.  **Start a Celery Worker**:
    Open a terminal and start a worker that listens to the `fetcher` queue.

    ```bash
    celery -A Ingestion.config.celery_app worker --loglevel=info -Q fetcher
    ```

2.  **Trigger a Task**:
    You can trigger tasks from a Python shell or another script. For example, to fetch 1000 grants:

    ```python
    from Ingestion.tasks.fetcher import fetch_batch
    fetch_batch.delay(finalidad="11", batch_id="culture_batch_01", total_items=1000)
    ```
