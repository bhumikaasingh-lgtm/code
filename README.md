# 🎯 Catch - Unified Story Retriever

**Multiple management tools in. One RAG pipeline out.**

A Retrieval-Augmented Generation (RAG) system that searches through project management issues and provides intelligent, context-aware answers to your questions.

---

## 🌟 Features

- 🔍 **Hybrid Search**: Combines keyword and semantic search for best results
- 🧠 **Smart AI**: Uses e5-large-v2 embeddings and Llama 3/GPT-4 for generation
- 📊 **Beautiful UI**: Clean Streamlit interface with filters and controls
- 🎯 **Accurate Results**: RAGAS evaluation ensures high-quality responses
- ⚡ **Fast**: Searches thousands of documents in seconds
- 🔒 **Source Citations**: Every answer shows the source documents

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Frontend (Streamlit)                   │
│  • User interface                        │
│  • Query input & filters                 │
│  • Results display                       │
└──────────────┬──────────────────────────┘
               │ HTTP/REST
               ▼
┌─────────────────────────────────────────┐
│  Backend (FastAPI)                      │
│  • Search coordination                   │
│  • Hybrid retrieval                      │
│  • Answer generation                     │
└──────────────┬──────────────────────────┘
               │ Queries
               ▼
┌─────────────────────────────────────────┐
│  Weaviate (Vector Database)             │
│  • Document chunks + embeddings          │
│  • Hybrid search engine                  │
└─────────────────────────────────────────┘
```

---

## 📋 Prerequisites

- Python 3.9 or higher
- Weaviate instance (local or cloud)
- 8GB+ RAM recommended
- GPU optional (faster embeddings)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository (or use existing workspace)
cd /workspace

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Setup Weaviate

**Option A: Local Weaviate (Docker)**

```bash
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  cr.weaviate.io/semitechnologies/weaviate:latest
```

**Option B: Weaviate Cloud Services (WCS)**

1. Sign up at https://console.weaviate.cloud
2. Create a free cluster
3. Get your cluster URL and API key

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

Required settings:
```bash
WEAVIATE_URL=http://localhost:8080  # Or your WCS URL
WEAVIATE_API_KEY=                   # Optional for local, required for WCS

# Choose LLM (default: free Llama 3)
USE_OPENAI=false
LLM_MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct

# Or use OpenAI GPT-4 (requires API key)
# USE_OPENAI=true
# OPENAI_API_KEY=your-key-here
# LLM_MODEL_NAME=gpt-4
```

### 4. Setup Database

Process documents and create embeddings:

```bash
python setup_database.py
```

This will:
1. Load and chunk the CSV data
2. Create embeddings using e5-large-v2
3. Populate Weaviate database

**Expected output:**
```
🚀 RAG SYSTEM DATABASE SETUP
============================================================

📄 STEP 1: Processing Documents
------------------------------------------------------------
Loaded 100 issues from /workspace/all_issues_for_test.csv
Created 350 chunks from 100 issues

✅ Processing complete!
   • Total chunks: 350
   • Unique issues: 100
   • Avg chunks per issue: 3.50
   • Unique authors: 45
   • Unique statuses: 8

🧠 STEP 2: Creating Embeddings
------------------------------------------------------------
Loading embedding model: intfloat/e5-large-v2 on cpu...
✓ Embedding model loaded (dimension: 1024)
Creating embeddings for 350 chunks...
✓ Created 350 embeddings

🗄️  STEP 3: Setting up Weaviate Database
------------------------------------------------------------
✓ Connected to Weaviate at http://localhost:8080
✓ Deleted existing collection: IssueChunk
✓ Created collection: IssueChunk
Inserting 350 chunks into Weaviate...
  Inserted 100/350 chunks
  Inserted 200/350 chunks
  Inserted 300/350 chunks
✓ Inserted 350 chunks in 5.23s

✓ Database setup complete!
  Total objects: 350

============================================================
✅ DATABASE SETUP COMPLETE!
⏱️  Total time: 127.45 seconds
============================================================
```

### 5. Start the Backend

```bash
python backend.py
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 6. Start the Frontend

In a new terminal:

```bash
streamlit run frontend.py
```

The UI will open automatically in your browser (usually http://localhost:8501)

---

## 💻 Usage

### Web Interface

1. **Enter your question** in natural language
2. **Adjust filters** (optional):
   - Filter by author
   - Filter by status
3. **Configure search** (optional):
   - Search balance (keyword ↔ semantic)
   - Number of results
4. **Click "Run"** to get your answer

### Example Queries

- "What API features did Adnan work on?"
- "Show closed issues by Abbas about calendar"
- "Find features related to authentication"
- "What work has been done on time tracking?"

### API Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "What features involve keyboard shortcuts?",
        "alpha": 0.5,
        "top_k": 5,
        "author": None,
        "status": None,
        "generate_answer": True
    }
)

data = response.json()
print(data['answer'])
```

---

## 📊 Evaluation

Run RAGAS evaluation to assess system quality:

```bash
python ragas_evaluation.py
```

Optional parameters:
```bash
python ragas_evaluation.py 0.5 5  # alpha=0.5, top_k=5
```

**Sample output:**
```
📊 RAGAS EVALUATION REPORT
============================================================
Context Precision    |████████████████░░░░| 0.850 ✅ Good
Context Recall       |██████████████░░░░░░| 0.725 ✅ Good
Faithfulness         |███████████████░░░░░| 0.790 ✅ Good
Answer Relevancy     |███████████████████░| 0.950 ✅ Excellent
------------------------------------------------------------
Average              |█████████████████░░░| 0.829 ✅ Good
============================================================
```

---

## 🛠️ Project Structure

```
workspace/
├── all_issues_for_test.csv   # Source data
├── config.py                  # Configuration
├── document_processor.py      # Chunking logic
├── embeddings.py              # E5 embedding model
├── weaviate_client.py         # Vector database
├── llm_generator.py           # Answer generation
├── backend.py                 # FastAPI server
├── frontend.py                # Streamlit UI
├── ragas_evaluation.py        # Quality evaluation
├── setup_database.py          # Database setup script
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

---

## ⚙️ Configuration

### Key Settings (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `EMBEDDING_MODEL_NAME` | `intfloat/e5-large-v2` | Embedding model |
| `EMBEDDING_DIMENSION` | `1024` | Vector dimensions |
| `LLM_MODEL_NAME` | `meta-llama/Llama-3.2-3B-Instruct` | Generation model |
| `CHUNK_SIZE` | `512` | Max chunk size (chars) |
| `CHUNK_OVERLAP` | `50` | Chunk overlap (chars) |
| `DEFAULT_ALPHA` | `0.5` | Search balance |
| `DEFAULT_TOP_K` | `5` | Default results |

### Search Balance (Alpha)

- **0.0 - 0.3**: Keyword-focused (exact matches)
- **0.4 - 0.6**: Balanced (recommended)
- **0.7 - 1.0**: Semantic-focused (meaning-based)

---

## 🧪 Testing

### Test Individual Components

```bash
# Test document processor
python document_processor.py

# Test embeddings
python embeddings.py

# Test Weaviate connection
python weaviate_client.py

# Test LLM generator
python llm_generator.py
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# Get stats
curl http://localhost:8000/stats

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "API features", "alpha": 0.5, "top_k": 5}'
```

---

## 🔧 Troubleshooting

### Backend won't start

**Issue**: `Failed to connect to Weaviate`

**Solution**: Ensure Weaviate is running:
```bash
# Check if Weaviate is running
docker ps | grep weaviate

# Restart Weaviate
docker restart weaviate
```

### Frontend shows "Backend not accessible"

**Issue**: Frontend can't reach backend

**Solution**: 
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `BACKEND_URL` in `.env`
3. Check firewall settings

### Out of memory during setup

**Issue**: Embedding creation fails with OOM

**Solution**: Reduce batch size in `setup_database.py`:
```python
embeddings = create_embeddings_for_chunks(chunks, batch_size=16)  # Was 32
```

### Slow embeddings

**Issue**: Embedding creation is very slow

**Solution**: 
1. Use GPU if available (set `EMBEDDING_DEVICE=cuda` in config)
2. Reduce data size for testing
3. Use a smaller embedding model

### LLM generation fails

**Issue**: `Error generating response`

**Solution**:
1. Check if you have enough RAM (8GB+ recommended)
2. Try using OpenAI API instead:
   ```bash
   USE_OPENAI=true
   OPENAI_API_KEY=your-key
   ```
3. Use a smaller local model

---

## 📚 How It Works

### 1. Document Processing

Documents are split into smart chunks:
- Subject section
- Description chunks (with overlap)
- Combined context chunk

Each chunk retains metadata (author, status, etc.)

### 2. Embedding Creation

Text → Vectors using e5-large-v2:
- "passage:" prefix for documents
- "query:" prefix for searches
- 1024-dimensional vectors
- Normalized for cosine similarity

### 3. Hybrid Search

Combines two methods:
- **Keyword**: BM25 algorithm (exact matches)
- **Semantic**: Vector similarity (meaning)
- **Alpha**: Controls the balance

### 4. Answer Generation

LLM reads retrieved contexts and generates answer:
- Uses only retrieved information
- Cites sources (ID, author, status)
- Markdown formatted
- Factual and concise

### 5. Quality Evaluation

RAGAS measures 4 metrics:
- **Context Precision**: Relevance of retrieved docs
- **Context Recall**: Completeness of retrieval
- **Faithfulness**: Accuracy to sources
- **Answer Relevancy**: Query-answer alignment

---

## 🎯 Performance Tips

### For Better Search Results

1. **Use complete questions**: "What features did X work on?" vs "features X"
2. **Adjust alpha**: Lower for exact terms, higher for concepts
3. **Increase top_k**: More contexts = better answers
4. **Use filters**: Narrow down by author/status

### For Better Performance

1. **GPU acceleration**: Use CUDA for embeddings
2. **Batch size**: Tune based on available memory
3. **Chunk size**: Smaller chunks = more precise, larger = more context
4. **Caching**: Results are not cached by default (add if needed)

---

## 🔮 Future Enhancements

- [ ] Query history and favorites
- [ ] Multi-language support
- [ ] Document upload interface
- [ ] Advanced filters (date ranges, keywords)
- [ ] Result caching
- [ ] User authentication
- [ ] Analytics dashboard
- [ ] Export results to PDF/CSV

---

## 📄 License

This project is provided as-is for educational and internal use.

---

## 🙏 Acknowledgments

- **Weaviate**: Vector database
- **HuggingFace**: Embedding and LLM models
- **Streamlit**: Web interface framework
- **RAGAS**: Evaluation metrics
- **FastAPI**: Backend framework

---

## 📧 Support

For issues and questions:
1. Check the troubleshooting section
2. Review component test outputs
3. Check logs for detailed errors

---

## 🎉 Quick Tips

- **First time?** Start with default settings
- **Not finding results?** Try increasing top_k to 10
- **Too many results?** Use filters to narrow down
- **Slow responses?** Check if Weaviate is local vs cloud
- **Testing?** Run RAGAS evaluation to validate

---

**Ready to start?** Run `python setup_database.py` and begin your RAG journey! 🚀
