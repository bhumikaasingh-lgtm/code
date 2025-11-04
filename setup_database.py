"""
Database Setup Script
Process documents, create embeddings, and populate Weaviate
"""
import sys
import time
from config import Config
from document_processor import DocumentProcessor
from embeddings import create_embeddings_for_chunks
from weaviate_client import setup_database


def main():
    """Main setup function"""
    print("="*60)
    print("🚀 RAG SYSTEM DATABASE SETUP")
    print("="*60)
    print()
    
    start_time = time.time()
    
    # Step 1: Process documents
    print("📄 STEP 1: Processing Documents")
    print("-" * 60)
    processor = DocumentProcessor(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    
    try:
        chunks = processor.process_file(Config.DATA_PATH)
        stats = processor.get_statistics(chunks)
        
        print(f"\n✅ Processing complete!")
        print(f"   • Total chunks: {stats['total_chunks']}")
        print(f"   • Unique issues: {stats['unique_issues']}")
        print(f"   • Avg chunks per issue: {stats['chunks_per_issue']:.2f}")
        print(f"   • Unique authors: {stats['unique_authors']}")
        print(f"   • Unique statuses: {stats['unique_statuses']}")
        
    except Exception as e:
        print(f"\n❌ Error processing documents: {e}")
        sys.exit(1)
    
    # Step 2: Create embeddings
    print("\n🧠 STEP 2: Creating Embeddings")
    print("-" * 60)
    
    try:
        embeddings = create_embeddings_for_chunks(chunks, batch_size=32)
        print(f"✅ Created {len(embeddings)} embeddings")
        
    except Exception as e:
        print(f"\n❌ Error creating embeddings: {e}")
        sys.exit(1)
    
    # Step 3: Setup Weaviate database
    print("\n🗄️  STEP 3: Setting up Weaviate Database")
    print("-" * 60)
    
    try:
        setup_database(chunks, embeddings)
        
    except Exception as e:
        print(f"\n❌ Error setting up database: {e}")
        sys.exit(1)
    
    # Done
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print(f"✅ DATABASE SETUP COMPLETE!")
    print(f"⏱️  Total time: {elapsed:.2f} seconds")
    print("="*60)
    print()
    print("Next steps:")
    print("  1. Start the backend: python backend.py")
    print("  2. Start the frontend: streamlit run frontend.py")
    print("  3. Open your browser to the Streamlit URL")
    print()


if __name__ == "__main__":
    main()
