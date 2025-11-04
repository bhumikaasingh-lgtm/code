"""
Embedding Pipeline using e5-large-v2
Converts text into vector embeddings for semantic search
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import torch
import numpy as np
from config import Config


class EmbeddingModel:
    """Handles text-to-vector embedding generation"""
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Initialize the embedding model
        
        Args:
            model_name: Name of the sentence transformer model
            device: Device to run model on ('cpu', 'cuda', or 'mps')
        """
        self.model_name = model_name or Config.EMBEDDING_MODEL_NAME
        self.device = device or Config.EMBEDDING_DEVICE
        
        # Auto-detect device if not specified
        if self.device == "cpu":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
        
        print(f"Loading embedding model: {self.model_name} on {self.device}...")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        print(f"✓ Embedding model loaded (dimension: {self.model.get_sentence_embedding_dimension()})")
    
    def encode_query(self, query: str) -> List[float]:
        """
        Encode a search query into an embedding
        
        For e5 models, queries should be prefixed with "query: "
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector as list of floats
        """
        # E5 models use special prefixes for better performance
        if "e5" in self.model_name.lower():
            query = f"query: {query}"
        
        embedding = self.model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()
    
    def encode_documents(self, documents: List[str], batch_size: int = 32, show_progress: bool = True) -> List[List[float]]:
        """
        Encode multiple documents into embeddings
        
        For e5 models, documents should be prefixed with "passage: "
        
        Args:
            documents: List of document texts
            batch_size: Number of documents to process at once
            show_progress: Whether to show progress bar
            
        Returns:
            List of embedding vectors
        """
        # E5 models use special prefixes for better performance
        if "e5" in self.model_name.lower():
            documents = [f"passage: {doc}" for doc in documents]
        
        embeddings = self.model.encode(
            documents,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        return self.model.get_sentence_embedding_dimension()
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)


def create_embeddings_for_chunks(chunks: List, batch_size: int = 32) -> List[List[float]]:
    """
    Create embeddings for a list of document chunks
    
    Args:
        chunks: List of DocumentChunk objects or strings
        batch_size: Batch size for encoding
        
    Returns:
        List of embedding vectors
    """
    model = EmbeddingModel()
    
    # Extract text content from chunks
    if hasattr(chunks[0], 'content'):
        texts = [chunk.content for chunk in chunks]
    else:
        texts = chunks
    
    print(f"Creating embeddings for {len(texts)} chunks...")
    embeddings = model.encode_documents(texts, batch_size=batch_size)
    print(f"✓ Created {len(embeddings)} embeddings")
    
    return embeddings


if __name__ == "__main__":
    # Test the embedding model
    model = EmbeddingModel()
    
    print("\n=== Testing Embedding Model ===")
    
    # Test query encoding
    query = "API authentication features"
    query_embedding = model.encode_query(query)
    print(f"\nQuery: '{query}'")
    print(f"Embedding dimension: {len(query_embedding)}")
    print(f"Embedding sample (first 5 values): {query_embedding[:5]}")
    
    # Test document encoding
    documents = [
        "Implement JWT authentication for API endpoints",
        "Add user registration and login functionality",
        "Create calendar view for project timeline",
    ]
    
    doc_embeddings = model.encode_documents(documents, show_progress=False)
    print(f"\nEncoded {len(documents)} documents")
    
    # Test similarity
    print("\n=== Similarity Scores ===")
    for i, doc in enumerate(documents):
        similarity = model.compute_similarity(query_embedding, doc_embeddings[i])
        print(f"Query vs '{doc[:50]}...': {similarity:.4f}")
    
    print("\n✓ Embedding model test complete!")
