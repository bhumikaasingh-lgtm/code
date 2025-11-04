"""
FastAPI Backend for RAG System
Provides REST API endpoints for search and retrieval
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
from contextlib import asynccontextmanager

from config import Config
from weaviate_client import WeaviateManager
from embeddings import EmbeddingModel
from llm_generator import LLMGenerator


# Global instances
weaviate_manager = None
embedding_model = None
llm_generator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app"""
    global weaviate_manager, embedding_model, llm_generator
    
    print("🚀 Starting RAG System Backend...")
    
    # Initialize components
    try:
        weaviate_manager = WeaviateManager()
        weaviate_manager.connect()
        print("✓ Weaviate connected")
        
        embedding_model = EmbeddingModel()
        print("✓ Embedding model loaded")
        
        llm_generator = LLMGenerator()
        print("✓ LLM generator initialized")
        
        print("✅ Backend ready!")
        
    except Exception as e:
        print(f"❌ Failed to initialize backend: {e}")
        raise
    
    yield
    
    # Cleanup
    if weaviate_manager:
        weaviate_manager.disconnect()
    print("👋 Backend shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Catch - RAG System API",
    description="Unified Story Retriever: Multiple management tools in. One RAG pipeline out.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    query: str = Field(..., description="Search query")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="Hybrid search balance (0=keyword, 1=semantic)")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    author: Optional[str] = Field(None, description="Filter by author")
    status: Optional[str] = Field(None, description="Filter by status")
    generate_answer: bool = Field(True, description="Whether to generate an answer")


class SearchResult(BaseModel):
    """Model for a single search result"""
    chunk_id: str
    issue_id: str
    content: str
    section: str
    author: str
    status: str
    subject: str
    related_issues: str
    score: float


class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    query: str
    results: List[SearchResult]
    answer: Optional[str] = None
    total_results: int
    search_params: Dict[str, Any]


class StatsResponse(BaseModel):
    """Response model for stats endpoint"""
    total_chunks: int
    collection_name: str
    authors: List[str]
    statuses: List[str]


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Catch - Unified Story Retriever API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Weaviate connection
        stats = weaviate_manager.get_collection_stats()
        
        return {
            "status": "healthy",
            "weaviate": "connected",
            "embedding_model": embedding_model.model_name,
            "llm_model": llm_generator.model_name,
            "total_chunks": stats['total_objects']
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Perform hybrid search and optionally generate an answer
    
    Args:
        request: SearchRequest with query and parameters
        
    Returns:
        SearchResponse with results and optional generated answer
    """
    try:
        # Generate query embedding
        query_embedding = embedding_model.encode_query(request.query)
        
        # Build filters
        filters = {}
        if request.author and request.author != "All":
            filters['author'] = request.author
        if request.status and request.status != "All":
            filters['status'] = request.status
        
        # Perform hybrid search
        results = weaviate_manager.hybrid_search(
            query=request.query,
            query_embedding=query_embedding,
            alpha=request.alpha,
            limit=request.top_k,
            filters=filters if filters else None
        )
        
        # Convert to SearchResult objects
        search_results = [SearchResult(**result) for result in results]
        
        # Generate answer if requested
        answer = None
        if request.generate_answer and results:
            answer = llm_generator.generate(request.query, results)
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            answer=answer,
            total_results=len(search_results),
            search_params={
                "alpha": request.alpha,
                "top_k": request.top_k,
                "author_filter": request.author,
                "status_filter": request.status,
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics"""
    try:
        stats = weaviate_manager.get_collection_stats()
        authors = weaviate_manager.get_all_authors()
        statuses = weaviate_manager.get_all_statuses()
        
        return StatsResponse(
            total_chunks=stats['total_objects'],
            collection_name=stats['collection_name'],
            authors=authors,
            statuses=statuses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/authors")
async def get_authors():
    """Get list of all authors"""
    try:
        authors = weaviate_manager.get_all_authors()
        return {"authors": authors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get authors: {str(e)}")


@app.get("/statuses")
async def get_statuses():
    """Get list of all statuses"""
    try:
        statuses = weaviate_manager.get_all_statuses()
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statuses: {str(e)}")


if __name__ == "__main__":
    print("🚀 Starting Catch RAG System Backend...")
    print(f"📊 Backend URL: http://{Config.BACKEND_HOST}:{Config.BACKEND_PORT}")
    print(f"📚 API Docs: http://{Config.BACKEND_HOST}:{Config.BACKEND_PORT}/docs")
    
    uvicorn.run(
        "backend:app",
        host=Config.BACKEND_HOST,
        port=Config.BACKEND_PORT,
        reload=False,
        log_level="info"
    )
