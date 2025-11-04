# 🚀 Complete Setup Guide

This guide walks you through setting up the RAG system from scratch.

---

## 📋 Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] 8GB+ RAM available
- [ ] 10GB+ disk space
- [ ] Docker installed (for local Weaviate)
- [ ] Terminal/Command prompt access

---

## 🛠️ Step-by-Step Installation

### Step 1: Prepare Environment

```bash
# Navigate to workspace
cd /workspace

# Create and activate virtual environment
python -m venv venv

# Activate (choose your OS)
source venv/bin/activate          # Linux/Mac
# or
venv\Scripts\activate              # Windows

# Verify Python version
python --version  # Should be 3.9+
```

### Step 2: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# This will take 5-10 minutes
# Downloads ~3GB of packages
```

**Common Issues:**

- **PyTorch CUDA**: If you have GPU, install PyTorch with CUDA:
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```

- **Memory issues**: If installation fails, install in batches:
  ```bash
  pip install fastapi uvicorn streamlit
  pip install sentence-transformers transformers
  pip install weaviate-client ragas
  ```

### Step 3: Setup Weaviate Database

#### Option A: Local Weaviate (Recommended for Testing)

```bash
# Pull Weaviate Docker image
docker pull cr.weaviate.io/semitechnologies/weaviate:latest

# Run Weaviate
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -v $(pwd)/weaviate_data:/var/lib/weaviate \
  cr.weaviate.io/semitechnologies/weaviate:latest

# Verify it's running
docker ps | grep weaviate

# Test connection
curl http://localhost:8080/v1/.well-known/ready
# Should return: {"status":"ok"}
```

**To stop/start Weaviate:**
```bash
docker stop weaviate
docker start weaviate
```

#### Option B: Weaviate Cloud Services (For Production)

1. Go to https://console.weaviate.cloud
2. Sign up for free account
3. Click "Create Cluster"
4. Choose free sandbox tier
5. Wait for cluster to provision (~2 minutes)
6. Copy your cluster URL and API key

### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your favorite editor
nano .env
# or
vim .env
# or
code .env  # VSCode
```

**For Local Weaviate:**
```bash
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

USE_OPENAI=false
LLM_MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
```

**For Weaviate Cloud:**
```bash
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your-api-key-here

USE_OPENAI=false
LLM_MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
```

**For OpenAI (Optional, Better Quality):**
```bash
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

USE_OPENAI=true
OPENAI_API_KEY=sk-your-openai-api-key
LLM_MODEL_NAME=gpt-4
```

### Step 5: Verify Data File

```bash
# Check that data file exists
ls -lh all_issues_for_test.csv

# Preview first few lines
head -n 5 all_issues_for_test.csv

# Count issues
wc -l all_issues_for_test.csv
```

### Step 6: Setup Database

```bash
# Run the setup script
python setup_database.py
```

**What happens:**
1. Loads and processes CSV (1-2 minutes)
2. Creates embeddings (5-10 minutes on CPU, 1-2 min on GPU)
3. Populates Weaviate (1-2 minutes)

**Expected output:**
```
🚀 RAG SYSTEM DATABASE SETUP
============================================================

📄 STEP 1: Processing Documents
------------------------------------------------------------
Loaded X issues from /workspace/all_issues_for_test.csv
Created Y chunks from X issues
✅ Processing complete!

🧠 STEP 2: Creating Embeddings
------------------------------------------------------------
Loading embedding model: intfloat/e5-large-v2 on cpu...
✓ Embedding model loaded (dimension: 1024)
Creating embeddings for Y chunks...
100%|████████████████████| Y/Y [XX:XX<00:00]
✓ Created Y embeddings

🗄️  STEP 3: Setting up Weaviate Database
------------------------------------------------------------
✓ Connected to Weaviate at http://localhost:8080
✓ Created collection: IssueChunk
Inserting Y chunks into Weaviate...
✓ Inserted Y chunks in X.XXs

✅ DATABASE SETUP COMPLETE!
```

**Troubleshooting:**

- **Connection refused**: Weaviate not running
  ```bash
  docker ps | grep weaviate
  docker start weaviate
  ```

- **Out of memory**: Reduce batch size
  - Edit `setup_database.py`
  - Change `batch_size=32` to `batch_size=16`

- **Embedding download fails**: Network issue
  ```bash
  # Manually download model first
  python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-large-v2')"
  ```

### Step 7: Start Backend

```bash
# Start the FastAPI backend
python backend.py
```

**Expected output:**
```
🚀 Starting RAG System Backend...
✓ Weaviate connected
✓ Embedding model loaded
✓ LLM generator initialized
✅ Backend ready!

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test the backend:**
```bash
# In another terminal
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "weaviate": "connected",
  "embedding_model": "intfloat/e5-large-v2",
  "llm_model": "meta-llama/Llama-3.2-3B-Instruct",
  "total_chunks": 350
}
```

### Step 8: Start Frontend

Open a **new terminal** (keep backend running):

```bash
# Activate virtual environment again
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate      # Windows

# Start Streamlit
streamlit run frontend.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

Your browser should open automatically!

### Step 9: Test the System

1. **Enter a query**: "What features involve keyboard shortcuts?"
2. **Click "Run"**
3. **Wait 5-10 seconds**
4. **View results**: Answer + source documents

Try these queries:
- "Show issues about importing from JIRA"
- "What work has been done on time tracking?"
- "Find closed issues about filtering"

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Weaviate is running: `docker ps | grep weaviate`
- [ ] Backend is healthy: `curl http://localhost:8000/health`
- [ ] Frontend is accessible: Open http://localhost:8501
- [ ] Search works: Try a test query
- [ ] Results appear: See answer + documents
- [ ] Filters work: Try filtering by author/status

---

## 🎨 Optional: Run Evaluation

```bash
# In a new terminal
source venv/bin/activate
python ragas_evaluation.py
```

This evaluates system quality (takes 2-5 minutes).

---

## 📊 System Check Commands

```bash
# Check Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Check Backend
curl http://localhost:8000/health

# Get stats
curl http://localhost:8000/stats

# Test search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "API features", "alpha": 0.5, "top_k": 5}'
```

---

## 🛑 Stopping the System

```bash
# Stop frontend: Press Ctrl+C in Streamlit terminal

# Stop backend: Press Ctrl+C in backend terminal

# Stop Weaviate
docker stop weaviate

# Or stop and remove
docker stop weaviate && docker rm weaviate
```

---

## 🔄 Restarting the System

```bash
# 1. Start Weaviate
docker start weaviate

# 2. Start Backend
python backend.py

# 3. Start Frontend (in new terminal)
streamlit run frontend.py
```

---

## 🆘 Common Issues & Solutions

### Issue: "ModuleNotFoundError"

**Cause**: Dependencies not installed or wrong environment

**Solution**:
```bash
# Verify you're in virtual environment
which python  # Should show venv path

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: "Connection to Weaviate failed"

**Cause**: Weaviate not running

**Solution**:
```bash
docker start weaviate
# Wait 10 seconds for startup
curl http://localhost:8080/v1/.well-known/ready
```

### Issue: "Backend not accessible" in Frontend

**Cause**: Backend not running or wrong URL

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# If not, start it
python backend.py

# Check BACKEND_URL in .env
cat .env | grep BACKEND_URL
```

### Issue: Very slow embedding creation

**Cause**: Running on CPU

**Solutions**:
1. Use GPU if available (update config.py: `EMBEDDING_DEVICE = "cuda"`)
2. Reduce data size for testing
3. Use smaller model: `EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"`

### Issue: LLM out of memory

**Cause**: Model too large for RAM

**Solutions**:
1. Close other applications
2. Use OpenAI API instead:
   ```bash
   USE_OPENAI=true
   OPENAI_API_KEY=your-key
   ```
3. Use smaller model: `LLM_MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"`

---

## 🎯 Next Steps

Once everything is running:

1. ✅ Try different queries
2. ✅ Adjust search parameters (alpha, top_k)
3. ✅ Test filters (author, status)
4. ✅ Run RAGAS evaluation
5. ✅ Customize for your data

---

## 📚 Additional Resources

- **Weaviate Docs**: https://weaviate.io/developers/weaviate
- **Streamlit Docs**: https://docs.streamlit.io
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **RAGAS Docs**: https://docs.ragas.io

---

**Setup complete? Start asking questions!** 🎉
