"""
Phase 3: Vector Database Setup and Retrieval Pipeline with LLM Generation
This script sets up Qdrant vector database and implements retrieval functionality with Mistral AI.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from tqdm import tqdm
from mistralai import Mistral
from dotenv import load_dotenv
from langsmith import traceable, Client as LangSmithClient #type: ignore
import time

# Load environment variables
load_dotenv()

class MeetingRAGSystem:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 mistral_api_key: str = None):
        """Initialize the RAG system with embedding model, Qdrant client, Mistral AI, and LangSmith."""
        self.model = SentenceTransformer(model_name)
        self.client = QdrantClient(":memory:")  # In-memory for demo, use persistent storage in production
        self.collection_name = "meeting_chunks"
        self.vector_size = 384  # all-MiniLM-L6-v2 embedding dimension
        
        # Initialize Mistral AI client - use env variable or fallback to parameter
        api_key = mistral_api_key or os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("Mistral API key must be provided via MISTRAL_API_KEY environment variable or parameter")
        
        self.mistral_client = Mistral(api_key=api_key)
        self.mistral_model = "mistral-large-latest"
        
        # Initialize LangSmith client
        self.langsmith_client = None
        if os.getenv("LANGCHAIN_API_KEY"):
            try:
                self.langsmith_client = LangSmithClient()
                print("LangSmith tracing enabled")
            except Exception as e:
                print(f"LangSmith initialization failed: {e}")
        else:
            print("LangSmith API key not found - tracing disabled")
        
    def setup_collection(self):
        """Create and configure the Qdrant collection."""
        try:
            self.client.delete_collection(self.collection_name)
        except:
            pass  # Collection doesn't exist
            
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )
        print(f"Created collection: {self.collection_name}")
        
    def load_embeddings_to_qdrant(self, embeddings_dir: Path):
        """Load all embeddings from JSON files into Qdrant."""
        points = []
        point_id = 0
        
        for embedding_file in tqdm(list(embeddings_dir.glob("*.json")), desc="Loading embeddings"):
            with open(embedding_file, "r", encoding="utf-8") as f:
                embeddings_data = json.load(f)
                
            for item in embeddings_data:
                metadata = item["metadata"]
                
                # Create point with embedding and metadata
                point = PointStruct(
                    id=point_id,
                    vector=item["embedding"],
                    payload={
                        "chunk_id": item["chunk_id"],
                        "meeting_id": metadata["meeting_id"],
                        "text": metadata.get("text", metadata.get("task", "")),
                        "type": metadata["type"],
                        "speaker": metadata.get("speaker"),
                        "role": metadata.get("role"),
                        "assigned_to": metadata.get("assigned_to"),
                        "due_date": metadata.get("due_date"),
                        "priority": metadata.get("priority"),
                        "file_source": embedding_file.name
                    }
                )
                points.append(point)
                point_id += 1
                
        # Upload points in batches
        batch_size = 100
        for i in tqdm(range(0, len(points), batch_size), desc="Uploading to Qdrant"):
            batch = points[i:i + batch_size]
            self.client.upsert(collection_name=self.collection_name, points=batch)
            
        print(f"Loaded {len(points)} embeddings into Qdrant")
        
    @traceable(name="semantic_search")
    def search(self, query: str, limit: int = 10, chunk_type: str = None, meeting_id: str = None) -> List[Dict[str, Any]]:
        """Search for relevant chunks using semantic similarity with LangSmith tracing."""
        start_time = time.time()
        
        # Generate query embedding
        query_vector = self.model.encode(query).tolist()
        
        # Build filter conditions
        filter_conditions = []
        if chunk_type:
            filter_conditions.append(FieldCondition(key="type", match=MatchValue(value=chunk_type)))
        if meeting_id:
            filter_conditions.append(FieldCondition(key="meeting_id", match=MatchValue(value=meeting_id)))
            
        search_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        # Perform search
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "score": result.score,
                "chunk_id": result.payload["chunk_id"],
                "meeting_id": result.payload["meeting_id"],
                "text": result.payload["text"],
                "type": result.payload["type"],
                "speaker": result.payload.get("speaker"),
                "role": result.payload.get("role"),
                "metadata": {k: v for k, v in result.payload.items() if k not in ["text", "chunk_id", "meeting_id", "type", "speaker", "role"]}
            })
        
        # Log search metrics to LangSmith
        search_time = time.time() - start_time
        if self.langsmith_client:
            try:
                self.langsmith_client.create_run(
                    name="semantic_search_metrics",
                    run_type="retriever",
                    inputs={"query": query, "limit": limit, "chunk_type": chunk_type, "meeting_id": meeting_id},
                    outputs={"results_count": len(results), "search_time": search_time, "top_score": results[0]["score"] if results else 0}
                )
            except Exception as e:
                pass  # Don't fail on logging errors
            
        return results
    
    @traceable(name="generate_answer")
    def generate_answer(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an answer using Mistral AI based on retrieved chunks with LangSmith tracing."""
        start_time = time.time()
        
        if not retrieved_chunks:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "confidence": 0.0,
                "sources_used": 0
            }
        
        # Prepare context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks[:5], 1):  # Use top 5 chunks
            context_parts.append(f"Source {i}:")
            context_parts.append(f"Meeting: {chunk['meeting_id']}")
            if chunk['speaker']:
                context_parts.append(f"Speaker: {chunk['speaker']} ({chunk['role']})")
            context_parts.append(f"Content: {chunk['text']}")
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Create prompt for Mistral AI
        prompt = f"""You are an AI assistant helping analyze meeting data for an AI-insurance entrepreneur named Arjun Vasanth. Based on the retrieved meeting information below, provide a comprehensive and accurate answer to the user's question.

Question: {query}

Retrieved Meeting Information:
{context}

Instructions:
- Provide a clear, comprehensive answer based only on the information provided
- If multiple perspectives are mentioned, include them in your response
- Cite specific meetings, speakers, or details when relevant
- If the information is insufficient to fully answer the question, state what you can determine and what limitations exist
- Be conversational but professional
- Focus on insights that would be valuable for business decision-making

Answer:"""

        try:
            # Generate response using Mistral AI
            response = self.mistral_client.chat.complete(
                model=self.mistral_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            generated_answer = response.choices[0].message.content
            
            # Calculate confidence based on retrieval scores
            avg_score = sum(chunk['score'] for chunk in retrieved_chunks[:5]) / min(len(retrieved_chunks), 5)
            confidence = min(avg_score * 1.2, 1.0)  # Scale and cap at 1.0
            
            generation_time = time.time() - start_time
            
            # Log generation metrics to LangSmith
            if self.langsmith_client:
                try:
                    self.langsmith_client.create_run(
                        name="llm_generation_metrics",
                        run_type="llm",
                        inputs={"query": query, "context_length": len(context), "sources_count": len(retrieved_chunks[:5])},
                        outputs={"answer_length": len(generated_answer), "confidence": confidence, "generation_time": generation_time}
                    )
                except Exception as e:
                    pass  # Don't fail on logging errors
            
            return {
                "answer": generated_answer,
                "confidence": confidence,
                "sources_used": len(retrieved_chunks[:5]),
                "retrieval_scores": [chunk['score'] for chunk in retrieved_chunks[:5]]
            }
            
        except Exception as e:
            return {
                "answer": f"Sorry, I encountered an error generating the response: {str(e)}",
                "confidence": 0.0,
                "sources_used": len(retrieved_chunks),
                "error": str(e)
            }
    
    @traceable(name="rag_pipeline")
    def search_and_generate(self, query: str, limit: int = 10, chunk_type: str = None, 
                           meeting_id: str = None) -> Dict[str, Any]:
        """Perform retrieval and generate answer in one step with full LangSmith tracing."""
        start_time = time.time()
        
        # Retrieve relevant chunks
        retrieved_chunks = self.search(query, limit, chunk_type, meeting_id)
        
        # Generate answer using LLM
        llm_response = self.generate_answer(query, retrieved_chunks)
        
        total_time = time.time() - start_time
        
        # Log complete RAG pipeline metrics to LangSmith
        if self.langsmith_client:
            try:
                self.langsmith_client.create_run(
                    name="rag_pipeline_complete",
                    run_type="chain",
                    inputs={"query": query, "limit": limit, "chunk_type": chunk_type, "meeting_id": meeting_id},
                    outputs={
                        "total_time": total_time,
                        "chunks_retrieved": len(retrieved_chunks),
                        "confidence": llm_response.get("confidence", 0.0),
                        "answer_length": len(llm_response.get("answer", "")),
                        "sources_used": llm_response.get("sources_used", 0)
                    }
                )
            except Exception as e:
                pass  # Don't fail on logging errors
        
        return {
            "query": query,
            "generated_answer": llm_response,
            "retrieved_chunks": retrieved_chunks,
            "total_chunks_found": len(retrieved_chunks)
        }

    def get_collection_stats(self):
        """Get statistics about the collection."""
        info = self.client.get_collection(self.collection_name)
        return {
            "total_points": info.points_count,
            "vector_size": info.config.params.vectors.size,
            "distance_metric": info.config.params.vectors.distance
        }

def main():
    print("Starting Phase 3: Vector Database Setup and Retrieval Pipeline with LLM")
    
    # Initialize RAG system
    rag_system = MeetingRAGSystem()
    
    # Setup collection
    rag_system.setup_collection()
    
    # Load embeddings
    embeddings_dir = Path("synthetic_dataset/embeddings")
    rag_system.load_embeddings_to_qdrant(embeddings_dir)
    
    # Print collection stats
    stats = rag_system.get_collection_stats()
    print(f"Collection Stats: {stats}")
    
    # Test queries with LLM generation
    print("\nTesting RAG with LLM Generation:")
    
    test_queries = [
        "What are Arjun's main concerns about the business?",
        "How do investors view the company's growth potential?", 
        "What technical challenges has the team discussed?",
        "What are the key action items that need immediate attention?"
    ]
    
    for query in test_queries:
        print(f"\n" + "="*80)
        print(f"Query: '{query}'")
        print("="*80)
        
        result = rag_system.search_and_generate(query, limit=5)
        
        print(f"Generated Answer (Confidence: {result['generated_answer']['confidence']:.2f}):")
        print(result['generated_answer']['answer'])
        
        print(f"\nBased on {result['generated_answer']['sources_used']} sources from {result['total_chunks_found']} retrieved chunks")
    
    print("\nPhase 3 complete! RAG system with LLM generation is ready.")
    return rag_system

if __name__ == "__main__":
    rag_system = main()