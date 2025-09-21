"""
This script provides a command-line interface for querying the meeting database with AI-generated answers.
"""

import time
import os
from phase3_rag_system import MeetingRAGSystem
from pathlib import Path
from langsmith import Client as LangSmithClient #type: ignore
import uuid

def format_llm_response(result, query_time):
    """Format LLM-generated response for display."""
    print(f"\nAI-Generated Answer (in {query_time:.3f} seconds):")
    print("=" * 80)
    
    answer_data = result['generated_answer']
    
    # Display the generated answer
    print(f"Answer:")
    print(answer_data['answer'])
    print()
    
    # Display metadata
    print(f"📊 Confidence: {answer_data['confidence']:.2f}")
    print(f"📚 Sources Used: {answer_data['sources_used']} chunks")
    if 'retrieval_scores' in answer_data:
        avg_score = sum(answer_data['retrieval_scores']) / len(answer_data['retrieval_scores'])
        print(f"🎯 Average Retrieval Score: {avg_score:.3f}")
    print()

def format_search_results(results, query_time, show_detailed=False):
    """Format search results for display."""
    if not show_detailed:
        return
        
    print(f"\nRaw Retrieved Chunks ({len(results)} results):")
    print("=" * 80)
    
    for i, result in enumerate(results[:3], 1):  # Show top 3 only
        print(f"\n{i}. [{result['type'].upper()}] Score: {result['score']:.3f}")
        print(f"   Meeting: {result['meeting_id']}")
        
        if result['speaker']:
            print(f"   Speaker: {result['speaker']} ({result['role']})")
            
        # Display appropriate content based on type
        if result['type'] == 'action_item':
            print(f"   Task: {result['text']}")
            if result['metadata'].get('assigned_to'):
                print(f"   Assigned to: {result['metadata']['assigned_to']}")
            if result['metadata'].get('due_date'):
                print(f"   Due: {result['metadata']['due_date']}")
            if result['metadata'].get('priority'):
                print(f"   Priority: {result['metadata']['priority']}")
        else:
            # For minutes and insights
            text = result['text']
            if len(text) > 150:
                text = text[:150] + "..."
            print(f"   Content: {text}")
        
        print("-" * 40)

def main():
    print("Meeting RAG System - Interactive Query Interface with AI Generation and LangSmith Tracing")
    print("Loading system...")
    
    # Initialize LangSmith session tracking
    session_id = str(uuid.uuid4())
    langsmith_client = None
    if os.getenv("LANGCHAIN_API_KEY"):
        try:
            langsmith_client = LangSmithClient()
            print(f"LangSmith session tracking enabled (Session: {session_id[:8]})")
        except Exception as e:
            print(f"LangSmith session tracking failed: {e}")
    else:
        print("LangSmith API key not found - session tracking disabled")
    
    # Initialize RAG system
    rag_system = MeetingRAGSystem()
    rag_system.setup_collection()
    
    # Load embeddings
    embeddings_dir = Path("synthetic_dataset/embeddings")
    rag_system.load_embeddings_to_qdrant(embeddings_dir)
    
    # Get collection stats
    stats = rag_system.get_collection_stats()
    print(f"Loaded {stats['total_points']} chunks from meetings")
    
    print("\n" + "="*60)
    print("RAG QUERY INTERFACE WITH AI GENERATION")
    print("="*60)
    print("Available modes:")
    print("  Default: AI-generated answers (recommended)")
    print("  Raw mode: Add 'raw:' prefix for retrieval-only results")
    print()
    print("Available filters:")
    print("  - Type: 'minute', 'action_item', 'key_insight'")
    print("  - Use 'filter:type=action_item' to filter by type")
    print("  - Use 'filter:meeting=MTG_2024_01_01_001' to filter by meeting")
    print("  - Add 'detailed:' prefix to show raw chunks alongside AI answer")
    print("  - Type 'quit' to exit")
    print("="*60)
    
    while True:
        try:
            # Get user query
            query = input("\nEnter your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not query:
                continue
            
            # Parse special modes
            raw_mode = query.startswith('raw:')
            detailed_mode = query.startswith('detailed:')
            
            if raw_mode:
                query = query[4:].strip()  # Remove 'raw:' prefix
            elif detailed_mode:
                query = query[9:].strip()  # Remove 'detailed:' prefix
            
            # Parse filters
            chunk_type = None
            meeting_id = None
            
            if 'filter:' in query:
                parts = query.split()
                query_parts = []
                
                for part in parts:
                    if part.startswith('filter:'):
                        filter_part = part[7:]  # Remove 'filter:'
                        if '=' in filter_part:
                            key, value = filter_part.split('=', 1)
                            if key == 'type':
                                chunk_type = value
                            elif key == 'meeting':
                                meeting_id = value
                    else:
                        query_parts.append(part)
                
                query = ' '.join(query_parts)
            
            # Perform search with timing
            start_time = time.time()
            
            if raw_mode:
                # Raw retrieval mode
                results = rag_system.search(
                    query=query, 
                    limit=5, 
                    chunk_type=chunk_type, 
                    meeting_id=meeting_id
                )
                query_time = time.time() - start_time
                format_search_results(results, query_time, show_detailed=True)
            else:
                # AI generation mode
                result = rag_system.search_and_generate(
                    query=query, 
                    limit=10, 
                    chunk_type=chunk_type, 
                    meeting_id=meeting_id
                )
                query_time = time.time() - start_time
                
                # Display AI-generated answer
                format_llm_response(result, query_time)
                
                # Optionally show detailed retrieval results
                if detailed_mode:
                    format_search_results(result['retrieved_chunks'], query_time, show_detailed=True)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            print(f"Details: {traceback.format_exc()}")

if __name__ == "__main__":
    main()