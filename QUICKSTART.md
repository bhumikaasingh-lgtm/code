# ⚡ Quick Start - Get Running in 5 Minutes!

This is the **fastest** way to get your RAG system running.

---

## 🎯 Goal

Get from zero to asking questions in **5 minutes**.

---

## ✅ Prerequisites Check (30 seconds)

```bash
# Check Python version (need 3.9+)
python --version

# Check Docker (need for Weaviate)
docker --version

# Check you have 8GB+ RAM
free -h  # Linux
# or
vm_stat  # Mac
```

All good? Let's go! 🚀

---

## 📦 Step 1: Install (2 minutes)

```bash
# Navigate to workspace
cd /workspace

# Install Python packages
pip install -r requirements.txt
```

☕ Go grab coffee while this installs (~2 minutes)...

---

## 🗄️ Step 2: Start Weaviate (30 seconds)

```bash
# Start Weaviate database
docker-compose up -d

# Wait 10 seconds for it to start
sleep 10

# Verify it's running
curl http://localhost:8080/v1/.well-known/ready
# Should show: {"status":"ok"}
```

---

## ⚙️ Step 3: Configure (30 seconds)

```bash
# Copy environment template
cp .env.example .env

# Use default settings (they work out of the box!)
# No editing needed for quick start
```

---

## 📊 Step 4: Load Data (1 minute)

```bash
# Process CSV and create embeddings
python setup_database.py
```

You'll see:
```
🚀 RAG SYSTEM DATABASE SETUP
📄 Processing Documents...
🧠 Creating Embeddings...
🗄️ Setting up Database...
✅ COMPLETE!
```

---

## 🚀 Step 5: Run! (10 seconds)

### Option A: Automatic (Recommended)

```bash
./run.sh
```

Done! Browser opens automatically.

### Option B: Manual

```bash
# Terminal 1
python backend.py

# Terminal 2
streamlit run frontend.py
```

---

## 🎉 Success!

Your browser should open to: **http://localhost:8501**

### Try These Queries:

1. "What features involve keyboard shortcuts?"
2. "Show issues about importing from JIRA"
3. "What work has been done on time tracking?"

---

## ⏱️ Total Time: ~5 minutes

- Install: 2 min
- Weaviate: 30 sec
- Config: 30 sec
- Data load: 1 min
- Start: 10 sec
- **Done!** 🎯

---

## 🆘 Something Wrong?

### Backend won't start?
```bash
# Check Weaviate is running
docker ps | grep weaviate

# Restart it
docker restart weaviate
```

### Can't access frontend?
```bash
# Check backend is running
curl http://localhost:8000/health

# If not, start it
python backend.py
```

### Need more help?
See `SETUP_GUIDE.md` for detailed troubleshooting.

---

## 🎓 Next Steps

Now that it's running:

1. ✅ Try different queries
2. ✅ Adjust the search balance slider
3. ✅ Use filters (author, status)
4. ✅ Read `README.md` for full features
5. ✅ Run evaluation: `python ragas_evaluation.py`

---

## 📚 Full Documentation

- **Quick Start**: This file (you are here!)
- **Setup Guide**: `SETUP_GUIDE.md` (detailed installation)
- **User Manual**: `README.md` (complete guide)
- **Architecture**: `ARCHITECTURE.md` (technical deep-dive)

---

**Ready? Let's go!** 🚀

```bash
pip install -r requirements.txt && \
docker-compose up -d && \
sleep 10 && \
cp .env.example .env && \
python setup_database.py && \
./run.sh
```

Copy-paste the above for **one-command setup**! ⚡
