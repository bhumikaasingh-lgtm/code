"""
Weaviate Database Integration
Handles vector database operations for storing and retrieving document chunks
"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter, MetadataQuery
from typing import List, Dict, Optional, Any
import time
from config import Config
from document_processor import DocumentChunk


class WeaviateManager:
    """Manages Weaviate vector database operations"""
    
    def __init__(self, url: str = None, api_key: str = None):
        """
        Initialize Weaviate client
        
        Args:
            url: Weaviate instance URL
            api_key: Optional API key for authentication
        """
        self.url = url or Config.WEAVIATE_URL
        self.api_key = api_key or Config.WEAVIATE_API_KEY
        self.class_name = Config.WEAVIATE_CLASS_NAME
        self.client = None
        
    def connect(self):
        """Establish connection to Weaviate"""
        try:
            if self.api_key:
                self.client = weaviate.connect_to_wcs(
                    cluster_url=self.url,
                    auth_credentials=weaviate.auth.AuthApiKey(self.api_key),
                )
            else:
                self.client = weaviate.connect_to_local(host=self.url.replace("http://", "").replace("https://", "").split(":")[0])
            
            print(f"✓ Connected to Weaviate at {self.url}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Weaviate: {e}")
            raise
    
    def disconnect(self):
        """Close connection to Weaviate"""
        if self.client:
            self.client.close()
            print("✓ Disconnected from Weaviate")
    
    def create_schema(self, delete_if_exists: bool = False):
        """
        Create the schema for storing issue chunks
        
        Args:
            delete_if_exists: If True, delete existing collection first
        """
        try:
            # Check if collection exists
            if self.client.collections.exists(self.class_name):
                if delete_if_exists:
                    self.client.collections.delete(self.class_name)
                    print(f"✓ Deleted existing collection: {self.class_name}")
                else:
                    print(f"✓ Collection already exists: {self.class_name}")
                    return
            
            # Create collection with properties
            self.client.collections.create(
                name=self.class_name,
                vectorizer_config=Configure.Vectorizer.none(),  # We'll provide our own vectors
                properties=[
                    Property(name="chunk_id", data_type=DataType.TEXT),
                    Property(name="issue_id", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="section", data_type=DataType.TEXT),
                    Property(name="author", data_type=DataType.TEXT),
                    Property(name="status", data_type=DataType.TEXT),
                    Property(name="related_issues", data_type=DataType.TEXT),
                    Property(name="subject", data_type=DataType.TEXT),
                ],
            )
            
            print(f"✓ Created collection: {self.class_name}")
            
        except Exception as e:
            print(f"✗ Error creating schema: {e}")
            raise
    
    def insert_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]], batch_size: int = 100):
        """
        Insert document chunks with their embeddings into Weaviate
        
        Args:
            chunks: List of DocumentChunk objects
            embeddings: List of embedding vectors (same order as chunks)
            batch_size: Number of objects to insert per batch
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have same length")
        
        collection = self.client.collections.get(self.class_name)
        
        print(f"Inserting {len(chunks)} chunks into Weaviate...")
        start_time = time.time()
        
        # Insert in batches
        with collection.batch.dynamic() as batch:
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                properties = {
                    "chunk_id": chunk.chunk_id,
                    "issue_id": chunk.issue_id,
                    "content": chunk.content,
                    "section": chunk.section,
                    "author": chunk.metadata['author'],
                    "status": chunk.metadata['status'],
                    "related_issues": chunk.metadata['related_issues'],
                    "subject": chunk.metadata['subject'],
                }
                
                batch.add_object(
                    properties=properties,
                    vector=embedding
                )
                
                if (idx + 1) % batch_size == 0:
                    print(f"  Inserted {idx + 1}/{len(chunks)} chunks")
        
        elapsed = time.time() - start_time
        print(f"✓ Inserted {len(chunks)} chunks in {elapsed:.2f}s")
    
    def hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        alpha: float = 0.5,
        limit: int = 5,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (keyword + semantic)
        
        Args:
            query: Text query for keyword search
            query_embedding: Vector embedding for semantic search
            alpha: Balance between keyword (0) and semantic (1) search
            limit: Number of results to return
            filters: Optional filters (author, status, etc.)
            
        Returns:
            List of search results with scores and metadata
        """
        collection = self.client.collections.get(self.class_name)
        
        # Build filter if provided
        filter_obj = None
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if value and value != "All":
                    filter_conditions.append(Filter.by_property(key).equal(value))
            
            if filter_conditions:
                filter_obj = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    filter_obj = filter_obj & condition
        
        # Perform hybrid search
        response = collection.query.hybrid(
            query=query,
            vector=query_embedding,
            alpha=alpha,
            limit=limit,
            filters=filter_obj,
            return_metadata=MetadataQuery(score=True, distance=True)
        )
        
        # Format results
        results = []
        for obj in response.objects:
            results.append({
                'chunk_id': obj.properties['chunk_id'],
                'issue_id': obj.properties['issue_id'],
                'content': obj.properties['content'],
                'section': obj.properties['section'],
                'author': obj.properties['author'],
                'status': obj.properties['status'],
                'related_issues': obj.properties['related_issues'],
                'subject': obj.properties['subject'],
                'score': obj.metadata.score if obj.metadata.score else 0.0,
            })
        
        return results
    
    def get_all_authors(self) -> List[str]:
        """Get list of all unique authors"""
        collection = self.client.collections.get(self.class_name)
        
        # Aggregate to get unique authors
        response = collection.aggregate.over_all(
            group_by="author"
        )
        
        authors = sorted([group.grouped_by.value for group in response.groups])
        return authors
    
    def get_all_statuses(self) -> List[str]:
        """Get list of all unique statuses"""
        collection = self.client.collections.get(self.class_name)
        
        # Aggregate to get unique statuses
        response = collection.aggregate.over_all(
            group_by="status"
        )
        
        statuses = sorted([group.grouped_by.value for group in response.groups])
        return statuses
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        collection = self.client.collections.get(self.class_name)
        
        # Get total count
        response = collection.aggregate.over_all(
            total_count=True
        )
        
        return {
            'total_objects': response.total_count,
            'collection_name': self.class_name,
        }
    
    def delete_collection(self):
        """Delete the entire collection"""
        try:
            self.client.collections.delete(self.class_name)
            print(f"✓ Deleted collection: {self.class_name}")
        except Exception as e:
            print(f"✗ Error deleting collection: {e}")


def setup_database(chunks: List[DocumentChunk], embeddings: List[List[float]]):
    """
    Setup Weaviate database with chunks and embeddings
    
    Args:
        chunks: List of document chunks
        embeddings: List of embedding vectors
    """
    manager = WeaviateManager()
    
    try:
        manager.connect()
        manager.create_schema(delete_if_exists=True)
        manager.insert_chunks(chunks, embeddings)
        
        stats = manager.get_collection_stats()
        print(f"\n✓ Database setup complete!")
        print(f"  Total objects: {stats['total_objects']}")
        
    finally:
        manager.disconnect()


if __name__ == "__main__":
    # Test Weaviate connection
    manager = WeaviateManager()
    
    try:
        manager.connect()
        print("✓ Weaviate connection test successful")
        
        # Try to get stats if collection exists
        if manager.client.collections.exists(Config.WEAVIATE_CLASS_NAME):
            stats = manager.get_collection_stats()
            print(f"✓ Collection exists with {stats['total_objects']} objects")
        else:
            print("ℹ Collection does not exist yet")
        
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
    finally:
        manager.disconnect()
