"""
Streamlit Frontend for RAG System
Beautiful web interface for querying the RAG system
"""
import streamlit as st
import requests
import time
from typing import Dict, Any, List
from config import Config


# Page configuration
st.set_page_config(
    page_title="Catch - Unified Story Retriever",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .score-badge {
        background-color: #28a745;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .metadata {
        color: #666;
        font-size: 0.9rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def get_backend_url() -> str:
    """Get the backend URL from config"""
    return Config.BACKEND_URL


def check_backend_health() -> bool:
    """Check if backend is healthy"""
    try:
        response = requests.get(f"{get_backend_url()}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def fetch_authors() -> List[str]:
    """Fetch list of authors from backend"""
    try:
        response = requests.get(f"{get_backend_url()}/authors", timeout=10)
        if response.status_code == 200:
            return ["All"] + response.json()["authors"]
        return ["All"]
    except:
        return ["All"]


def fetch_statuses() -> List[str]:
    """Fetch list of statuses from backend"""
    try:
        response = requests.get(f"{get_backend_url()}/statuses", timeout=10)
        if response.status_code == 200:
            return ["All"] + response.json()["statuses"]
        return ["All"]
    except:
        return ["All"]


def fetch_stats() -> Dict[str, Any]:
    """Fetch database statistics"""
    try:
        response = requests.get(f"{get_backend_url()}/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def perform_search(query: str, alpha: float, top_k: int, author: str, status: str) -> Dict[str, Any]:
    """Perform search via backend API"""
    try:
        payload = {
            "query": query,
            "alpha": alpha,
            "top_k": top_k,
            "author": author if author != "All" else None,
            "status": status if status != "All" else None,
            "generate_answer": True
        }
        
        response = requests.post(
            f"{get_backend_url()}/search",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Search failed: {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


def display_result(result: Dict[str, Any], index: int):
    """Display a single search result"""
    score = result.get('score', 0.0)
    
    # Create a styled result card
    st.markdown(f"""
    <div class="result-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0;">📄 Issue #{result['issue_id']} - {result['subject']}</h4>
            <span class="score-badge">Score: {score:.3f}</span>
        </div>
        <div class="metadata" style="margin-top: 0.5rem;">
            <strong>Author:</strong> {result['author']} | 
            <strong>Status:</strong> {result['status']} | 
            <strong>Section:</strong> {result['section']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show content in expander
    with st.expander("📖 View Content", expanded=(index == 0)):
        st.markdown(result['content'])
        if result.get('related_issues'):
            st.caption(f"**Related Issues:** {result['related_issues']}")


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<div class="main-header">🎯 Catch - Unified Story Retriever</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Multiple management tools in. One RAG pipeline out.</div>', unsafe_allow_html=True)
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend is not accessible. Please ensure the backend server is running.")
        st.info(f"Expected backend URL: {get_backend_url()}")
        st.stop()
    
    # Initialize session state
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Control Panel")
        
        # Stats
        with st.expander("📊 Database Stats", expanded=False):
            stats = fetch_stats()
            if stats:
                st.metric("Total Chunks", stats.get('total_chunks', 0))
                st.metric("Unique Authors", len(stats.get('authors', [])))
                st.metric("Unique Statuses", len(stats.get('statuses', [])))
        
        st.divider()
        
        # Model information
        st.subheader("🤖 Models")
        st.caption("**Embedding:** e5-large-v2")
        st.caption(f"**LLM:** {Config.LLM_MODEL_NAME.split('/')[-1]}")
        
        st.divider()
        
        # Filters
        st.subheader("🔍 Filters")
        
        authors = fetch_authors()
        selected_author = st.selectbox(
            "Author",
            options=authors,
            index=0,
            help="Filter results by author"
        )
        
        statuses = fetch_statuses()
        selected_status = st.selectbox(
            "Status",
            options=statuses,
            index=0,
            help="Filter results by status"
        )
        
        st.divider()
        
        # Search parameters
        st.subheader("⚙️ Search Settings")
        
        alpha = st.slider(
            "Search Balance",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="0 = Keyword search, 1 = Semantic search"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.caption("🔤 Keyword")
        with col2:
            st.caption("🧠 Semantic")
        
        top_k = st.slider(
            "Top Results",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of results to retrieve"
        )
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Your query:",
            placeholder="e.g., What API features did Adnan work on?",
            help="Ask a question about the issues in natural language"
        )
    
    with col2:
        st.write("")  # Spacing
        search_button = st.button("🔍 Run", type="primary", use_container_width=True)
    
    # Perform search
    if search_button and query:
        st.session_state.last_query = query
        
        with st.spinner("🔎 Searching..."):
            start_time = time.time()
            results = perform_search(query, alpha, top_k, selected_author, selected_status)
            elapsed_time = time.time() - start_time
        
        st.session_state.search_results = results
        st.session_state.elapsed_time = elapsed_time
    
    # Display results
    if st.session_state.search_results:
        results = st.session_state.search_results
        
        if "error" in results:
            st.error(f"❌ {results['error']}")
        else:
            # Show search info
            st.success(f"✅ Found {results['total_results']} results in {st.session_state.elapsed_time:.2f}s")
            
            # Display generated answer
            if results.get('answer'):
                st.markdown("---")
                st.subheader("💡 Generated Answer")
                st.markdown(results['answer'])
            
            # Display retrieved documents
            st.markdown("---")
            st.subheader("📚 Retrieved Documents")
            
            if results['results']:
                for idx, result in enumerate(results['results']):
                    display_result(result, idx)
            else:
                st.info("No results found. Try adjusting your query or filters.")
    
    # Footer
    st.markdown("---")
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        ### 🎯 Tips for Better Results
        
        1. **Ask Natural Questions**: Use complete questions like "What features did Abbas work on?"
        2. **Use Filters**: Narrow down results by author or status
        3. **Adjust Search Balance**: 
           - Lower values (0-0.3): Better for exact keyword matches
           - Middle values (0.4-0.6): Balanced approach (recommended)
           - Higher values (0.7-1.0): Better for semantic/meaning-based search
        4. **Increase Top Results**: Get more context by retrieving more documents
        
        ### 🔍 Search Methods
        
        - **Keyword Search**: Finds exact word matches
        - **Semantic Search**: Understands meaning and context
        - **Hybrid Search**: Combines both methods for best results
        
        ### 💡 Example Queries
        
        - "Show calendar features by Abbas"
        - "What authentication work has been done?"
        - "Find closed issues about API improvements"
        - "List all features in progress"
        """)


if __name__ == "__main__":
    main()
