# 📂 Complete File Guide

Your RAG system consists of **19 files** across **4,394 lines**.

---

## 📊 File Overview

### Python Modules (9 files, 2,519 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `config.py` | 60 | System configuration and settings |
| `document_processor.py` | 253 | Convert CSV to searchable chunks |
| `embeddings.py` | 156 | Text to vector conversion (e5-large-v2) |
| `weaviate_client.py` | 287 | Vector database operations |
| `llm_generator.py` | 236 | AI answer generation (Llama/GPT) |
| `backend.py` | 226 | FastAPI REST API server |
| `frontend.py` | 312 | Streamlit web interface |
| `ragas_evaluation.py` | 327 | Quality evaluation system |
| `setup_database.py` | 82 | Database initialization script |

### Documentation (5 files, 1,713 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `README.md` | 479 | Complete user guide |
| `SETUP_GUIDE.md` | 421 | Step-by-step installation |
| `ARCHITECTURE.md` | 579 | Technical architecture |
| `PROJECT_SUMMARY.md` | 333 | Project overview |
| `QUICKSTART.md` | 139 | 5-minute quick start |
| `FILE_GUIDE.md` | - | This file! |

### Configuration (5 files)

| File | Lines | Purpose |
|------|-------|---------|
| `requirements.txt` | 38 | Python dependencies |
| `.env.example` | 16 | Environment template |
| `.gitignore` | 41 | Git ignore rules |
| `docker-compose.yml` | 24 | Weaviate Docker setup |
| `run.sh` | 56 | Convenience launcher script |

---

## 🎯 Which File to Read First?

### If you want to...

**Get started quickly** → `QUICKSTART.md`
- 5-minute setup guide
- One-command installation
- Basic usage

**Understand the system** → `README.md`
- Complete user manual
- Feature descriptions
- Configuration options

**Install step-by-step** → `SETUP_GUIDE.md`
- Detailed installation
- Troubleshooting tips
- Prerequisites checklist

**Learn architecture** → `ARCHITECTURE.md`
- Technical deep-dive
- Design decisions
- Performance details

**Get an overview** → `PROJECT_SUMMARY.md`
- High-level summary
- Key features
- Success criteria

---

## 🗂️ File Organization by Purpose

### Setup & Configuration
```
config.py           - Central configuration
.env.example        - Environment template
requirements.txt    - Dependencies
docker-compose.yml  - Weaviate setup
```

### Data Processing Pipeline
```
document_processor.py  - CSV → Chunks
embeddings.py          - Chunks → Vectors
weaviate_client.py     - Store in DB
setup_database.py      - Run entire pipeline
```

### Runtime System
```
backend.py    - API server (port 8000)
frontend.py   - Web UI (port 8501)
run.sh        - Start both
```

### Quality & Testing
```
ragas_evaluation.py  - Quality metrics
llm_generator.py     - Answer generation
```

### Documentation
```
QUICKSTART.md       - Fast start
SETUP_GUIDE.md      - Detailed setup
README.md           - User manual
ARCHITECTURE.md     - Technical docs
PROJECT_SUMMARY.md  - Overview
FILE_GUIDE.md       - This file
```

---

## 📖 Reading Order by Use Case

### Use Case 1: First-Time Setup
1. `QUICKSTART.md` - Get running fast
2. `README.md` - Learn features
3. Try the system!
4. `SETUP_GUIDE.md` - If issues arise

### Use Case 2: Understanding the System
1. `PROJECT_SUMMARY.md` - High-level overview
2. `README.md` - User perspective
3. `ARCHITECTURE.md` - Technical details
4. Source code - Deep dive

### Use Case 3: Customization
1. `config.py` - Adjust settings
2. `ARCHITECTURE.md` - Understand components
3. Specific module files - Modify behavior
4. Test changes with `ragas_evaluation.py`

### Use Case 4: Troubleshooting
1. `SETUP_GUIDE.md` - Common issues section
2. Component test scripts - Identify problem
3. Logs - Check for errors
4. `ARCHITECTURE.md` - Understand interactions

---

## 🔍 Detailed File Descriptions

### `config.py` - Central Configuration
```python
# What it contains:
- Weaviate connection settings
- Embedding model selection
- LLM configuration
- Chunking parameters
- Search defaults
- API settings

# Key classes:
- Config: Main configuration class

# When to edit:
- Change models
- Adjust chunk sizes
- Modify search defaults
```

### `document_processor.py` - Document Processing
```python
# What it does:
- Loads CSV files
- Cleans and normalizes text
- Splits documents into chunks
- Maintains metadata
- Creates multiple chunk types

# Key classes:
- DocumentChunk: Represents one chunk
- DocumentProcessor: Main processor

# Key methods:
- load_csv(): Read CSV
- create_chunks_from_text(): Smart splitting
- process_file(): Full pipeline
```

### `embeddings.py` - Vector Embeddings
```python
# What it does:
- Loads e5-large-v2 model
- Converts text to 1024-dim vectors
- Handles query vs document prefixes
- Batch processing for efficiency

# Key classes:
- EmbeddingModel: Embedding operations

# Key methods:
- encode_query(): Query → vector
- encode_documents(): Batch docs → vectors
- compute_similarity(): Vector comparison
```

### `weaviate_client.py` - Vector Database
```python
# What it does:
- Connects to Weaviate
- Creates database schema
- Inserts chunks + embeddings
- Performs hybrid search
- Manages filters

# Key classes:
- WeaviateManager: Database operations

# Key methods:
- connect(): Establish connection
- create_schema(): Setup database
- insert_chunks(): Bulk insert
- hybrid_search(): Search with α balance
```

### `llm_generator.py` - Answer Generation
```python
# What it does:
- Initializes LLM (Llama or GPT)
- Creates prompts from contexts
- Generates factual answers
- Cites sources

# Key classes:
- LLMGenerator: Answer generation

# Key methods:
- create_prompt(): Format context
- generate(): Create answer
- generate_openai(): GPT-4 generation
- generate_huggingface(): Llama generation
```

### `backend.py` - API Server
```python
# What it does:
- FastAPI REST API
- Coordinates all components
- Handles search requests
- Returns JSON responses

# Key endpoints:
- POST /search: Main search
- GET /health: Health check
- GET /stats: Database info
- GET /authors: List authors
- GET /statuses: List statuses
```

### `frontend.py` - Web Interface
```python
# What it does:
- Streamlit web UI
- Query input form
- Filter controls
- Results display
- Beautiful styling

# Key sections:
- Sidebar: Controls and filters
- Main: Query and results
- Expanders: Detailed views
```

### `ragas_evaluation.py` - Quality Metrics
```python
# What it does:
- Defines test cases
- Runs evaluation pipeline
- Calculates RAGAS metrics
- Generates reports

# Key classes:
- RAGASEvaluator: Evaluation system

# Key methods:
- create_test_cases(): Define tests
- run_test_case(): Execute one test
- evaluate(): Run all tests
- print_report(): Show results
```

### `setup_database.py` - Setup Script
```python
# What it does:
- Orchestrates setup process
- Calls all components
- Shows progress
- Validates completion

# Process:
1. Load and process CSV
2. Create embeddings
3. Setup Weaviate
4. Insert data
5. Verify
```

---

## 🎨 Visual File Map

```
RAG SYSTEM
│
├── 📚 DOCUMENTATION (Read first)
│   ├── QUICKSTART.md ............... ⚡ 5-min start
│   ├── README.md ................... 📖 User guide
│   ├── SETUP_GUIDE.md .............. 🔧 Detailed setup
│   ├── ARCHITECTURE.md ............. 🏗️ Tech details
│   ├── PROJECT_SUMMARY.md .......... 📊 Overview
│   └── FILE_GUIDE.md ............... 📂 This file
│
├── ⚙️ CONFIGURATION
│   ├── config.py ................... Central config
│   ├── .env.example ................ Environment
│   ├── requirements.txt ............ Dependencies
│   ├── .gitignore .................. Git rules
│   └── docker-compose.yml .......... Weaviate
│
├── 🔄 DATA PIPELINE
│   ├── document_processor.py ....... CSV → Chunks
│   ├── embeddings.py ............... Text → Vectors
│   ├── weaviate_client.py .......... Vector DB
│   └── setup_database.py ........... Run pipeline
│
├── 🚀 RUNTIME SYSTEM
│   ├── backend.py .................. API server
│   ├── frontend.py ................. Web UI
│   ├── llm_generator.py ............ Answer gen
│   └── run.sh ...................... Launcher
│
└── 📊 QUALITY
    └── ragas_evaluation.py ......... Evaluation
```

---

## 📏 Code Statistics

### By Category

| Category | Files | Lines | % |
|----------|-------|-------|---|
| Documentation | 6 | 1,713 | 39% |
| Core Python | 9 | 2,519 | 57% |
| Configuration | 5 | 162 | 4% |
| **Total** | **20** | **4,394** | **100%** |

### Largest Files

1. `ARCHITECTURE.md` - 579 lines
2. `README.md` - 479 lines
3. `SETUP_GUIDE.md` - 421 lines
4. `ragas_evaluation.py` - 327 lines
5. `PROJECT_SUMMARY.md` - 333 lines

### Most Complex Modules

1. `ragas_evaluation.py` - Evaluation logic
2. `frontend.py` - UI components
3. `weaviate_client.py` - DB operations
4. `document_processor.py` - Text processing
5. `llm_generator.py` - LLM integration

---

## 🎯 File Dependencies

```
setup_database.py
    ├── config.py
    ├── document_processor.py
    ├── embeddings.py
    └── weaviate_client.py

backend.py
    ├── config.py
    ├── weaviate_client.py
    ├── embeddings.py
    └── llm_generator.py

frontend.py
    ├── config.py
    └── backend.py (via HTTP)

ragas_evaluation.py
    ├── config.py
    ├── weaviate_client.py
    ├── embeddings.py
    └── llm_generator.py
```

---

## 🔄 File Modification Guide

### To change embedding model:
1. Edit `config.py` → `EMBEDDING_MODEL_NAME`
2. May need to adjust `EMBEDDING_DIMENSION`
3. Re-run `setup_database.py`

### To change LLM:
1. Edit `.env` → `USE_OPENAI`, `LLM_MODEL_NAME`
2. Restart `backend.py`
3. No database changes needed

### To adjust chunking:
1. Edit `config.py` → `CHUNK_SIZE`, `CHUNK_OVERLAP`
2. Re-run `setup_database.py`

### To modify UI:
1. Edit `frontend.py`
2. Changes apply immediately (Streamlit auto-reloads)

### To add new data:
1. Update CSV file
2. Re-run `setup_database.py`

---

## 🎓 Learning Path

### Beginner: Just Want to Use It
```
QUICKSTART.md → Try the system → Done!
```

### Intermediate: Understand & Customize
```
README.md → ARCHITECTURE.md → Modify config.py
```

### Advanced: Extend & Enhance
```
All docs → Read source code → Make changes → Test
```

---

## 📦 Files by Installation Stage

### Before Installation
- `README.md` - Learn what you're installing
- `QUICKSTART.md` - See it's easy
- `requirements.txt` - See dependencies

### During Installation
- `SETUP_GUIDE.md` - Follow steps
- `.env.example` → `.env` - Configure
- `docker-compose.yml` - Start Weaviate

### After Installation
- `setup_database.py` - Load data
- `run.sh` - Start system
- `ragas_evaluation.py` - Test quality

### Daily Use
- `frontend.py` (runs in browser)
- Occasionally: `ARCHITECTURE.md` for reference

---

This guide covers all 20 files in your RAG system. Start with `QUICKSTART.md` and explore from there! 🚀
