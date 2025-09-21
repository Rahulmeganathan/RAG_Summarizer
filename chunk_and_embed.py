"""
Phase 2: Chunking and Embedding Pipeline
This script chunks the enriched dataset and generates embeddings using sentence-transformers/all-MiniLM-L6-v2.
"""

import os
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Initialize embedding model
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

# Input and output directories
ENRICHED_DIR = Path("synthetic_dataset/enriched_meetings")
CHUNKED_DIR = Path("synthetic_dataset/chunked_meetings")
CHUNKED_DIR.mkdir(exist_ok=True)

# Chunking function
def chunk_meeting(meeting_data):
    """Chunk a single enriched meeting into smaller pieces."""
    chunks = []
    meeting_id = meeting_data.get("meeting_id")

    # Chunk minutes (speaker-level)
    for minute in meeting_data.get("minutes", []):
        chunk = {
            "chunk_id": f"{meeting_id}_{minute.get('timestamp')}",
            "meeting_id": meeting_id,
            "speaker": minute.get("speaker"),
            "role": next((p.get("role") for p in meeting_data.get("participants", []) if p.get("name") == minute.get("speaker")), "unknown"),
            "text": minute.get("text"),
            "type": "minute"
        }
        chunks.append(chunk)

    # Chunk action items
    for idx, action in enumerate(meeting_data.get("action_items", [])):
        chunk = {
            "chunk_id": f"{meeting_id}_action_{idx+1}",
            "meeting_id": meeting_id,
            "task": action.get("task"),
            "assigned_to": action.get("assigned_to"),
            "due_date": action.get("due_date"),
            "priority": action.get("priority"),
            "type": "action_item"
        }
        chunks.append(chunk)

    # Chunk key insights
    for idx, insight in enumerate(meeting_data.get("enrichment_metadata", {}).get("analysis_results", {}).get("key_insights", [])):
        chunk = {
            "chunk_id": f"{meeting_id}_insight_{idx+1}",
            "meeting_id": meeting_id,
            "text": insight,
            "type": "key_insight"
        }
        chunks.append(chunk)

    return chunks

# Process all enriched meetings
def process_enriched_meetings():
    """Process all enriched meetings and save chunked data."""
    for enriched_file in tqdm(list(ENRICHED_DIR.glob("*.json")), desc="Chunking meetings"):
        with open(enriched_file, "r", encoding="utf-8") as f:
            meeting_data = json.load(f)

        # Chunk the meeting
        chunks = chunk_meeting(meeting_data)

        # Save chunks to output directory
        output_file = CHUNKED_DIR / f"chunked_{enriched_file.name}"
        with open(output_file, "w", encoding="utf-8") as out_f:
            json.dump(chunks, out_f, indent=2, ensure_ascii=False)

# Generate embeddings for chunks
def generate_embeddings():
    """Generate embeddings for all chunks and save them."""
    EMBEDDINGS_DIR = Path("synthetic_dataset/embeddings")
    EMBEDDINGS_DIR.mkdir(exist_ok=True)

    for chunked_file in tqdm(list(CHUNKED_DIR.glob("*.json")), desc="Generating embeddings"):
        with open(chunked_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        embeddings = []
        for chunk in chunks:
            text = chunk.get("text") or chunk.get("task")
            if text:
                embedding = model.encode(text)
                embeddings.append({
                    "chunk_id": chunk["chunk_id"],
                    "embedding": embedding.tolist(),
                    "metadata": chunk
                })

        # Save embeddings to output directory
        output_file = EMBEDDINGS_DIR / f"embeddings_{chunked_file.name}"
        with open(output_file, "w", encoding="utf-8") as out_f:
            json.dump(embeddings, out_f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("Starting Phase 2: Chunking and Embedding Pipeline")
    process_enriched_meetings()
    generate_embeddings()
    print("Phase 2 complete! Chunks and embeddings are ready.")