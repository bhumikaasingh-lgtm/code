# 🏗️ System Architecture

This document explains the technical architecture of the RAG system.

---

## 📊 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER                             │
│              (Web Browser)                          │
└────────────────────┬────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────┐
│              STREAMLIT FRONTEND                     │
│           (frontend.py - Port 8501)                 │
│                                                     │
│  • Query input interface                            │
│  • Filter controls (author, status)                 │
│  • Search parameter controls (alpha, top_k)         │
│  • Results display with markdown                    │
└────────────────────┬────────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────────┐
│               FASTAPI BACKEND                       │
│           (backend.py - Port 8000)                  │
│                                                     │
│  Endpoints:                                         │
│  • POST /search - Hybrid search + generation        │
│  • GET /health - Health check                       │
│  • GET /stats - Database statistics                 │
│  • GET /authors - List all authors                  │
│  • GET /statuses - List all statuses                │
└────────┬──────────────────────┬─────────────────────┘
         │                      │
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│  EMBEDDING      │    │  LLM GENERATOR  │
│  MODEL          │    │                 │
│                 │    │  • Llama 3 or   │
│  • e5-large-v2  │    │  • GPT-4        │
│  • Query: 🔍    │    │                 │
│  • Docs: 📄     │    │  Generates      │
│  • 1024-dim     │    │  final answers  │
└─────────────────┘    └─────────────────┘
         │
         │ Vector queries
         ▼
┌─────────────────────────────────────────────────────┐
│            WEAVIATE VECTOR DATABASE                 │
│              (Port 8080)                            │
│                                                     │
│  Collection: IssueChunk                             │
│  • Text content                                     │
│  • Vector embeddings (1024-dim)                     │
│  • Metadata (author, status, etc.)                  │
│                                                     │
│  Search Capabilities:                               │
│  • BM25 keyword search                              │
│  • Vector similarity search                         │
│  • Hybrid search (α-balanced)                       │
│  • Metadata filtering                               │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### Setup Phase (One-Time)

```
CSV File (all_issues_for_test.csv)
    │
    ├─> Document Processor (document_processor.py)
    │   ├─> Load CSV with pandas
    │   ├─> Parse rows into issues
    │   ├─> Chunk each issue into sections
    │   │   ├─> Subject chunk
    │   │   ├─> Description chunks (with overlap)
    │   │   └─> Combined context chunk
    │   └─> Add metadata (author, status, etc.)
    │
    ├─> Embedding Model (embeddings.py)
    │   ├─> Load e5-large-v2 from HuggingFace
    │   ├─> Add "passage:" prefix
    │   ├─> Batch encode (32 chunks at a time)
    │   ├─> Generate 1024-dim vectors
    │   └─> Normalize vectors
    │
    └─> Weaviate Client (weaviate_client.py)
        ├─> Connect to Weaviate
        ├─> Create schema/collection
        ├─> Batch insert chunks + vectors
        └─> Build indexes
```

### Query Phase (Real-Time)

```
User Query: "What API features did Adnan work on?"
    │
    ├─> Frontend (frontend.py)
    │   ├─> Capture query text
    │   ├─> Get filter selections (author, status)
    │   ├─> Get search params (alpha, top_k)
    │   └─> Send POST /search to backend
    │
    ├─> Backend (backend.py)
    │   │
    │   ├─> Embedding Model
    │   │   ├─> Add "query:" prefix
    │   │   ├─> Encode to 1024-dim vector
    │   │   └─> Return query embedding
    │   │
    │   ├─> Weaviate Client
    │   │   ├─> Build filter object from params
    │   │   ├─> Perform hybrid search
    │   │   │   ├─> BM25 on text (α=0.5)
    │   │   │   ├─> Vector similarity (α=0.5)
    │   │   │   └─> Combine scores
    │   │   ├─> Apply filters (author, status)
    │   │   ├─> Return top_k results
    │   │   └─> Include scores and metadata
    │   │
    │   └─> LLM Generator
    │       ├─> Format prompt with contexts
    │       ├─> Include retrieved chunks
    │       ├─> Generate answer
    │       │   ├─> If Llama 3: Local inference
    │       │   └─> If GPT-4: OpenAI API call
    │       └─> Return formatted answer
    │
    └─> Frontend
        ├─> Display generated answer
        ├─> Show source documents
        ├─> Display metadata (scores, authors)
        └─> Format with markdown
```

---

## 📦 Component Details

### 1. Document Processor (`document_processor.py`)

**Purpose**: Convert raw CSV into searchable chunks

**Key Classes**:
- `DocumentChunk`: Data class for chunk representation
- `DocumentProcessor`: Main processing logic

**Algorithm**:
```python
For each issue:
    1. Extract metadata (id, author, status)
    2. Create subject chunk (always whole)
    3. Create description chunks:
       - Split by max_size (512 chars)
       - Add overlap (50 chars)
       - Break at sentence boundaries
    4. Create combined chunk (full context, truncated)
    5. Attach metadata to all chunks
```

**Output**: List of DocumentChunk objects

### 2. Embedding Model (`embeddings.py`)

**Purpose**: Convert text to vector representations

**Model**: `intfloat/e5-large-v2`
- Dimensions: 1024
- Context window: 512 tokens
- Normalized embeddings

**Key Methods**:
- `encode_query(query)`: Adds "query:" prefix
- `encode_documents(docs)`: Adds "passage:" prefix, batches

**Why e5-large-v2?**
- State-of-the-art performance
- Good balance of speed/quality
- Works well for technical text
- Open source (free)

### 3. Weaviate Client (`weaviate_client.py`)

**Purpose**: Vector database operations

**Schema**:
```python
Collection: IssueChunk
Properties:
  - chunk_id: TEXT (unique identifier)
  - issue_id: TEXT (original issue ID)
  - content: TEXT (chunk text)
  - section: TEXT (subject/description/combined)
  - author: TEXT (filterable)
  - status: TEXT (filterable)
  - related_issues: TEXT
  - subject: TEXT
Vector: 1024 dimensions (e5-large-v2)
```

**Hybrid Search Algorithm**:
```
score = α × vector_score + (1 - α) × keyword_score

Where:
  α = 0.0: Pure keyword (BM25)
  α = 0.5: Balanced (default)
  α = 1.0: Pure semantic (vector)
```

### 4. LLM Generator (`llm_generator.py`)

**Purpose**: Generate answers from retrieved contexts

**Options**:

**Option A: Llama 3 (Local)**
- Model: `meta-llama/Llama-3.2-3B-Instruct`
- Pros: Free, private, no API key
- Cons: Slower, requires RAM
- Best for: Testing, development

**Option B: GPT-4 (OpenAI)**
- Model: `gpt-4`
- Pros: Better quality, faster
- Cons: Costs money, needs API key
- Best for: Production, best results

**Prompt Template**:
```
System: You are an assistant helping with project issues.

Context Documents:
[Retrieved chunks with metadata]

User Question: {query}

Rules:
- Answer ONLY from context
- Cite sources (ID, author, status)
- Use markdown formatting
- Be concise and accurate
```

### 5. FastAPI Backend (`backend.py`)

**Purpose**: REST API for search and retrieval

**Endpoints**:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Root, system info |
| GET | `/health` | Health check |
| GET | `/stats` | Database statistics |
| GET | `/authors` | List all authors |
| GET | `/statuses` | List all statuses |
| POST | `/search` | Main search endpoint |

**Search Request**:
```json
{
  "query": "string",
  "alpha": 0.5,
  "top_k": 5,
  "author": "optional",
  "status": "optional",
  "generate_answer": true
}
```

**Search Response**:
```json
{
  "query": "string",
  "results": [
    {
      "chunk_id": "315_combined_0",
      "issue_id": "315",
      "content": "...",
      "author": "Adnan Topçu",
      "status": "Closed",
      "score": 0.89
    }
  ],
  "answer": "Generated answer...",
  "total_results": 5
}
```

### 6. Streamlit Frontend (`frontend.py`)

**Purpose**: User interface for querying

**Features**:
- Text input for queries
- Sidebar with filters and controls
- Real-time search
- Results display with markdown
- Source document viewer
- Statistics and info

**State Management**:
```python
session_state:
  - search_results: Last search results
  - last_query: Previous query
  - elapsed_time: Search duration
```

### 7. RAGAS Evaluation (`ragas_evaluation.py`)

**Purpose**: Quality assessment

**Metrics**:

1. **Context Precision** (0-1)
   - Measures: Relevance of retrieved docs
   - Formula: Relevant docs / Total retrieved
   
2. **Context Recall** (0-1)
   - Measures: Completeness of retrieval
   - Formula: Retrieved info / Required info

3. **Faithfulness** (0-1)
   - Measures: Accuracy to sources
   - Formula: Factual statements / Total statements

4. **Answer Relevancy** (0-1)
   - Measures: Query-answer alignment
   - Formula: Semantic similarity(query, answer)

**Test Cases**: Pre-defined question/answer pairs

---

## 🔍 Search Algorithm Deep Dive

### Hybrid Search Implementation

```python
def hybrid_search(query, embedding, alpha):
    """
    Alpha: Balance parameter (0 to 1)
    
    Process:
    1. Keyword Search (BM25)
       - Tokenize query
       - Match tokens in documents
       - Score by term frequency & document length
       
    2. Semantic Search (Vector)
       - Use query embedding
       - Compute cosine similarity with all docs
       - Rank by similarity score
       
    3. Combine Scores
       final_score = alpha * semantic + (1-alpha) * keyword
       
    4. Apply Filters
       - Filter by author if specified
       - Filter by status if specified
       
    5. Return Top K
       - Sort by final_score
       - Return top k results
    """
```

**Why Hybrid?**
- Keyword good for: Exact terms, technical IDs, names
- Semantic good for: Concepts, synonyms, paraphrases
- Combined: Best of both worlds

**Example**:

Query: "authentication features"

| Document | Keyword Score | Semantic Score | α=0.5 Final |
|----------|---------------|----------------|-------------|
| "JWT auth" | 0.3 | 0.9 | 0.60 |
| "login system" | 0.1 | 0.85 | 0.475 |
| "authentication API" | 0.8 | 0.75 | 0.775 ⭐ |

---

## 🧮 Performance Characteristics

### Time Complexity

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| Document chunking | O(n × m) | ~1s per 100 docs |
| Embedding creation | O(n) | ~0.1s per doc (CPU) |
| Vector insertion | O(n × log n) | ~0.01s per doc |
| Hybrid search | O(log n) | ~100ms |
| Answer generation | O(k × t) | ~5s (Llama), ~2s (GPT) |

Where:
- n = number of chunks
- m = avg chunk size
- k = retrieved docs
- t = tokens per doc

### Space Complexity

| Component | Size per Item | 1000 Issues |
|-----------|---------------|-------------|
| Raw text | ~1KB | ~1MB |
| Embeddings | 4KB (1024×4 bytes) | ~12MB |
| Metadata | ~200 bytes | ~0.6MB |
| **Total** | **~5.2KB** | **~15MB** |

### Scalability

| # Issues | # Chunks | DB Size | Search Time |
|----------|----------|---------|-------------|
| 100 | 300 | 2MB | 50ms |
| 1,000 | 3,000 | 15MB | 80ms |
| 10,000 | 30,000 | 150MB | 150ms |
| 100,000 | 300,000 | 1.5GB | 300ms |

---

## 🔐 Security Considerations

### Current Implementation

- ✅ No authentication (suitable for internal use)
- ✅ Anonymous Weaviate access
- ✅ CORS enabled (development)
- ⚠️ No rate limiting
- ⚠️ No input validation
- ⚠️ API keys in environment variables

### Production Recommendations

1. **Add Authentication**
   ```python
   from fastapi.security import HTTPBearer
   security = HTTPBearer()
   ```

2. **Rate Limiting**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

3. **Input Validation**
   - Sanitize queries (SQL injection, XSS)
   - Validate file uploads
   - Limit query length

4. **API Key Security**
   - Use secrets manager (AWS, Azure, GCP)
   - Rotate keys regularly
   - Never commit to git

5. **CORS Configuration**
   - Restrict allowed origins
   - Remove wildcard "*"

---

## 🎯 Optimization Opportunities

### Current Bottlenecks

1. **Embedding Generation** (Slowest)
   - Solution: GPU acceleration
   - Alternative: Smaller model

2. **LLM Generation** (Second Slowest)
   - Solution: Use GPT-4 API
   - Alternative: Smaller Llama model

3. **Weaviate Network** (If cloud)
   - Solution: Local Weaviate
   - Alternative: Caching

### Caching Strategy

```python
# Add to backend.py
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str, alpha: float, top_k: int):
    # Cache search results for identical queries
    pass
```

### Batch Processing

```python
# For multiple queries
async def batch_search(queries: List[str]):
    embeddings = model.encode_documents(queries)
    results = await asyncio.gather(*[
        search(q, e) for q, e in zip(queries, embeddings)
    ])
    return results
```

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `WEAVIATE_URL` | `http://localhost:8080` | Weaviate endpoint |
| `WEAVIATE_API_KEY` | None | Authentication |
| `EMBEDDING_MODEL_NAME` | `intfloat/e5-large-v2` | Embedding model |
| `LLM_MODEL_NAME` | `meta-llama/Llama-3.2-3B-Instruct` | LLM |
| `USE_OPENAI` | `false` | Use OpenAI vs local |
| `OPENAI_API_KEY` | None | OpenAI auth |

### Tunable Parameters

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `chunk_size` | 512 | 256-1024 | Granularity |
| `chunk_overlap` | 50 | 0-200 | Context continuity |
| `alpha` | 0.5 | 0.0-1.0 | Search balance |
| `top_k` | 5 | 1-20 | Result count |
| `batch_size` | 32 | 8-64 | Embedding speed |

---

## 📈 Monitoring & Logging

### Key Metrics to Track

1. **Search Performance**
   - Query latency (p50, p95, p99)
   - Results returned
   - Filter usage

2. **System Health**
   - Weaviate connection status
   - Model load times
   - Memory usage

3. **Quality Metrics**
   - RAGAS scores over time
   - User satisfaction (if collected)
   - Answer length distribution

### Logging Strategy

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_system.log'),
        logging.StreamHandler()
    ]
)

# Log important events
logger.info(f"Search query: {query}")
logger.info(f"Retrieved {len(results)} results")
logger.warning(f"Slow query: {elapsed_time}s")
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# test_document_processor.py
def test_chunking():
    processor = DocumentProcessor(chunk_size=100, overlap=10)
    text = "A" * 250
    chunks = processor.create_chunks_from_text(text, 100)
    assert len(chunks) == 3
```

### Integration Tests

```python
# test_backend.py
def test_search_endpoint():
    response = client.post("/search", json={
        "query": "test",
        "alpha": 0.5,
        "top_k": 5
    })
    assert response.status_code == 200
    assert "results" in response.json()
```

### End-to-End Tests

```python
# test_e2e.py
def test_full_pipeline():
    # Setup database
    setup_database(test_chunks, test_embeddings)
    
    # Perform search
    result = perform_search("test query")
    
    # Verify results
    assert result['total_results'] > 0
    assert result['answer'] is not None
```

---

## 🎓 Design Decisions

### Why These Choices?

1. **Streamlit over React**
   - Faster development
   - Python-only
   - Built-in components

2. **FastAPI over Flask**
   - Async support
   - Auto documentation
   - Type checking

3. **Weaviate over Pinecone/Milvus**
   - Hybrid search built-in
   - Open source option
   - Great documentation

4. **e5-large-v2 over OpenAI embeddings**
   - Free (no API costs)
   - Runs locally
   - State-of-the-art quality

5. **Chunking strategy**
   - Small chunks: More precise retrieval
   - Overlap: Maintains context
   - Multiple types: Flexibility

---

This architecture supports the requirements outlined in the specification and provides a solid foundation for a production RAG system.
