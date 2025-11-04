"""
RAGAS Evaluation Module
Evaluates RAG system quality using RAGAS metrics
"""
from typing import List, Dict, Any
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy,
)

from config import Config
from weaviate_client import WeaviateManager
from embeddings import EmbeddingModel
from llm_generator import LLMGenerator


class RAGASEvaluator:
    """Evaluates RAG system using RAGAS metrics"""
    
    def __init__(self):
        """Initialize the RAGAS evaluator"""
        self.weaviate_manager = WeaviateManager()
        self.embedding_model = EmbeddingModel()
        self.llm_generator = LLMGenerator()
        
        # Define test cases
        self.test_cases = self.create_test_cases()
    
    def create_test_cases(self) -> List[Dict[str, str]]:
        """
        Create test cases for evaluation
        
        Returns:
            List of test case dictionaries with question and ground_truth
        """
        return [
            {
                "question": "What features involve keyboard shortcuts?",
                "ground_truth": "Motohiro Takayama proposed keyboard shortcuts for Redmine similar to Trac, including Ctrl+R for preview, Ctrl+S to submit, and Ctrl+/ for search. The implementation involves adding accesskey attributes to elements."
            },
            {
                "question": "Show issues about importing from JIRA",
                "ground_truth": "Charles L created a script for importing from JIRA (migrate_from_jira.rake) that imports projects, sub-projects, users, issue categories, issues, and issue comments from JIRA XML dumps."
            },
            {
                "question": "What features are related to time tracking?",
                "ground_truth": "ilenia zara proposed the ability to vary units for time tracking to support points or tomatoes. Michael Pirogov suggested the ability to move or delete timelog entries between projects."
            },
            {
                "question": "Find issues about filtering",
                "ground_truth": "Paolo Sulprizio requested filtering using more than one instance of each field, such as issues with subject containing 'email' but not containing 'server'."
            },
            {
                "question": "What work has been done on issue assignment?",
                "ground_truth": "João Saleiro proposed the ability to assign a task to multiple users and have a 'being solved' state where the first available worker can grab the task and lock it to themselves."
            },
        ]
    
    def run_test_case(self, test_case: Dict[str, str], alpha: float = 0.5, top_k: int = 5) -> Dict[str, Any]:
        """
        Run a single test case through the RAG pipeline
        
        Args:
            test_case: Test case with question and ground_truth
            alpha: Hybrid search balance
            top_k: Number of results to retrieve
            
        Returns:
            Dictionary with question, contexts, answer, and ground_truth
        """
        question = test_case["question"]
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode_query(question)
        
        # Retrieve contexts
        results = self.weaviate_manager.hybrid_search(
            query=question,
            query_embedding=query_embedding,
            alpha=alpha,
            limit=top_k,
            filters=None
        )
        
        # Extract contexts
        contexts = [result['content'] for result in results]
        
        # Generate answer
        answer = self.llm_generator.generate(question, results)
        
        return {
            "question": question,
            "contexts": contexts,
            "answer": answer,
            "ground_truth": test_case["ground_truth"]
        }
    
    def evaluate(self, alpha: float = 0.5, top_k: int = 5) -> Dict[str, float]:
        """
        Evaluate the RAG system using RAGAS metrics
        
        Args:
            alpha: Hybrid search balance for test queries
            top_k: Number of results to retrieve
            
        Returns:
            Dictionary with metric scores
        """
        print("🔍 Running RAGAS Evaluation...")
        print(f"Test cases: {len(self.test_cases)}")
        print(f"Parameters: alpha={alpha}, top_k={top_k}\n")
        
        # Connect to Weaviate
        self.weaviate_manager.connect()
        
        try:
            # Run all test cases
            results = []
            for i, test_case in enumerate(self.test_cases, 1):
                print(f"Running test case {i}/{len(self.test_cases)}: {test_case['question'][:50]}...")
                result = self.run_test_case(test_case, alpha, top_k)
                results.append(result)
            
            # Convert to Dataset format for RAGAS
            data = {
                "question": [r["question"] for r in results],
                "contexts": [r["contexts"] for r in results],
                "answer": [r["answer"] for r in results],
                "ground_truth": [r["ground_truth"] for r in results],
            }
            
            dataset = Dataset.from_dict(data)
            
            # Run RAGAS evaluation
            print("\n📊 Calculating RAGAS metrics...")
            
            try:
                evaluation_result = evaluate(
                    dataset,
                    metrics=[
                        context_precision,
                        context_recall,
                        faithfulness,
                        answer_relevancy,
                    ],
                )
                
                # Extract scores
                scores = {
                    "context_precision": evaluation_result["context_precision"],
                    "context_recall": evaluation_result["context_recall"],
                    "faithfulness": evaluation_result["faithfulness"],
                    "answer_relevancy": evaluation_result["answer_relevancy"],
                }
                
                # Calculate average
                scores["average"] = sum(scores.values()) / len(scores)
                
                return scores
                
            except Exception as e:
                print(f"⚠️ RAGAS evaluation failed: {e}")
                print("Falling back to manual evaluation...")
                
                # Fallback: Simple relevance scoring
                scores = self.manual_evaluation(results)
                return scores
            
        finally:
            self.weaviate_manager.disconnect()
    
    def manual_evaluation(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Manual evaluation fallback when RAGAS fails
        
        Args:
            results: List of test case results
            
        Returns:
            Dictionary with estimated metric scores
        """
        print("Running manual evaluation...")
        
        scores = {
            "context_precision": 0.0,
            "context_recall": 0.0,
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
        }
        
        for result in results:
            # Simple heuristics
            
            # Context precision: Did we get non-empty contexts?
            if result["contexts"] and len(result["contexts"]) > 0:
                scores["context_precision"] += 1.0
            
            # Context recall: Are contexts relevant to question?
            question_words = set(result["question"].lower().split())
            context_text = " ".join(result["contexts"]).lower()
            overlap = len([w for w in question_words if w in context_text])
            scores["context_recall"] += min(overlap / max(len(question_words), 1), 1.0)
            
            # Faithfulness: Does answer reference the contexts?
            answer_words = set(result["answer"].lower().split())
            context_words = set(context_text.split())
            common_words = answer_words & context_words
            scores["faithfulness"] += len(common_words) / max(len(answer_words), 1)
            
            # Answer relevancy: Does answer relate to question?
            answer_text = result["answer"].lower()
            relevance = len([w for w in question_words if w in answer_text])
            scores["answer_relevancy"] += min(relevance / max(len(question_words), 1), 1.0)
        
        # Average across test cases
        n = len(results)
        for key in scores:
            scores[key] /= n
        
        scores["average"] = sum(scores.values()) / len(scores)
        
        return scores
    
    def print_report(self, scores: Dict[str, float]):
        """
        Print evaluation report
        
        Args:
            scores: Dictionary with metric scores
        """
        print("\n" + "="*60)
        print("📊 RAGAS EVALUATION REPORT")
        print("="*60)
        
        metrics = [
            ("Context Precision", scores.get("context_precision", 0.0)),
            ("Context Recall", scores.get("context_recall", 0.0)),
            ("Faithfulness", scores.get("faithfulness", 0.0)),
            ("Answer Relevancy", scores.get("answer_relevancy", 0.0)),
        ]
        
        for metric_name, score in metrics:
            grade = self.get_grade(score)
            bar = self.get_bar(score)
            print(f"{metric_name:20} {bar} {score:.3f} {grade}")
        
        print("-"*60)
        avg_score = scores.get("average", 0.0)
        avg_grade = self.get_grade(avg_score)
        print(f"{'Average':20} {self.get_bar(avg_score)} {avg_score:.3f} {avg_grade}")
        print("="*60)
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if scores.get("context_precision", 0) < 0.7:
            print("  • Increase retrieval limit (top_k) for better precision")
        if scores.get("context_recall", 0) < 0.7:
            print("  • Adjust search balance (alpha) to favor semantic search")
        if scores.get("faithfulness", 0) < 0.7:
            print("  • Improve LLM prompt to reduce hallucination")
        if scores.get("answer_relevancy", 0) < 0.7:
            print("  • Refine retrieval to get more relevant contexts")
        
        if all(score >= 0.7 for score in scores.values()):
            print("  ✅ All metrics are performing well!")
    
    def get_grade(self, score: float) -> str:
        """Get letter grade for a score"""
        if score >= 0.9:
            return "✅ Excellent"
        elif score >= 0.75:
            return "✅ Good"
        elif score >= 0.6:
            return "⚠️  Fair"
        else:
            return "❌ Needs Improvement"
    
    def get_bar(self, score: float, width: int = 20) -> str:
        """Get visual bar for a score"""
        filled = int(score * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"|{bar}|"


def run_evaluation(alpha: float = 0.5, top_k: int = 5):
    """
    Run RAGAS evaluation and print report
    
    Args:
        alpha: Hybrid search balance
        top_k: Number of results to retrieve
    """
    evaluator = RAGASEvaluator()
    scores = evaluator.evaluate(alpha=alpha, top_k=top_k)
    evaluator.print_report(scores)
    
    return scores


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    alpha = 0.5
    top_k = 5
    
    if len(sys.argv) > 1:
        alpha = float(sys.argv[1])
    if len(sys.argv) > 2:
        top_k = int(sys.argv[2])
    
    print("🎯 RAGAS Evaluation for RAG System")
    print(f"Parameters: alpha={alpha}, top_k={top_k}\n")
    
    run_evaluation(alpha=alpha, top_k=top_k)
