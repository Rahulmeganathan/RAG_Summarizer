"""
Comprehensive Test Suite for Meeting RAG System with LLM Integration and LangSmith Evaluation
This script validates system performance, accuracy, and latency requirements.
"""

import time
import statistics
import os
from phase3_rag_system import MeetingRAGSystem
from pathlib import Path
from langsmith import Client as LangSmithClient, evaluate #type: ignore
import uuid

def test_langsmith_evaluation(rag_system):
    """Run LangSmith-based evaluation of the RAG system."""
    print("\nLangSmith Evaluation")
    print("=" * 50)
    
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("LangSmith API key not found - skipping evaluation")
        return
    
    try:
        langsmith_client = LangSmithClient()
        
        # Test dataset for evaluation
        test_cases = [
            {
                "query": "What are Arjun's main concerns about the business?",
                "expected_topics": ["funding", "market", "competition", "technical challenges"]
            },
            {
                "query": "How do investors view the company's prospects?",
                "expected_topics": ["investor sentiment", "funding", "valuation", "market potential"]
            },
            {
                "query": "What technical challenges need to be addressed?",
                "expected_topics": ["AI development", "technical debt", "scalability", "integration"]
            }
        ]
        
        # Custom evaluator function
        def evaluate_answer_quality(run, example):
            """Custom evaluator for answer quality."""
            try:
                answer = run.outputs.get("generated_answer", {}).get("answer", "")
                confidence = run.outputs.get("generated_answer", {}).get("confidence", 0.0)
                sources_used = run.outputs.get("generated_answer", {}).get("sources_used", 0)
                
                # Check if answer contains expected topics
                expected_topics = example.outputs.get("expected_topics", [])
                topic_coverage = sum(1 for topic in expected_topics if topic.lower() in answer.lower()) / len(expected_topics)
                
                # Quality score based on multiple factors
                quality_score = (
                    min(confidence * 2, 1.0) * 0.4 +  # Confidence (capped at 1.0)
                    topic_coverage * 0.4 +  # Topic coverage
                    min(sources_used / 3, 1.0) * 0.2  # Source utilization
                )
                
                return {
                    "key": "answer_quality",
                    "score": quality_score,
                    "comment": f"Confidence: {confidence:.2f}, Topic coverage: {topic_coverage:.2f}, Sources: {sources_used}"
                }
            except Exception as e:
                return {"key": "answer_quality", "score": 0.0, "comment": f"Error: {str(e)}"}
        
        # Run evaluation
        dataset_name = f"meeting_rag_test_{int(time.time())}"
        
        # Create dataset
        dataset = langsmith_client.create_dataset(
            dataset_name=dataset_name,
            description="Test dataset for Meeting RAG System evaluation"
        )
        
        # Add examples to dataset
        for i, case in enumerate(test_cases):
            langsmith_client.create_example(
                dataset_id=dataset.id,
                inputs={"query": case["query"]},
                outputs={"expected_topics": case["expected_topics"]}
            )
        
        # Run evaluation
        def rag_chain(inputs):
            """Wrapper function for evaluation."""
            result = rag_system.search_and_generate(inputs["query"])
            return result
        
        evaluation_results = evaluate(
            rag_chain,
            data=dataset_name,
            evaluators=[evaluate_answer_quality],
            experiment_prefix="meeting_rag_eval"
        )
        
        print(f"LangSmith evaluation completed")
        print(f"   Dataset: {dataset_name}")
        print(f"   Test cases: {len(test_cases)}")
        print(f"   Results logged to LangSmith dashboard")
        
        return evaluation_results
        
    except Exception as e:
        print(f"LangSmith evaluation failed: {e}")
        return None

def test_system_performance():
    """Test system performance and latency."""
    print("Testing RAG System Performance with LLM Integration")
    print("=" * 50)
    
    # Initialize system
    rag_system = MeetingRAGSystem()
    rag_system.setup_collection()
    
    # Load embeddings
    embeddings_dir = Path("synthetic_dataset/embeddings")
    load_start = time.time()
    rag_system.load_embeddings_to_qdrant(embeddings_dir)
    load_time = time.time() - load_start
    
    stats = rag_system.get_collection_stats()
    print(f"System loaded {stats['total_points']} chunks in {load_time:.2f} seconds")
    
    # Test queries for latency (RAG only)
    test_queries = [
        "What are the key priorities for product development?",
        "Show me high priority action items",
        "What did Arjun discuss about funding?",
        "Which meetings discussed regulatory compliance?",
        "What are the main concerns about market expansion?"
    ]
    
    print(f"\nTesting retrieval latency with {len(test_queries)} queries...")
    
    query_times = []
    results_count = []
    
    for i, query in enumerate(test_queries, 1):
        start_time = time.time()
        results = rag_system.search(query, limit=10)
        query_time = time.time() - start_time
        
        query_times.append(query_time)
        results_count.append(len(results))
        
        print(f"  Query {i:2d}: {query_time:.3f}s - {len(results)} results - '{query[:50]}...'")
    
    # Calculate performance metrics
    avg_latency = statistics.mean(query_times)
    max_latency = max(query_times)
    min_latency = min(query_times)
    avg_results = statistics.mean(results_count)
    
    print(f"\nRetrieval Performance Summary:")
    print(f"  Average latency: {avg_latency:.3f} seconds")
    print(f"  Maximum latency: {max_latency:.3f} seconds")
    print(f"  Minimum latency: {min_latency:.3f} seconds")
    print(f"  Average results: {avg_results:.1f} chunks")
    
    # Check latency requirement
    latency_requirement = 10.0  # seconds
    if max_latency < latency_requirement:
        print(f"PASS: All retrieval queries under {latency_requirement}s requirement")
    else:
        print(f"FAIL: Some retrieval queries exceed {latency_requirement}s requirement")
    
    return rag_system

def test_llm_generation(rag_system):
    """Test LLM answer generation quality and performance."""
    print(f"\nTesting LLM Answer Generation")
    print("=" * 50)
    
    # Test queries for LLM generation
    llm_test_queries = [
        "What are Arjun's main concerns about the business?",
        "How do investors view the company's prospects?", 
        "What technical challenges need to be addressed?"
    ]
    
    generation_times = []
    confidence_scores = []
    
    for i, query in enumerate(llm_test_queries, 1):
        print(f"\nLLM Test {i}: '{query}'")
        
        start_time = time.time()
        result = rag_system.search_and_generate(query, limit=5)
        generation_time = time.time() - start_time
        
        generation_times.append(generation_time)
        confidence_scores.append(result['generated_answer']['confidence'])
        
        print(f"  Generation time: {generation_time:.3f}s")
        print(f"  Confidence: {result['generated_answer']['confidence']:.2f}")
        print(f"  Sources used: {result['generated_answer']['sources_used']}")
        print(f"  Answer length: {len(result['generated_answer']['answer'])} chars")
        
        # Show first 100 chars of answer
        answer_preview = result['generated_answer']['answer'][:100] + "..." if len(result['generated_answer']['answer']) > 100 else result['generated_answer']['answer']
        print(f"  Preview: {answer_preview}")
    
    # Calculate LLM performance metrics
    avg_generation_time = statistics.mean(generation_times)
    avg_confidence = statistics.mean(confidence_scores)
    
    print(f"\nLLM Generation Summary:")
    print(f"  Average generation time: {avg_generation_time:.3f} seconds")
    print(f"  Average confidence: {avg_confidence:.2f}")
    print(f"  Total queries tested: {len(llm_test_queries)}")
    
    # Check LLM performance requirements
    if avg_generation_time < 30.0:  # 30 second limit for full RAG
        print(f"PASS: LLM generation under 30s requirement")
    else:
        print(f"FAIL: LLM generation exceeds 30s requirement")
    
    if avg_confidence > 0.5:
        print(f"PASS: Average confidence above 0.5 threshold")
    else:
        print(f"WARNING: Average confidence below 0.5 threshold")
def test_search_functionality(rag_system):
    """Test different search scenarios."""
    print(f"\nTesting Search Functionality")
    print("=" * 50)
    
    # Test 1: Basic semantic search
    print("Test 1: Basic semantic search")
    results = rag_system.search("product development strategy", limit=3)
    print(f"  Found {len(results)} results for 'product development strategy'")
    
    # Test 2: Filter by type
    print("\nTest 2: Filter by chunk type")
    action_results = rag_system.search("high priority", limit=5, chunk_type="action_item")
    print(f"  Found {len(action_results)} action items for 'high priority'")
    
    # Test 3: Filter by meeting
    print("\nTest 3: Filter by specific meeting")
    meeting_results = rag_system.search("discussion", limit=5, meeting_id="MTG_2024_01_01_001")
    print(f"  Found {len(meeting_results)} results in specific meeting")
    
    # Test 4: Complex query
    print("\nTest 4: Complex business query")
    complex_results = rag_system.search("market expansion risks and opportunities", limit=5)
    print(f"  Found {len(complex_results)} results for complex query")
    
    # Display sample results
    if complex_results:
        print("\n  Sample result:")
        result = complex_results[0]
        print(f"    Score: {result['score']:.3f}")
        print(f"    Type: {result['type']}")
        print(f"    Meeting: {result['meeting_id']}")
        print(f"    Content: {result['text'][:100]}...")

def test_data_coverage(rag_system):
    """Test data coverage and completeness."""
    print(f"\nTesting Data Coverage")
    print("=" * 50)
    
    # Test different chunk types
    chunk_types = ["minute", "action_item", "key_insight"]
    
    for chunk_type in chunk_types:
        results = rag_system.search("", limit=1000, chunk_type=chunk_type)
        print(f"  {chunk_type.replace('_', ' ').title()}: {len(results)} chunks")
    
    # Test meeting coverage
    all_results = rag_system.search("", limit=1000)
    meeting_ids = set(result['meeting_id'] for result in all_results)
    print(f"  Total meetings covered: {len(meeting_ids)}")
    
    # Test speaker coverage
    speakers = set(result['speaker'] for result in all_results if result['speaker'])
    print(f"  Unique speakers: {len(speakers)}")

def main():
    """Run comprehensive test suite with LangSmith evaluation."""
    print("Meeting RAG System - Comprehensive Test Suite with LLM Integration and LangSmith Evaluation")
    print("=" * 90)
    
    start_time = time.time()
    
    # Test 1: Performance and latency
    rag_system = test_system_performance()
    
    # Test 2: LLM generation
    test_llm_generation(rag_system)
    
    # Test 3: Search functionality
    test_search_functionality(rag_system)
    
    # Test 4: Data coverage
    test_data_coverage(rag_system)
    
    # Test 5: LangSmith evaluation
    test_langsmith_evaluation(rag_system)
    
    total_time = time.time() - start_time
    
    print(f"\nTest Suite Complete")
    print("=" * 70)
    print(f"Total test time: {total_time:.2f} seconds")
    
    return rag_system

if __name__ == "__main__":
    rag_system = main()