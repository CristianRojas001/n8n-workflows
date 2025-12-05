# RAG Pipeline Template

> Purpose: capture every moving part in your retrieval-augmented generation system so assistants can wire features consistently and avoid missing dependencies.

## 1. Use Case Summary
- **Primary user tasks**: _What questions/actions rely on RAG?_
- **Domain sources**: _Regs, manuals, PDFs, DB tables, APIs, etc._
- **Response format requirements**: _Citations, JSON schema, Markdown, etc._

## 2. Data Ingestion
- **Sources & frequency**:
  - _Source name_ – _Pull vs push_, _cron/Celery schedule_, _expected volume_.
- **Parsing/normalization**:
  - _Tools used (BeautifulSoup, pdfminer, custom parser)_.
  - _Fields extracted (title, section, content, metadata)._
- **Storage targets**:
  - _Relational DB tables, blob storage, search index, vector store._
- **Quality checks**:
  - _Validation scripts, deduping strategy, alerting._

## 3. Indexing & Retrieval Store
- **Search engine**: _OpenSearch, Elastic, Pinecone, etc. Version + plugins._
- **Index schema**:
  - Fields: `_id, title, section, content, embeddings, metadata`.
  - Analyzers/tokenizers: _Standard, n-gram, custom language analyzers._
- **Chunking strategy**:
  - Chunk size, overlap, heuristics (per article, per heading, per clause).
- **Reranking**:
  - _Model/heuristics used (e.g., semantic reranker, citation weighting)._ 

## 4. Embeddings & Vector Store
- **Embedding model**: _Provider + dimensions + cost considerations._
- **Vector DB**: _pgvector, Pinecone, FAISS, etc._
- **Fields stored**: _Query text, response text, metadata, TTL._
- **Usage**: _Similarity search, caching, personalization._

## 5. LLM Invocation
- **Provider/model**: _DeepSeek, OpenAI GPT-4o, Anthropic Claude, local model._
- **Prompt architecture**:
  - System prompt template: _Where you insert retrieval snippets and guardrails._
  - Message sequence: _System → retrieved context → user query (with optional chat history)._
- **Streaming/latency**:
  - _Do you stream tokens? Timeout thresholds? Retry policy?_
- **Cost controls**: _Max tokens, caching, fallback models._

## 6. Response Post-processing
- **Citation formatting**: _How to map retrieved docs to inline citations._
- **Validation**:
  - _Automated claim check? Cross-source verification?_
- **Semantic cache**:
  - _When to store conversation pairs; TTL; eviction policy._
- **Moderation/filters**: _Profanity, PII detection, guardrail hooks._

## 7. Monitoring & Metrics
- **Operational metrics**: _Ingestion lag, search latency, LLM latency, token usage._
- **Quality metrics**: _Precision@k, citation accuracy, user feedback loops._
- **Alerting**: _Conditions, channels, on-call rotation._

## 8. Open Questions / TODOs
- _Use this to track unresolved design choices—embedding provider, vector DB sizing, cost limits, etc._
