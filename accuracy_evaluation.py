"""
Accuracy Evaluation System for Meeting RAG System with LLM Integration
This script evaluates the retrieval accuracy and LLM generation quality.
"""

import json
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any, Tuple
from phase3_rag_system import MeetingRAGSystem

class AccuracyEvaluator:
    def __init__(self):
        self.rag_system = MeetingRAGSystem()
        self.ground_truth_queries = self._create_ground_truth_dataset()
        
    def _create_ground_truth_dataset(self) -> List[Dict[str, Any]]:
        """Create a ground truth dataset for evaluation."""
        return [
            {
                "query": "What are the key product development priorities?",
                "expected_types": ["minute", "key_insight"],
                "expected_speakers": ["Arjun Vasanth", "Vikram Malhotra"],
                "expected_keywords": ["product", "development", "priority", "roadmap", "strategy"],
                "category": "product_strategy"
            },
            {
                "query": "Show me high priority action items",
                "expected_types": ["action_item"],
                "expected_keywords": ["high", "priority", "urgent", "deadline", "task"],
                "category": "action_items"
            },
            {
                "query": "What did Arjun discuss about funding and investment?",
                "expected_types": ["minute"],
                "expected_speakers": ["Arjun Vasanth"],
                "expected_keywords": ["funding", "investment", "capital", "money", "investor"],
                "category": "funding"
            },
            {
                "query": "Which meetings discussed regulatory compliance?",
                "expected_types": ["minute", "key_insight"],
                "expected_keywords": ["regulatory", "compliance", "regulation", "legal", "policy"],
                "category": "compliance"
            },
            {
                "query": "What are the main concerns about market expansion?",
                "expected_types": ["minute", "key_insight"],
                "expected_keywords": ["market", "expansion", "growth", "scale", "risk"],
                "category": "market_strategy"
            },
            {
                "query": "Show me insights about competitive analysis",
                "expected_types": ["key_insight", "minute"],
                "expected_keywords": ["competitive", "competition", "competitor", "analysis", "market"],
                "category": "competition"
            },
            {
                "query": "What action items are assigned to technical team?",
                "expected_types": ["action_item"],
                "expected_keywords": ["technical", "tech", "development", "engineering", "implement"],
                "category": "technical_tasks"
            },
            {
                "query": "Which meetings had discussions about AI integration?",
                "expected_types": ["minute", "key_insight"],
                "expected_keywords": ["AI", "artificial intelligence", "integration", "technology", "automation"],
                "category": "ai_technology"
            },
            {
                "query": "What are the key risks identified in recent meetings?",
                "expected_types": ["key_insight", "minute"],
                "expected_keywords": ["risk", "concern", "challenge", "issue", "problem"],
                "category": "risk_management"
            },
            {
                "query": "Show me decisions made about product roadmap",
                "expected_types": ["minute", "key_insight"],
                "expected_keywords": ["decision", "roadmap", "timeline", "milestone", "plan"],
                "category": "product_planning"
            }
        ]
    
    def evaluate_relevance(self, query_data: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate the relevance of search results for a given query."""
        if not results:
            return {"type_accuracy": 0.0, "keyword_relevance": 0.0, "speaker_accuracy": 0.0, "overall_relevance": 0.0}
        
        # Type accuracy: percentage of results matching expected types
        type_matches = 0
        if "expected_types" in query_data:
            for result in results:
                if result["type"] in query_data["expected_types"]:
                    type_matches += 1
            type_accuracy = type_matches / len(results)
        else:
            type_accuracy = 1.0  # No type constraint
        
        # Keyword relevance: percentage of results containing expected keywords
        keyword_matches = 0
        if "expected_keywords" in query_data:
            for result in results:
                text = result["text"].lower()
                for keyword in query_data["expected_keywords"]:
                    if keyword.lower() in text:
                        keyword_matches += 1
                        break  # Count each result only once
            keyword_relevance = keyword_matches / len(results)
        else:
            keyword_relevance = 1.0  # No keyword constraint
        
        # Speaker accuracy: percentage of results from expected speakers
        speaker_matches = 0
        if "expected_speakers" in query_data:
            for result in results:
                if result["speaker"] in query_data["expected_speakers"]:
                    speaker_matches += 1
            speaker_accuracy = speaker_matches / len(results) if results else 0.0
        else:
            speaker_accuracy = 1.0  # No speaker constraint
        
        # Overall relevance (weighted average)
        overall_relevance = (type_accuracy * 0.3 + keyword_relevance * 0.5 + speaker_accuracy * 0.2)
        
        return {
            "type_accuracy": type_accuracy,
            "keyword_relevance": keyword_relevance,
            "speaker_accuracy": speaker_accuracy,
            "overall_relevance": overall_relevance
        }
    
    def evaluate_ranking_quality(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate the quality of result ranking based on scores."""
        if len(results) < 2:
            return {"score_monotonicity": 1.0, "score_distribution": 1.0}
        
        # Check if scores are in descending order (monotonicity)
        scores = [result["score"] for result in results]
        monotonic = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
        score_monotonicity = 1.0 if monotonic else 0.0
        
        # Check score distribution (should have good separation)
        score_range = max(scores) - min(scores)
        score_distribution = min(score_range / max(scores), 1.0) if max(scores) > 0 else 0.0
        
        return {
            "score_monotonicity": score_monotonicity,
            "score_distribution": score_distribution
        }
    
    def run_accuracy_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive accuracy evaluation including LLM generation."""
        print("Running Accuracy Evaluation with LLM Integration")
        print("=" * 60)
        
        # Setup system
        self.rag_system.setup_collection()
        embeddings_dir = Path("synthetic_dataset/embeddings")
        self.rag_system.load_embeddings_to_qdrant(embeddings_dir)
        
        results_by_category = {}
        all_relevance_scores = []
        all_ranking_scores = []
        all_generation_scores = []
        query_times = []
        generation_times = []
        
        print(f"Evaluating {len(self.ground_truth_queries)} test queries with LLM generation...")
        
        for i, query_data in enumerate(self.ground_truth_queries, 1):
            query = query_data["query"]
            category = query_data["category"]
            
            # Execute retrieval-only query with timing
            start_time = time.time()
            retrieval_results = self.rag_system.search(query, limit=10)
            retrieval_time = time.time() - start_time
            
            # Execute full RAG query with LLM generation
            generation_start = time.time()
            rag_result = self.rag_system.search_and_generate(query, limit=10)
            generation_time = time.time() - generation_start
            
            query_times.append(retrieval_time)
            generation_times.append(generation_time)
            
            # Evaluate retrieval relevance
            relevance_metrics = self.evaluate_relevance(query_data, retrieval_results)
            
            # Evaluate ranking
            ranking_metrics = self.evaluate_ranking_quality(retrieval_results)
            
            # Evaluate LLM generation quality
            generation_metrics = self.evaluate_generation_quality(query_data, rag_result)
            
            # Store results by category
            if category not in results_by_category:
                results_by_category[category] = []
            
            query_result = {
                "query": query,
                "retrieval_time": retrieval_time,
                "generation_time": generation_time,
                "num_retrieved": len(retrieval_results),
                "relevance": relevance_metrics,
                "ranking": ranking_metrics,
                "generation": generation_metrics,
                "confidence": rag_result['generated_answer']['confidence'],
                "top_score": retrieval_results[0]["score"] if retrieval_results else 0.0
            }
            results_by_category[category].append(query_result)
            
            all_relevance_scores.append(relevance_metrics["overall_relevance"])
            all_ranking_scores.append(ranking_metrics["score_monotonicity"])
            all_generation_scores.append(generation_metrics["overall_quality"])
            
            print(f"  Query {i:2d}: R:{retrieval_time:.3f}s G:{generation_time:.3f}s | Rel:{relevance_metrics['overall_relevance']:.2f} Gen:{generation_metrics['overall_quality']:.2f}")
        
        # Calculate overall metrics
        overall_metrics = {
            "average_relevance": statistics.mean(all_relevance_scores),
            "average_ranking_quality": statistics.mean(all_ranking_scores),
            "average_generation_quality": statistics.mean(all_generation_scores),
            "average_retrieval_time": statistics.mean(query_times),
            "average_generation_time": statistics.mean(generation_times),
            "total_queries": len(self.ground_truth_queries),
            "categories_tested": len(results_by_category)
        }
        
        return {
            "overall_metrics": overall_metrics,
            "results_by_category": results_by_category,
            "detailed_scores": {
                "relevance_scores": all_relevance_scores,
                "ranking_scores": all_ranking_scores,
                "generation_scores": all_generation_scores,
                "retrieval_times": query_times,
                "generation_times": generation_times
            }
        }
    
    def generate_accuracy_report(self, evaluation_results: Dict[str, Any]) -> str:
        """Generate a detailed accuracy report."""
        overall = evaluation_results["overall_metrics"]
        by_category = evaluation_results["results_by_category"]
        
        report = []
        report.append("# Meeting RAG System - Accuracy Evaluation Report with LLM Integration")
        report.append("=" * 80)
        report.append("")
        
        # Overall metrics
        report.append("## Overall Performance Metrics")
        report.append(f"- **Average Relevance Score**: {overall['average_relevance']:.3f} / 1.000")
        report.append(f"- **Average Ranking Quality**: {overall['average_ranking_quality']:.3f} / 1.000")
        report.append(f"- **Average Generation Quality**: {overall['average_generation_quality']:.3f} / 1.000")
        report.append(f"- **Average Retrieval Time**: {overall['average_retrieval_time']:.3f} seconds")
        report.append(f"- **Average Generation Time**: {overall['average_generation_time']:.3f} seconds")
        report.append(f"- **Total Test Queries**: {overall['total_queries']}")
        report.append(f"- **Categories Tested**: {overall['categories_tested']}")
        report.append("")
        
        # Performance grading
        relevance_grade = self._get_grade(overall['average_relevance'])
        ranking_grade = self._get_grade(overall['average_ranking_quality'])
        generation_grade = self._get_grade(overall['average_generation_quality'])
        
        report.append("## Performance Grades")
        report.append(f"- **Retrieval Relevance**: {relevance_grade} ({overall['average_relevance']:.1%})")
        report.append(f"- **Result Ranking**: {ranking_grade} ({overall['average_ranking_quality']:.1%})")
        report.append(f"- **LLM Generation**: {generation_grade} ({overall['average_generation_quality']:.1%})")
        report.append("")
        
        # Category breakdown
        report.append("## Performance by Category")
        for category, results in by_category.items():
            avg_relevance = statistics.mean([r["relevance"]["overall_relevance"] for r in results])
            avg_generation = statistics.mean([r["generation"]["overall_quality"] for r in results])
            avg_retrieval_time = statistics.mean([r["retrieval_time"] for r in results])
            avg_generation_time = statistics.mean([r["generation_time"] for r in results])
            
            report.append(f"### {category.replace('_', ' ').title()}")
            report.append(f"- Queries: {len(results)}")
            report.append(f"- Retrieval Relevance: {avg_relevance:.3f}")
            report.append(f"- Generation Quality: {avg_generation:.3f}")
            report.append(f"- Retrieval Time: {avg_retrieval_time:.3f}s")
            report.append(f"- Generation Time: {avg_generation_time:.3f}s")
            report.append("")
        
        return "\n".join(report)
    
    def evaluate_generation_quality(self, query_data: Dict[str, Any], rag_result: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate the quality of LLM-generated answers."""
        generated_answer = rag_result['generated_answer']['answer']
        confidence = rag_result['generated_answer']['confidence']
        sources_used = rag_result['generated_answer']['sources_used']
        
        # Length appropriateness (not too short, not too long)
        answer_length = len(generated_answer)
        length_score = 1.0 if 50 <= answer_length <= 1000 else max(0.3, min(answer_length / 500, 1.0))
        
        # Keyword coverage in generated answer
        keyword_coverage = 0.0
        if "expected_keywords" in query_data:
            answer_lower = generated_answer.lower()
            keyword_matches = sum(1 for keyword in query_data["expected_keywords"] 
                                if keyword.lower() in answer_lower)
            keyword_coverage = keyword_matches / len(query_data["expected_keywords"])
        
        # Sources utilization (did it use multiple sources effectively?)
        source_utilization = min(sources_used / 3.0, 1.0)  # Optimal is 3+ sources
        
        # Overall generation quality (weighted average)
        overall_quality = (
            confidence * 0.4 +          # Model's own confidence
            length_score * 0.2 +        # Appropriate length
            keyword_coverage * 0.3 +    # Covers expected topics
            source_utilization * 0.1    # Uses multiple sources
        )
        
        return {
            "confidence": confidence,
            "length_score": length_score,
            "keyword_coverage": keyword_coverage,
            "source_utilization": source_utilization,
            "overall_quality": overall_quality,
            "answer_length": answer_length
        }
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B+"
        elif score >= 0.6:
            return "B"
        elif score >= 0.5:
            return "C"
        else:
            return "D"

def main():
    """Run accuracy evaluation and generate report."""
    evaluator = AccuracyEvaluator()
    
    print("Meeting RAG System - Accuracy Evaluation with LLM Integration")
    print("=" * 80)
    
    # Run evaluation
    start_time = time.time()
    results = evaluator.run_accuracy_evaluation()
    total_time = time.time() - start_time
    
    # Generate and display report
    report = evaluator.generate_accuracy_report(results)
    print("\n" + report)
    
    # Save detailed results
    with open("accuracy_evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nAccuracy Evaluation Complete")
    print(f"Total evaluation time: {total_time:.2f} seconds")
    print("Detailed results saved to: accuracy_evaluation_results.json")
    
    return results

if __name__ == "__main__":
    results = main()