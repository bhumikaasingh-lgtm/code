"""
LLM Generator Module
Generates answers based on retrieved context using Llama 3 or GPT-4
"""
from typing import List, Dict, Optional
import os
from config import Config


class LLMGenerator:
    """Generates answers using Large Language Models"""
    
    def __init__(self, use_openai: bool = None, model_name: str = None):
        """
        Initialize the LLM generator
        
        Args:
            use_openai: Whether to use OpenAI (True) or local model (False)
            model_name: Name of the model to use
        """
        self.use_openai = use_openai if use_openai is not None else Config.USE_OPENAI
        self.model_name = model_name or Config.LLM_MODEL_NAME
        
        if self.use_openai:
            self._init_openai()
        else:
            self._init_huggingface()
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            print(f"✓ Initialized OpenAI with model: {self.model_name}")
        except Exception as e:
            print(f"✗ Failed to initialize OpenAI: {e}")
            raise
    
    def _init_huggingface(self):
        """Initialize HuggingFace model"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            import torch
            
            print(f"Loading HuggingFace model: {self.model_name}...")
            
            # Determine device
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device != "cpu" else torch.float32,
                device_map="auto" if device != "cpu" else None,
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device if device == "cpu" else 0,
            )
            
            print(f"✓ Initialized HuggingFace model on {device}")
            
        except Exception as e:
            print(f"✗ Failed to initialize HuggingFace model: {e}")
            raise
    
    def create_prompt(self, query: str, contexts: List[Dict]) -> str:
        """
        Create a prompt for the LLM with query and retrieved contexts
        
        Args:
            query: User's question
            contexts: List of retrieved document chunks
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an intelligent assistant helping users find information from project management issues.

Your task is to answer the user's question based ONLY on the provided context documents. Follow these rules:

1. Answer the question using information from the context documents
2. If multiple issues are relevant, organize the answer by issue
3. Always cite the issue ID, author, and status when referencing information
4. Use markdown formatting for better readability
5. If the context doesn't contain enough information to answer the question, say so clearly
6. Do NOT make up or infer information that's not in the context
7. Be concise but complete

Context Documents:
"""
        
        for i, ctx in enumerate(contexts, 1):
            prompt += f"""
---
Context {i}:
Issue ID: {ctx['issue_id']}
Author: {ctx['author']}
Status: {ctx['status']}
Subject: {ctx['subject']}

{ctx['content']}
"""
        
        prompt += f"""
---

User Question: {query}

Please provide a clear, well-organized answer based on the context above. Include issue IDs, authors, and status in your response.

Answer:"""
        
        return prompt
    
    def generate_openai(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate answer using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more factual responses
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Error generating response: {e}"
    
    def generate_huggingface(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate answer using HuggingFace model"""
        try:
            # Format prompt for chat models
            if "instruct" in self.model_name.lower() or "chat" in self.model_name.lower():
                formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            else:
                formatted_prompt = prompt
            
            outputs = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_tokens,
                temperature=0.3,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
            )
            
            generated_text = outputs[0]['generated_text']
            
            # Extract only the assistant's response
            if "<|start_header_id|>assistant<|end_header_id|>" in generated_text:
                response = generated_text.split("<|start_header_id|>assistant<|end_header_id|>")[-1]
                response = response.split("<|eot_id|>")[0].strip()
            else:
                # For non-chat models, remove the prompt
                response = generated_text[len(formatted_prompt):].strip()
            
            return response
        
        except Exception as e:
            return f"Error generating response: {e}"
    
    def generate(self, query: str, contexts: List[Dict], max_tokens: int = 1000) -> str:
        """
        Generate an answer to the query based on retrieved contexts
        
        Args:
            query: User's question
            contexts: List of retrieved document chunks
            max_tokens: Maximum tokens in the response
            
        Returns:
            Generated answer string
        """
        if not contexts:
            return "No relevant information found in the database. Please try a different query or check if the database is populated."
        
        prompt = self.create_prompt(query, contexts)
        
        if self.use_openai:
            return self.generate_openai(prompt, max_tokens)
        else:
            return self.generate_huggingface(prompt, max_tokens)


if __name__ == "__main__":
    # Test the LLM generator
    print("=== Testing LLM Generator ===\n")
    
    # Sample contexts
    sample_contexts = [
        {
            'issue_id': '315',
            'author': 'Adnan Topçu',
            'status': 'Closed',
            'subject': 'API Filtering Improvements',
            'content': 'Users need better filtering options for API calls to reduce data transfer and improve performance. Implementation includes query parameters and pagination.',
        },
        {
            'issue_id': '412',
            'author': 'Adnan Topçu',
            'status': 'New',
            'subject': 'API Rate Limiting',
            'content': 'Add rate limiting per API key to prevent abuse and ensure fair usage across all users.',
        }
    ]
    
    sample_query = "What API features did Adnan work on?"
    
    generator = LLMGenerator()
    
    print(f"Query: {sample_query}\n")
    print("Generating answer...\n")
    
    answer = generator.generate(sample_query, sample_contexts, max_tokens=500)
    
    print("="*60)
    print("ANSWER:")
    print("="*60)
    print(answer)
    print("="*60)
