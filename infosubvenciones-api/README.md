# InfoSubvenciones API Project

## Overview

The `infosubvenciones-api` project aims to create a comprehensive, searchable, and AI-enriched database of public grants from Spain's *Sistema Nacional de Publicidad de Subvenciones y Ayudas Públicas* (InfoSubvenciones).

The core goal is to transform the raw, often complex data from the official portal into a clean, structured format. By leveraging AI models, the project will generate concise summaries and vector embeddings for each grant, enabling powerful semantic search and data analysis capabilities that are not possible with the source portal.

## Key Components

This project is divided into several key components:

1.  **Ingestion Pipeline (`/Ingestion`)**: This is the heart of the data collection system. It is a Python-based pipeline responsible for:
    - Fetching grant data from the official InfoSubvenciones API.
    - Cleaning and structuring the raw data.
    - Storing the data in a PostgreSQL database.
    - Orchestrating the AI-powered processing stages (summarization, embedding).

2.  **Django REST API (Future)**: A RESTful API will be developed to expose the enriched grant data to other applications. It will provide endpoints for searching, filtering, and retrieving grant information.

3.  **Frontend Application (Future)**: A web-based user interface will be built to provide an intuitive way for users to search, explore, and analyze the grant data.

## Core Technologies

- **Backend**: Python
- **Data Fetching & Processing**: Celery, Redis
- **Database**: PostgreSQL with `pgvector` for vector similarity search
- **AI Models**: Google Gemini for summarization and Google's embedding models.
- **Future API**: Django REST Framework
- **Containerization**: Docker

## Getting Started

To get the project running, start with the Ingestion Pipeline, as it is the foundation for all other components.

For detailed instructions on setting up the database, configuring the environment, and running the data fetching tasks, please refer to the pipeline's specific documentation:

**[>> Go to Ingestion Pipeline README](./Ingestion/README.md)**
