"""
Document Processing and Chunking Module
Converts CSV data into searchable chunks with metadata
"""
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class DocumentChunk:
    """Represents a single chunk of a document"""
    chunk_id: str
    issue_id: str
    content: str
    section: str  # "subject", "description", or "combined"
    metadata: Dict[str, str]
    

class DocumentProcessor:
    """Processes CSV documents into searchable chunks"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize the document processor
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load issues from CSV file"""
        df = pd.read_csv(file_path)
        # Clean column names
        df.columns = df.columns.str.strip()
        # Fill NaN values
        df = df.fillna("")
        return df
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not isinstance(text, str):
            text = str(text)
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might cause issues
        text = text.strip()
        return text
    
    def create_chunks_from_text(self, text: str, max_size: int) -> List[str]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to split
            max_size: Maximum size of each chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_size
            
            # If not at the end, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings
                last_period = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                last_space = text.rfind(' ', start, end)
                
                # Use the best break point
                break_point = max(last_period, last_newline, last_space)
                if break_point > start:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start <= end - max_size:
                start = end
        
        return chunks
    
    def create_issue_chunks(self, issue: pd.Series) -> List[DocumentChunk]:
        """
        Create chunks from a single issue
        
        Args:
            issue: A pandas Series representing one issue
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        issue_id = str(issue['id'])
        
        # Extract metadata
        metadata = {
            'issue_id': issue_id,
            'author': self.clean_text(issue['author']),
            'status': self.clean_text(issue['status']),
            'related_issues': self.clean_text(issue['related issues']),
            'subject': self.clean_text(issue['subject']),
        }
        
        # Create subject chunk (always keep as one chunk)
        subject = self.clean_text(issue['subject'])
        if subject:
            chunk_id = f"{issue_id}_subject_0"
            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                issue_id=issue_id,
                content=f"## Topic\n{subject}",
                section="subject",
                metadata=metadata.copy()
            ))
        
        # Create description chunks
        description = self.clean_text(issue['description'])
        if description:
            desc_chunks = self.create_chunks_from_text(description, self.chunk_size)
            for idx, desc_chunk in enumerate(desc_chunks):
                chunk_id = f"{issue_id}_description_{idx}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    issue_id=issue_id,
                    content=f"## Description\n{desc_chunk}",
                    section="description",
                    metadata=metadata.copy()
                ))
        
        # Create a combined chunk with full context (for better retrieval)
        combined_text = f"""ID: {issue_id}
Author: {metadata['author']}
Status: {metadata['status']}

## Topic
{subject}

## Description
{description[:500]}{'...' if len(description) > 500 else ''}

## Related Issues
{metadata['related_issues']}"""
        
        chunk_id = f"{issue_id}_combined_0"
        chunks.append(DocumentChunk(
            chunk_id=chunk_id,
            issue_id=issue_id,
            content=self.clean_text(combined_text),
            section="combined",
            metadata=metadata.copy()
        ))
        
        return chunks
    
    def process_dataframe(self, df: pd.DataFrame) -> List[DocumentChunk]:
        """
        Process entire dataframe into chunks
        
        Args:
            df: DataFrame containing issues
            
        Returns:
            List of all DocumentChunk objects
        """
        all_chunks = []
        
        for idx, issue in df.iterrows():
            try:
                issue_chunks = self.create_issue_chunks(issue)
                all_chunks.extend(issue_chunks)
            except Exception as e:
                print(f"Error processing issue {issue.get('id', idx)}: {e}")
                continue
        
        return all_chunks
    
    def process_file(self, file_path: str) -> List[DocumentChunk]:
        """
        Process a CSV file into chunks
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of all DocumentChunk objects
        """
        df = self.load_csv(file_path)
        print(f"Loaded {len(df)} issues from {file_path}")
        
        chunks = self.process_dataframe(df)
        print(f"Created {len(chunks)} chunks from {len(df)} issues")
        
        return chunks
    
    def get_statistics(self, chunks: List[DocumentChunk]) -> Dict:
        """Get statistics about the processed chunks"""
        total_chunks = len(chunks)
        unique_issues = len(set(chunk.issue_id for chunk in chunks))
        
        section_counts = {}
        for chunk in chunks:
            section_counts[chunk.section] = section_counts.get(chunk.section, 0) + 1
        
        authors = set(chunk.metadata['author'] for chunk in chunks)
        statuses = set(chunk.metadata['status'] for chunk in chunks)
        
        return {
            'total_chunks': total_chunks,
            'unique_issues': unique_issues,
            'chunks_per_issue': total_chunks / unique_issues if unique_issues > 0 else 0,
            'section_counts': section_counts,
            'unique_authors': len(authors),
            'unique_statuses': len(statuses),
            'authors': sorted(authors),
            'statuses': sorted(statuses),
        }


if __name__ == "__main__":
    # Test the document processor
    from config import Config
    
    processor = DocumentProcessor(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    
    chunks = processor.process_file(Config.DATA_PATH)
    stats = processor.get_statistics(chunks)
    
    print("\n=== Document Processing Statistics ===")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Unique issues: {stats['unique_issues']}")
    print(f"Average chunks per issue: {stats['chunks_per_issue']:.2f}")
    print(f"\nSection breakdown:")
    for section, count in stats['section_counts'].items():
        print(f"  {section}: {count}")
    print(f"\nUnique authors: {stats['unique_authors']}")
    print(f"Unique statuses: {stats['unique_statuses']}")
    
    # Show example chunks
    print("\n=== Example Chunks ===")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1}:")
        print(f"ID: {chunk.chunk_id}")
        print(f"Issue: {chunk.issue_id}")
        print(f"Section: {chunk.section}")
        print(f"Content preview: {chunk.content[:200]}...")
